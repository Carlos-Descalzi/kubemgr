from kubemgr.util import ansi
import time
import sys
import tty

class Point:

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def copy(self):
        return Point(self.x, self.y)

    def __str__(self):
        return f"Point:{self.x},{self.y}"

    def __eq__(self, other):
        return (
            isinstance(other, Point)
            and self.x == other.x
            and self.y == other.y
        )

class Dimension:

    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height

    def copy(self):
        return Dimension(self.width, self.height)

    def __str__(self):
        return f'Dimension:{self.width},{self.height}'

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

COLORS = {}
