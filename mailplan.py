
from email.message import Message
import sys
import configparser
import imaplib
from typing import Any, Callable, Union
from actions.complex_action import ComplexAction
from util import *
import os
import re
import email

class MailPlanConfig:

    def __init__(self, filename):
        self.config = configparser.SafeConfigParser()
        expanded = os.path.expanduser(filename)
        print("Opening config file %s (%s)" % (filename, expanded))
        if expanded in self.config.read(expanded):
            print("Success!")
        else:
            print("Unable to open file")

    def list_enabled_accounts(self):
        v = self.config.get('accounts', 'enabled')
        return v.split(',')

    def get_account_config(self, account):
        """
            Get the configuration info for the specified
            account, and return the info as:
                (server, (login info), (options))
        """
        server   = self.config.get('accounts', account + '.server')
        username = self.config.get('accounts', account + '.username')
        password = self.config.get('accounts', account + '.password')
        return (server, (username, password), ())

    def list_enabled_rules(self):
        v = self.config.get('rules', 'enabled')
        return v.split(',')

    def get_rule_config(self, rule):
        """
            Get the configuration info for the specified
            rule, and return the info as:
                (select, search, action, order)
        """
        # TODO: support (search, [(action1, params1), (action2, params2), ...])
        select = self.config.get('rules', rule + '.select')
        search = self.config.get('rules', rule + '.search')
        action = self.config.get('rules', rule + '.action')
        # currently, we support empty or 'newest_first'; default to empty (None)
        order = self.config.get('rules', rule + '.order', fallback=None)

        return (select, search, action, order)

def load_config_file(filename):
    return MailPlanConfig(filename)

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

def filter_list(listitem):
    return [p for p in listitem if not p.startswith("(") and p != '"/"']

def resolve_one(str, typ):
    """
        Parse, import, and evaluate the python function specified on a search or action line
    """

    parts = str.split(':', 1)
    module = parts[0]

    exec('import %s.%s' % (typ, module))

    # If there are arguments, we assume the resolved module defines a make_ function
    # which will return the resolved function
    if len(parts) > 1:
        return eval('%s.%s.make_%s(%s)' % (typ, module, module, parts[1]))
    else:
        return eval('%s.%s.%s' % (typ, module, module))

def compose_search_and(fn1, fn2):
    if fn1 is None:
        return lambda *_: fn2()
    def composed():
        return '' + fn1() + ' ' + fn2() + ''
    return composed

class ComposedActions(ComplexAction):
    def __init__(self, *actions: Union[Callable[[Message, MessageOperations], None], ComplexAction]) -> None:
        self._actions = actions

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        for fn in self._actions:
            res = fn(*args)
            if res != "OK":
                return res
        return "OK"

    def after(self) -> Any:
        for fn in self._actions:
            if isinstance(fn, ComplexAction):
                fn.after()

def resolve_action(str) -> Union[Callable[[MessageOperations], None], ComplexAction]:

    """
        Resolve the action for a rule.  This could be a single action
        or a action chain; each action could be a simple function or a ComplexAction.
        This method will parse str to figure out which and to resolve each part
    """
    typ = 'actions'
    if str.startswith('\n'):
        # this is a chain; split by \n and resolve each part, then glue them together
        # NOTE: skip the first one, which will be empty
        parts = str.split('\n')[1:]
        return ComposedActions(*[resolve_one(part, typ) for part in parts])
    else:
        return resolve_one(str, typ)

def resolve_search(str) -> Callable[[], str]:

    """
        Resolve the search for a rule.  This could be a single function
        or a function chain; this method will parse str to figure out which and to
        resolve each part
    """
    typ = 'search'
    if str.startswith('\n'):
        # this is a chain; split by \n and resolve each part, then glue them together
        # NOTE: skip the first one, which will be empty
        parts = str.split('\n')[1:]
        resolved = None
        for part in parts:
            resolved = compose_search_and(resolved, resolve_one(part, typ))
        return resolved or (lambda *_: None)

    else:
        return resolve_one(str, typ)

    # Load the action from the actions folder, and get the action function
    # to use later.
def main():

    config = load_config_file("~/.mailplanrc")
    for account in config.list_enabled_accounts():
        server, auth, _ = config.get_account_config(account)
        imap = imaplib.IMAP4_SSL(server)
        imap.login(*auth)

#        imaplist = imap.list()
#        dirs = [' '.join([p.replace('"','') for p in filter_list(s.split(' '))]) for s in imaplist[1]]


 #       print imaplist[1]
  #      print dirs
   #     exit(1)
        for rule in config.list_enabled_rules():
            select, search, action, order = config.get_rule_config(rule)

            # TODO: maybe we should resolve everything first and then run them
            # doing this one at a time could cause issues with large rulesets in large inboxes
            # where e.g. the definition of today changes in the course of running thru the
            # rules; alternatively, for non-parameterzed functions, maybe cache the results
            searchfn = resolve_search(search)
            actionfn = resolve_action(action)
            # TODO: support multiple select mailboxes
            imap.select(select)
            term = searchfn()
            print("Searching in %s for %s" % (select, term))
            # Special case for gmail search, which needs to be passed as a literal
            if ('X-GM-RAW' in term):
                term = term.replace('X-GM-RAW ', '')
                imap.literal = term.encode('us-ascii')
                typ, msgnums = imap.search(None, 'X-GM-RAW')
                # imap.literal is consumed by imap.search
            else:
                typ, msgnums = imap.search(None, '(%s)' % term)

            if typ == "OK":
                msgnumarray = msgnums[0].split()
                print('Found %d messages' % len(msgnumarray))

                if order == 'newest_first':
                    msgnumarray = reversed(msgnumarray)

                for num in msgnumarray:
                    print('Processing message %s' % num)
                    ret = actionfn(MessageOperations(imap, [], select, num))
                    print('\n')
                    if (ret == "STOP"):
                        break

                if isinstance(actionfn, ComplexAction):
                    actionfn.after()

if __name__ == "__main__":
    main()
