import configparser
import os

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
