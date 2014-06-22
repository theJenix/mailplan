
import ConfigParser
import imaplib
from util import *
import os

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

def main():

    config = load_config_file("~/.mailplanrc")
    for account in config.list_enabled_accounts():
        server, auth, _ = config.get_account_config(account)
        imap = imaplib.IMAP4_SSL(server)
        imap.login(*auth)

        print imap.list()
        
        for rule in config.list_enabled_rules():
            select, search, action = config.get_rule_config(rule)
            searchparts = search.split(",")
            # Load the action from the actions folder, and get the action function
            # to use later.
            exec('import actions.' + action)
            actionfn = eval('actions.' + action + '.action')
            # TODO: support multiple select mailboxes
            imap.select(select)
            typ, msgnums = imap.search(None, *searchparts)
            if typ == "OK":
                for num in msgnums[0].split():
                    typ, data = imap.fetch(num, '(BODY.PEEK[HEADER] BODY.PEEK[TEXT])')
                    print 'Processing message %s\n%s\n' % (num, data[0][1])
                    actionfn(data[1][1], data[0][1])
                    break

if __name__ == "__main__":
    main()
