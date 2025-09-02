MailPlan
========

_Note that this is **SUPER ALPHA** software.  This is the result of a few hours of hacking on a Saturday afternoon, mostly to prove the concept and address a very specific need I had.  I will continue to develop it into something more general purpose, but for now, caveat emptor._

MailPlan is a command line mail rules engine written in Python.  MailPlan is not a full fledged email client, and it never will be; there's plenty of competition in that space.  Instead, MailPlan provides a way to define rules to select and perform actions on your emails.  Since the actions are written in Python, you can do pretty much anything you like to your emails, including parsing and automatically downloading linked files and moving or deleting the message itself.  You can even use MailPlan as a *mail delivery agent*, by defining an action that saves messages

# Features

* Command line, scriptable, cron-able mail rules engine.
* Supports IMAP4 over SSL only (for now), including version of IMAP4 supported by Gmail.com.
* Supports arbitrary actions that act on the mail header or message (other info TBD).
* 100% pure Python, with no platform dependencies or compiled libraries.


# Usage

To use MailPlan, you must first define a configuration file.  The configuration file for MailPlan is named .mailplanrc and lives in your home folder (i.e. ~/.mailplanrc).  This file must declare the following sections and properties:

```
[accounts]
enabled=primary

primary.server=mail.server.com
primary.username=me
primary.password=mypass

[rules]
enabled=file

file.select=INBOX
file.search=FROM *@important.com
file.action=file_important
```

The **[accounts]** section contains your email account information.  The *enabled* property allows you to selectively enable and disable accounts without removing the information.  When MailPlan runs, it will evaluate rules for every enabled account.

Each account is defined by a set of properties, prefixed by a name.  In this example, the account name is *primary*, and the properties that must be defined are *server*, *username*, and *password*.  Note that the account name used here must match the account name specified in the *enabled* property.

The **[rules]** section contains your rules to run.  Like with accounts, the *enabled* property allows you to selectively enable and disable rules without removing the information.  When MailPlan runs, it will evaluate every enabled rule.

Each rule is defined by a set of properties, prefixed by a name.  In this example, the rule name is *file*, and the properties that must be defined are:

* *select* - The mailbox to select before searching.  This is probably INBOX but it can be any mailbox or label accessible via the configured accounts.
* *search* - The search to use to query messages.  This expressed in standard IMAP4 search criteria format.
* *action* - The action to execute.  This action must exist in the *actions* subfolder.
* *order* - (optional) The order to process the emails.  Omit it to process the emails in the order returned from the server (likely smallest message number to biggest message number). This only supports the value "newest_first" for now.

# Actions

Actions are defined as .py files stored in the *actions* subfolder of MailPlan.  An action can be an arbitrary Python program; the only requirement is that the .py file define an *action* function as an entry point, e.g.:

```
def action(ops):
	...
```

This function can perform whatever action is required based on the header and message information.  It can use the *ops* parameter to perform IMAP operations on the message, such as fetch, copy, move, and delete.  The action function must return one of the following string values:

* OK - The action was performed correctly and the system can proceed with further processing.
* SKIP - The action was skipped, and the rest of the processing on this message should be skipped.
* ERROR - There was an error performing the action, and the appropriate information should be logged for analysis.
* STOP - The action indicates that the rule should stop processing (i.e. a limit or stop condition was reached).

# Example Rules

Move all email older than one day out of the inbox and into `[Mailplan]/To Be Filed`

```
clear_inbox.select=INBOX
clear_inbox.search=before_today
clear_inbox.action=move_to_label:"[Mailplan]/To Be Filed"
```

Move emails more than one day old with a List-Unsubscribe header to `[Mailplan]/Mailing Lists`
```
mailing_lists.select=INBOX
mailing_lists.search=
    before_today
    header:'List-Unsubscribe ""'

mailing_lists.action=
    # Gmail's header search will return false positives
    proceed_if_header_is_present:'list-unsubscribe'
    print_message
    count:'mailing_lists'
    move_to_label:"[Mailplan]/Mailing Lists"
```

Move notifications for past calendar events (i.e. notifications, responses, cancellation, etc) to `[Mailplan]/To Be Deleted`
```
old_calendar_notifications.select=INBOX
old_calendar_notifications.search=gmail:'(invite.ics OR invite.vcs) has:attachment'
old_calendar_notifications.action=
    proceed_if_past_event
    move_to_label:"[Mailplan]/To Be Deleted"

old_calendar_notifications.order=newest_first
```

Note that the move_to_label can accept any IMAP label.  These examples use a `[Mailplan]` parent label but you can change this to whatever you want.

# Future Plans

- [x] Compose actions from action sequences, directly in .mailplanrc file
  - Supported by defining multiline searches or actions.  See the examples above.
- [-] Define reusable set of actions, to use in composed action sequences
  - Partially implemented.  There's still a lot to do here.
- Multiple mailboxes per rule (currently only one mailbox is allowed in the select property)
- Selectively enable rules for each account (currently, all rules run on all accounts).
- CLI options
  - Select custom configuration file
  - Run only a specific rule (whether or not its enabled)
- Rule development workflow - hot reload, dry runs, and undoable actions to develop and test rules more easily
- Client side search validators
- Full support for X-GM-RAW (currently supports single terms using the gmail: search but does not support composing search from individual clauses)
