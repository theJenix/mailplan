
from typing import TYPE_CHECKING, Any

from .types import ActionResult
from .complex_action import ComplexAction

if TYPE_CHECKING:
    from ..mailplan import MessageOperations

class CountAction(ComplexAction):
    def __init__(self, msg: str) -> None:
        self._count = 0
        self._msg = msg

    def call(self, ops: 'MessageOperations') -> ActionResult:
        self._count += 1
        return "OK"

    def after(self) -> Any:
        print(self._msg + ': ' + str(self._count))
        pass

def make_count(msg):
    return CountAction(msg)