from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView
from collections import OrderedDict
import logging
import json


class NsItem:
    def __init__(self, namespace):
        self.namespace = namespace
        self.selected = False

    def to_dict(self):
        return self.namespace.to_dict()

    @property
    def name(self):
        return self.namespace["metadata"]["name"]

    def toggle(self):
        self.selected = not self.selected


class NamespacesListModel(AsyncListModel):

    _cluster = None

    def __init__(self, application):
        super().__init__(application, False)

    def set_cluster(self, cluster):
        self._cluster = cluster
        self.refresh()

    def get_cluster(self):
        return self._cluster

    cluster = property(get_cluster, set_cluster)

    def enabled(self):
        return self._cluster is not None

    def fetch_data(self):
        if self._cluster and self._cluster.connected:
            api_client = self._cluster.api_client

            response, status, _ = self._cluster.api_client.call_api(
                "/api/v1/namespaces", "GET", _preload_content=False
            )
            namespaces = json.loads(response.data.decode())["items"]
            self._items = [NsItem(i) for i in namespaces]
        else:
            self._items = []


class NamespacesListView(ResourceListView):
    @property
    def current_item(self):
        item = super().current_item
        return item.namespace if item else None

    def do_render_item(self, item, width):
        width = self._rect.width
        name = item.name[0 : width - 4]
        name += " " * max(0, ((width - 4) - len(name)))
        name += "(F)" if item.selected else " "
        return name

    def _select(self, index):
        for i in range(self._model.get_item_count()):
            item = self._model.get_item(i)
            if i == index:
                item.toggle()
            else:
                item.selected = False
        super()._select(index)
