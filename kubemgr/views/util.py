from kubemgr.util.ui import ListModel
from abc import ABCMeta, abstractmethod
import logging
import json
from typing import List, Any


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
