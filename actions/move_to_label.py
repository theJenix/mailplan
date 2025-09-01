def make_move_to_label(label):
    def move_to_label(message, ops):
        nonlocal label
        # Make sure we quote the label in case it has spaces or special characters
        ops.move('"' + label + '"')

    return move_to_label