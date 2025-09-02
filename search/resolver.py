
from typing import Callable
from common.resolve_one import resolve_one

def compose_search_and(fn1, fn2):
    if fn1 is None:
        return lambda *_: fn2()
    def composed():
        return '' + fn1() + ' ' + fn2() + ''
    return composed

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
