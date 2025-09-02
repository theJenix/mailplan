
from typing import TYPE_CHECKING

from .types import ActionResult

if TYPE_CHECKING:
    from ..mailplan import MessageOperations

def print_message(ops: 'MessageOperations') -> ActionResult:
    message = ops.fetch()
    print('Fetched message %s\nDate: %s\nFrom: %s\nSubject: %s\n' % (ops.msgnum, message['date'], message['from'], message['subject']))
    return "OK"