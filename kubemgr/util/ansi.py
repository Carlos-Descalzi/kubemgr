import sys
import subprocess
import re

UNDERLINE = "\u001b[4m"
BOLD = "\u001b[1m"
UNDERLINE = "\u001b[4m"
RESET = "\u001b[0m"
CLRSCR = "\u001b[2J"


class UiWriter:
    def __init__(self):
        self._buffer = ""

    def clrscr(self):
        self._buffer += CLRSCR
        return self

    def underline(self):
        self._buffer += UNDERLINE
        return self

    def reverse(self):
        self._buffer += REVERSE
        return self

    def bold(self):
        self._buffer += BOLD
        return self

    def reset(self):
        self._buffer += RESET
        return self

    def gotoxy(self, x, y):
        self._buffer += f"\u001b[{y};{x}H"
        return self

    def write(self, string):
        self._buffer += string
        return self

    def writefill(self, string, length):
        str_len = _ansi_string_len(string)
        self._buffer += string + " " * (length - str_len)
        return self

    def fg(self, color):
        self._buffer += f"\u001b[38;5;{color}m"
        return self

    def bg(self, color):
        self._buffer += f"\u001b[48;5;{color}m"
        return self

    def put(self):
        sys.stdout.write(self._buffer)
        sys.stdout.flush()

    def __str__(self):
        return self._buffer

    def __len__(self):
        return _ansi_string_len(self._buffer)


def _ansi_string_len(string):
    l = 0
    skip = False
    for c in string:
        if c == "\u001b":
            skip = True
        elif c in "mHJ" and skip:
            skip = False
        elif not skip:
            l += 1
    return l


def begin():
    return UiWriter()


def terminal_size():
    output = subprocess.check_output(["stty", "size"]).decode()
    return tuple(map(int, output.strip().split(" ")))


def cursor_on():
    subprocess.check_output(["tput", "cnorm"])


def cursor_off():
    subprocess.check_output(["tput", "civis"])
