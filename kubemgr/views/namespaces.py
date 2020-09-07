from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView
from collections import OrderedDict
import logging


class NsItem:
    def __init__(self, namespace):
        self.namespace = namespace
        self.selected = False
        logging.info(f"item {self} init")

    def to_dict(self):
        return self.namespace.to_dict()

    @property
    def name(self):
        return self.namespace.metadata.name

    def toggle(self):
        self.selected = not self.selected
        logging.info(f"item {self} selected: {self.selected}")


class NamespacesListModel(AsyncListModel):
    _current_cluster = None

    def fetch_data(self):
        cluster = self._application.selected_cluster

        if cluster:
            if cluster != self._current_cluster or not self._items:
                self._current_cluster = cluster
                api_client = cluster.api_client

                core_api = client.CoreV1Api(api_client)

                namespaces = core_api.list_namespace()
                self._items = [NsItem(i) for i in namespaces.items]
        else:
            self._items = []


class NamespacesListView(ResourceListView):
    def do_render_item(self, item, width):
        width = self._rect.width
        name = item.name[0 : width - 4]
        if len(name) < width - 4:
            name += " " * ((width - 4) - len(name))
        return name + ("(F)" if item.selected else " ")

    def _select(self, index):
        for i in range(self._model.get_item_count()):
            item = self._model.get_item(i)
            if i == index:
                logging.info(f"item {item.name} set toggle")
                item.toggle()
            else:
                logging.info(f"item {item.name} set false")
                item.selected = False
        super()._select(index)
