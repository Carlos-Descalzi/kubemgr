from kubemgr.util.ui import ListModel
from abc import ABCMeta, abstractmethod
import logging
import json


class AsyncListModel(ListModel, metaclass=ABCMeta):
    def __init__(self, application, periodic=True):
        self._application = application
        self._periodic = periodic
        self._items = []
        self._application.add_task(self.fetch_data, periodic)

    def refresh(self):
        self._application.add_task(self.fetch_data, False)

    def get_item_count(self):
        return len(self._items)

    def get_item(self, index):
        return self._items[index]

    @abstractmethod
    def fetch_data(self):
        pass
