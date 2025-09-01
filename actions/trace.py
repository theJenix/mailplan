
def make_trace(msg):
    def trace(message, ops):
        nonlocal msg
        print(msg)

    return trace