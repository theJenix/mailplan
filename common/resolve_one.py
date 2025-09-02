
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
