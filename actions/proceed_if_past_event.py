from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
import base64
import quopri
import tnefparse
import re
from email.iterators import _structure

from .types import ActionResult

debug_enabled = False
def debug_out(msg: str):
    if debug_enabled:
        print(msg)

def proceed_if_past_event_icalendar(part):
    debug_out('proceed_if_past_event_icalendar')
    tz_replacements = {
        "Eastern Standard Time": "US/Eastern",
        "Eastern Daylight Time": "US/Eastern",
        "US Eastern Standard Time": "US/Eastern",
        "Central Standard Time": "US/Central",
        "Central Daylight Time": "US/Central",
        "Central Standard Time (Mexico)": "America/Mexico_City",
        "Mountain Standard Time": "US/Mountain",
        "Mountain Daylight Time": "US/Mountain",
        "Pacific Standard Time": "US/Pacific",
        "Pacific Daylight Time": "US/Pacific",
        # as per https://stackoverflow.com/a/41495917
        "India Standard Time": "Asia/Kolkata",
        "Greenwich Standard Time": "GMT",
        "GMT Standard Time": "GMT",
        "W. Europe Standard Time": "WET",
        "E. Africa Standard Time": "Africa/Nairobi",
        "E. Australia Standard Time": "Australia/Sydney",
        "AUS Eastern Standard Time": "Australia/Sydney",
        "Romance Standard Time": "Europe/Paris",
        "Hawaiian Standard Time": "Pacific/Honolulu",
        "Sri Lanka Standard Time": "Asia/Colombo",
        "Central European Standard Time": "CET",
        "Paraguay Standard Time": "America/Asuncion",
        "South Africa Standard Time": "Africa/Johannesburg",
        "Israel Standard Time": "Asia/Jerusalem",
    }
    payload = part.get_payload()
    if 'content-transfer-encoding' in part:
        encoding = part['content-transfer-encoding']
        if encoding == '7bit':
            # This is standard ascii; nothing to do
            pass
        elif encoding == 'base64':
            payload = base64.b64decode(payload).decode(part.get_content_charset() or 'utf-8')
        elif encoding == 'quoted-printable':
            payload = quopri.decodestring(payload).decode('utf-8')
        else:
            print('unknown content encoding ' + encoding)
            return "SKIP"

    # NOTE: this is done in all cases; if payload is empty, this will be a no op
    # and will fall thru to skip below

    def parse_date_time(line: str, property: str) -> Optional[datetime]:
        debug_out('parsing ' + property)
        # As per spec https://icalendar.org/iCalendar-RFC-5545/3-3-5-date-time.html
        # DTSTART:19970714T173000Z
        if line.startswith(property + ':'):
            end_date_str = line[(len(property) + 1):]
            # TODO: we need to handle the local time case (without the z) and also make sure we set the timezone right for
            # this case
            try:
                print('parsing UTC date ' + end_date_str)
                return datetime.strptime(end_date_str, '%Y%m%dT%H%M%SZ')
            except ValueError:
                import traceback
                traceback.print_exc()
        # DTSTART;TZID=America/New_York:19970714T133000
        elif line.startswith(property + ';TZID='):
            substr = line[(len(property) + 1):]
            tzpart, datetime_part = substr.split(':')
            tzname = tzpart[5:]
            tzname = tzname.strip(" \"")

            # for debugging purposes
            tzorig = tzname
            if tzname in tz_replacements:
                tzname = tz_replacements[tzname]
            try:
                if tzname != tzorig:
                    debug_out('using timezone ' + tzname + ' (originally ' + tzorig + ')')
                else:
                    debug_out('using timezone ' + tzname)
                tzinfo = ZoneInfo(tzname)
            except:
                print('unrecognized timezone ' + tzname)
                return None
            end_date = datetime.strptime(datetime_part, '%Y%m%dT%H%M%S')
            return end_date.replace(tzinfo=tzinfo)
        # DTEND;VALUE=DATE:20230124 is an all day value
        elif line.startswith(property + ';VALUE=DATE:'):
            # FIXME: we're not using timezones here, which could cause this to act early or late +/- 12 hours (depending)
            # on your local time zone.  ok for now; probably should be fixed at some point.
            _, date_str = line.split(':')
            return datetime.strptime(date_str, '%Y%m%d')

        else:
            debug_out('unrecognized' + property + ' line ' + line)
            return None

    def parse_duration(duration_str: str) -> Optional[timedelta]:
        # As per spec https://icalendar.org/iCalendar-RFC-5545/3-3-6-duration.html
        # Format: [+/-]P[nW][nD][T[nH][nM][nS]]
        # Examples: P15DT5H0M20S, P7W, PT1H30M, -P1DT12H

        duration_str = duration_str.strip()

        # Handle sign
        sign = 1
        if duration_str.startswith('-'):
            sign = -1
            duration_str = duration_str[1:]
        elif duration_str.startswith('+'):
            duration_str = duration_str[1:]

        if not duration_str.startswith('P'):
            return None

        duration_str = duration_str[1:]  # Remove P

        # Parse weeks (if present, it's the only component)
        weeks_match = re.match(r'^(\d+)W$', duration_str)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return timedelta(weeks=sign * weeks)

        # Split on T to separate date and time parts
        if 'T' in duration_str:
            date_part, time_part = duration_str.split('T', 1)
        else:
            date_part = duration_str
            time_part = ''

        days = 0
        hours = 0
        minutes = 0
        seconds = 0

        # Parse date part (days)
        if date_part:
            days_match = re.search(r'(\d+)D', date_part)
            if days_match:
                days = int(days_match.group(1))

        # Parse time part (hours, minutes, seconds)
        if time_part:
            hours_match = re.search(r'(\d+)H', time_part)
            if hours_match:
                hours = int(hours_match.group(1))

            minutes_match = re.search(r'(\d+)M', time_part)
            if minutes_match:
                minutes = int(minutes_match.group(1))

            seconds_match = re.search(r'(\d+(?:\.\d+)?)S', time_part)
            if seconds_match:
                seconds = float(seconds_match.group(1))

        return timedelta(
            days=sign * days,
            hours=sign * hours,
            minutes=sign * minutes,
            seconds=sign * seconds
        )

    # TODO this does not support "Customized Time Zone" sent by Microsoft Exchange
    # or really any of the VTIMEZONE stuff.  Not a problem so far in practice but something
    # to implement if we see a lot of custom timezones in the wild.

    # As per spec https://icalendar.org/iCalendar-RFC-5545/3-6-1-event-component.html
    # A calendar VEVENT component has a DTSTART and either a DTEND or a DURATION
    # but ultimately we just care about the event end, so we loop until we either
    # find DTEND or we find both DTSTART and DURATION and can compute DTEND
    lines = payload.split('\n')
    in_vevent = False
    start_date = None
    duration = None
    end_date = None
    for line in lines:
        line = line.strip()
        debug_out(line)
        if line.startswith('BEGIN:VEVENT'):
            debug_out('entering VEVENT')
            in_vevent = True
            continue
        if line.startswith('END:VEVENT'):
            debug_out('leaving VEVENT')
            in_vevent = False
            continue

        # Only process lines in the VEVENT section
        if not in_vevent:
            continue

        if line.startswith('DURATION'):
            duration = parse_duration(line[9:])
        if line.startswith('DTSTART'):
            start_date = parse_date_time(line, 'DTSTART')
        if line.startswith('DTEND'):
            end_date = parse_date_time(line, 'DTEND')

        if not end_date and start_date and duration:
            end_date = start_date + duration

        if end_date:
            now = datetime.now(tz=end_date.tzinfo)
            if end_date < now:
                print(str(end_date) + ' < ' + str(now) + ', returning OK')
                return "OK"
            else:
                print(str(end_date) + ' >= ' + str(now) + ', returning SKIP')
                return "SKIP"

    print('unable to determine event end date, returning SKIP')
    return "SKIP"

def proceed_if_past_event_tnef(part):
    """
        # IF its ms-tnef, it might be binary, and its definitely full of bugs
        # see https://support.microsoft.com/en-us/topic/how-email-message-formats-affect-internet-email-messages-in-outlook-3b2c0536-c1c0-1d68-19f0-8cae13c26722 and
        # and https://www.acumenitsupport.com/blog/email/calendar-attachments-showing-as-winmail-dat-rather-than-ics/
    """
    t = tnefparse.TNEF(base64.b64decode(part.get_payload()))

    end_date = next((p.data for p in t.msgprops if p.name_str == 'Date End'), None)
    if end_date is not None:
        now = datetime.now()
        if end_date < now:
            print(str(end_date) + ' < ' + str(now) + ', returning OK')
            return "OK"

    return "SKIP"

def proceed_if_past_event(ops) -> ActionResult:
    print('proceed_if_past_event')
    message = ops.fetch()

    if debug_enabled:
        _structure(message)
        # for part in message.walk():
        #     content_type = part.get_content_type()
        #     print(content_type)
        #     print(part.get_content_maintype() == 'multipart', part.is_multipart())

    for part in message.walk():
        content_type = part.get_content_type()
        if 'application/ms-tnef' in content_type:
            return proceed_if_past_event_tnef(part) or "SKIP"

        elif content_type == 'text/calendar':
            return proceed_if_past_event_icalendar(part) or "SKIP"

    return "SKIP"