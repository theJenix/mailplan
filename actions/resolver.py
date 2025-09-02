
from email.message import Message
from typing import Any, Callable, Union
from actions.complex_action import ComplexAction
from common.message_operations import MessageOperations
from common.resolve_one import resolve_one

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
