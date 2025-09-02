
from .types import ActionResult

def make_trace(msg):
    def trace(ops) -> ActionResult:
        nonlocal msg
        print(msg)
        return "OK"

    return trace