
import ConfigParser
import imaplib
from util import *
import os
import re

class MailPlanConfig:

    def __init__(self, filename):
        self.config = ConfigParser.SafeConfigParser()
        expanded = os.path.expanduser(filename)
        print "Opening config file %s (%s)" % (filename, expanded)
        if expanded in self.config.read(expanded):
            print "Success!"
        else:
            print "Unable to open file"

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
                (select, search, action)
        """
        # TODO: support (search, [(action1, params1), (action2, params2), ...])
        select = self.config.get('rules', rule + '.select')
        search = self.config.get('rules', rule + '.search')
        action = self.config.get('rules', rule + '.action') 
        return (select, search, action)

def load_config_file(filename):
    return MailPlanConfig(filename)

class MessageOperations:

    def __init__(self, imap, dirs, path, msgnum):
        self.imap = imap
        self.dirs = dirs
        self.path = path
        self.msgnum = msgnum

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
            # OK ['[COPYUID 103 129044 1] (Success)']
            m = re.search("(\d+)\]", r[0])
            newmo = MessageOperations(self.imap, self.dirs, newpath, int(m.group(1)))
        return newmo

    def delete(self):
        self.imap.select(self.path)
        self.imap.store(self.msgnum, '+FLAGS', '\\Deleted')

    def move(self, newpath, create=True):
        
        print "Moving message to ", newpath
        newmo = self.copy(newpath, create)
        if newmo:
            self.delete()
        return newmo

def filter_list(listitem):
    return [p for p in listitem if not p.startswith("(") and p != '"/"']

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
            select, search, action = config.get_rule_config(rule)
            # Load the action from the actions folder, and get the action function
            # to use later.
            exec('import actions.' + action)
            actionfn = eval('actions.' + action + '.action')
            # TODO: support multiple select mailboxes
            imap.select(select)
            typ, msgnums = imap.search(None, '(%s)' % search)
            if typ == "OK":
                for num in reversed(msgnums[0].split()):
                    typ, data = imap.fetch(num, '(BODY.PEEK[HEADER] BODY.PEEK[TEXT])')
                    print 'Processing message %s\n%s\n' % (num, data[0][1])
                    actionfn(data[1][1], data[0][1], MessageOperations(imap, [], select, num))

if __name__ == "__main__":
    main()
