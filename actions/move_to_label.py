
from .types import ActionResult

def make_move_to_label(label):
    def move_to_label(ops) -> ActionResult:
        nonlocal label
        # Make sure we quote the label in case it has spaces or special characters
        ops.move('"' + label + '"')
        return "OK"

    return move_to_label