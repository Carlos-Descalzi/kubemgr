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
            try:
                result = self._cluster.do_simple_get("/api/v1/namespaces")
                namespaces = json.loads(result.decode())["items"]
                return [NsItem(i) for i in namespaces]
            except Exception as e:
                logging.error(e)
        return []


class NamespacesListView(ResourceListView):
    def __init__(self, model):
        super().__init__(model=model, selectable=True)
        self.set_item_renderer(self._do_render_item)

    @property
    def current_item(self):
        item = super().current_item
        return item.namespace if item else None

    def _do_render_item(self, view, item):
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
