
import imaplib
from actions.complex_action import ComplexAction
from actions.resolver import resolve_action
from common.mail_plan_config import load_config_file
from common.message_operations import MessageOperations
from search.resolver import resolve_search

def main():

    config = load_config_file("~/.mailplanrc")
    for account in config.list_enabled_accounts():
        server, auth, _ = config.get_account_config(account)
        imap = imaplib.IMAP4_SSL(server)
        imap.login(*auth)

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
