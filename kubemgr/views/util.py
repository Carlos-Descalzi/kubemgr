from kubemgr.util.ui import ListModel
from abc import ABCMeta, abstractmethod

class AsyncListModel(ListModel, metaclass=ABCMeta):

    def __init__(self, application):
        self._application = application
        self._application.add_task(self.fetch_data)
        self._items = []

    def get_item_count(self):
        return len(self._items)

    def get_item(self, index):
        return self._items[index]

    @abstractmethod
    def fetch_data(self):
        pass
