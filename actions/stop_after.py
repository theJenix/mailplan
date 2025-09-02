
from .types import ActionResult

def make_stop_after(stop_after_str: str):
    _stop_after = int(stop_after_str)
    _count = 0
    def stop_after(ops) -> ActionResult:
        nonlocal _count
        _count += 1
        if _count >= _stop_after:
            print('Stopping after %d messages.' % _stop_after)
            return "STOP"

        return "OK"

    return stop_after