from typing import TYPE_CHECKING

from .types import ActionResult

if TYPE_CHECKING:
    from ..mailplan import MessageOperations

def make_proceed_if_header_is_present(header):
    def proceed_if_header_is_present(ops: 'MessageOperations') -> ActionResult:
        print('proceed_if_header_is_present')
        message = ops.fetch()

        header_value = message.get(header)
        print(f'Header {header} is {message.get(header)}')
        if header_value:
            return "OK"

        return "SKIP"
    return proceed_if_header_is_present