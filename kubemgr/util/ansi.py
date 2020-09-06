import sys
import subprocess


class UiWriter:
    def __init__(self):
        self._buffer = ""

    def clrsrc(self):
        self._buffer += "\u001b[2J"
        return self

    def underline(self):
        self._buffer += "\u001b[4m"
        return self

    def reverse(self):
        self._buffer += "\u001b[7m"
        return self

    def bold(self):
        self._buffer += "\u001b[1m"
        return self

    def reset(self):
        self._buffer += "\u001b[0m"
        return self

    def gotoxy(self, x, y):
        self._buffer += f"\u001b[{y};{x}H"
        return self

    def write(self, string):
        self._buffer += string
        return self

    def writefill(self, string, length):
        self._buffer += string + " " * (length - len(string))
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

def begin():
    return UiWriter()

def terminal_size():
    output = subprocess.check_output(['stty','size']).decode()
    return tuple(map(int,output.strip().split(' ')))

def cursor_on():
    subprocess.check_output(['tput','cnorm'])

def cursor_off():
    subprocess.check_output(['tput','civis'])
