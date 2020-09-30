from cdtui import ListModel
from abc import ABCMeta, abstractmethod
import logging
import json
from typing import List, Any
from datetime import datetime, timedelta, timezone


class AsyncListModel(ListModel, metaclass=ABCMeta):
    def __init__(self, application, periodic=True):
        super().__init__()
        self._application = application
        self._periodic = periodic
        self._items = []
        self._application.add_task(self._async_fetch_data, periodic)

    def refresh(self):
        """
        Forces refresh of contents
        """
        self._application.add_task(self._async_fetch_data, False)

    def get_item_count(self) -> int:
        return len(self._items)

    def get_item(self, index: int) -> Any:
        return self._items[index]

    def _async_fetch_data(self):
        items = self.fetch_data()
        changed = items != self._items
        self._items = items
        if changed:
            self.notify_list_changed()

    @abstractmethod
    def fetch_data(self) -> List:
        pass


import re

_PARSERS = [
    (re.compile("^([0-9]+)$"), lambda x: int(x)),
    (re.compile("^([0-9]+)K[ibB]?$"), lambda x: int(x) * 1024),
    (re.compile("^([0-9]+)M[ibB]?$"), lambda x: int(x) * (1024 ** 2)),
    (re.compile("^([0-9]+)G[ibB]?$"), lambda x: int(x) * (1024 ** 3)),
]


def _parse_mem(string):
    for regex, converter in _PARSERS:
        matched = regex.match(string)
        if matched:
            value = matched.groups()[0]
            return converter(value)
    return None


def _format_mem(val):
    if val < 1024:
        return f"{val}B"
    if val < 1024 ** 2:
        v = int(val / 1024)
        return f"{v}KB"
    if val < 1024 ** 3:
        v = int(val / (1024 ** 2))
        return f"{v}MB"
    v = int(val / (1024 ** 3))
    return f"{v}GB"


def _do_fill(string, length):
    # > 0 means left padding, < 0 right padding.
    l = abs(length)
    if len(string) > l:
        string = string[0:l]
    elif len(string) < l:
        padding = " " * (l - len(string))
        if length > 0:
            string += padding
        else:
            string = padding + string
    return string


def _do_age(date_string):
    now = datetime.now(tz=timezone.utc)
    dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
    delta = now - dt

    if delta.days > 0:
        return f"{delta.days}d"

    minutes = int(delta.seconds / 60) % 60
    hours = int(delta.seconds / (60 * 60)) % 24
    delta_str = ""
    if hours > 0:
        delta_str += f"{hours}h"
    delta_str += f"{minutes}m"
    return delta_str


BASE_JINJA_CONTEXT = {
    "parse_mem": _parse_mem,
    "format_mem": _format_mem,
    "fill": _do_fill,
    "age": _do_age,
    "str": str,
    "int": int,
}
