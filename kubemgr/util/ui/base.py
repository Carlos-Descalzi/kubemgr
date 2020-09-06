from kubemgr.util import ansi
import time
import sys
import tty

COLORS = {
    "titledview.bg": "\u001b[48;5;241m",
    "titledview.fg": "\u001b[38;5;0m",
    "titledview.focused.bg": "\u001b[48;5;244m",
    "titledview.focused.fg": "\u001b[38;5;255m",
    "tabbedview.bg": "\u001b[48;5;241m",
    "tabbedview.fg": "\u001b[38;5;0m",
    "tabbedview.focused.bg": "\u001b[48;5;244m",
    "tabbedview.focused.fg": "\u001b[38;5;255m",
    "tabbedview.selected.bg": "\u001b[48;5;241m",
    "tabbedview.selected.fg": "\u001b[38;5;0m",
    "tabbedview.focused.selected.bg": "\u001b[48;5;244m",
    "tabbedview.focused.selected.fg": "\u001b[38;5;255m\u001b[1m",
    "textview.bg": "\u001b[48;5;236m",
    "textview.fg": "\u001b[38;5;255m",
}


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def copy(self):
        return Point(self.x, self.y)

    def __str__(self):
        return f"Point:{self.x},{self.y}"

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y


class Dimension:
    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height

    def copy(self):
        return Dimension(self.width, self.height)

    def __str__(self):
        return f"Dimension:{self.width},{self.height}"

    def __eq__(self, other):
        return (
            isinstance(other, Dimension)
            and self.width == other.width
            and self.height == other.height
        )


class Rect:
    def __init__(self, x=0, y=0, width=0, height=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def copy(self):
        return Rect(self.x, self.y, self.width, self.height)

    def __str__(self):
        return f"Rect:{self.x},{self.y},{self.width},{self.height}"

    @property
    def location(self):
        return Point(self.x, self.y)

    @property
    def dimension(self):
        return Dimension(self.width, self.height)

    def __eq__(self, other):
        return (
            isinstance(other, Rect)
            and self.x == other.x
            and self.y == other.y
            and self.width == other.width
            and self.height == other.height
        )
