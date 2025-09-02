from email.message import Message
import imaplib
import re
import email

class MessageOperations:

    def __init__(self, imap: imaplib.IMAP4_SSL, dirs, path, msgnum, raw_header = None, raw_body = None):
        self.imap = imap
        self.dirs = dirs
        self.path = path
        self.msgnum = msgnum
        self.raw_header = raw_header
        self.raw_body = raw_body

        self._message = None # type: Message | None

    def copy(self, newpath, create=True):
        self.imap.select(self.path)
#        if newpath not in self.dirs:
#            if not create:
#                return None
#        self.imap.create(newpath)
#            self.dirs = self.dirs + newpath
        status, r = self.imap.copy(self.msgnum, newpath)
        newmo = None
        if status == "OK":
            rstr = r[0].decode('utf-8')
            # OK ['[COPYUID 103 129044 1] (Success)']
            m = re.search("(\d+)\]", rstr)
            newmo = MessageOperations(self.imap, self.dirs, newpath, int(m.group(1)), self.raw_header, self.raw_body)
        return newmo

    def delete(self):
        self.imap.select(self.path)
        self.imap.store(self.msgnum, '+FLAGS', '\\Deleted')

    def fetch(self) -> Message:
        if self._message:
            return self._message
        # TODO: check response and handle errors
        typ, data = self.imap.fetch(self.msgnum, '(BODY.PEEK[HEADER] BODY.PEEK[TEXT])')
        header = b''
        text = b''
        for response_part in data:
            if isinstance(response_part, tuple):
                part_str = response_part[0].decode('utf-8')
                if '[HEADER]' in part_str:
                    header = response_part[1]
                if '[TEXT]' in part_str:
                    text = response_part[1]

        # Parse the header + the text to get us a complete message
        message = email.message_from_bytes(header + text)
        self._message = message
        self.raw_header = header
        self.raw_body = text
        return self._message

    def move(self, newpath, create=True):

        # TODO: this assumes the newpath already exists; at least with GMAIL if it doesn't
        # we'll get an error like NO [b'[TRYCREATE] No folder Target Folder (Failure)']
        print("Moving message ", str(self.msgnum), " to ", newpath)

#        newmo = self.copy(newpath, create)
#        if newmo:
#            self.delete()
#        return newmo

        status, r = self.imap._simple_command('MOVE', self.msgnum, newpath)

        newmo = None
        if status == "OK":
            rstr = r[0].decode('utf-8')
            # OK ['[COPYUID 103 129044 1] (Success)']
            m = re.search("(\d+)\]", rstr)
            newmo = MessageOperations(self.imap, self.dirs, newpath, int(m.group(1)), self.raw_header, self.raw_body)
        else:
            print(status + ' ' + str(r))
        return newmo
