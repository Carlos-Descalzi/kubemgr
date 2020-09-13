import tempfile


def word_wrap_text(string, length):
    buff = ""

    for line in string.split("\n"):

        current_line = ""

        for word in line.split(" "):
            if len(current_line + " " + word) > length:
                buff += "\n" + current_line
                current_line = ""
            else:
                current_line += " "
            current_line += word

        buff += current_line + "\n"

    return buff


def make_tempfile(text, format_hint=None):
    suffix = f".{format_hint}" if format_hint else None
    tf = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=suffix)
    tf.write(text)
    tf.flush()
    return tf
