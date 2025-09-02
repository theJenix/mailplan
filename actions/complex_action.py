
from typing import Any

from .types import ActionResult

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..mailplan import MessageOperations

class ComplexAction:

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.call(args[0])

    def call(self, ops: 'MessageOperations') -> ActionResult:
        print('Action must implement call method')
        return 'STOP'

    def after(self) -> None:
        pass