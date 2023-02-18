from cdtui import ansi, ListModel, ListView
from typing import List
from kubemgr.cluster import Cluster
from .util import AsyncListModel
import logging

_logger = logging.getLogger(__name__)
class Context:
    def __init__(self, context):
        self.context = context

    @property
    def name(self):
        return self.context["name"]

class ContextsListModel(AsyncListModel):


    def __init__(self, application):
        super().__init__(application)
        self._cluster = None

    def set_cluster(self, cluster: Cluster):
        self._cluster = cluster
        self.refresh()

    def get_cluster(self) -> Cluster:
        return self._cluster

    cluster = property(get_cluster, set_cluster)

    def enabled(self):
        return self._cluster is not None

    def fetch_data(self):
        if self._cluster and self._cluster.connected:
            return [Context(c) for c in self._cluster.get_contexts()]
        return []

    def is_item_selected(self, item):
        return item.context == self._cluster.get_active_context()


class ContextsListView(ListView):

    def render_item(self, item, current, selected: bool) -> str:

        buff = ansi.begin()

        if self.focused and current:
            buff.underline()
        if self._model.is_item_selected(item):
            buff.writefill(f"<{item.name}>", self._rect.width - 4)
        else:
            buff.writefill(f" {item.name} ", self._rect.width - 4)

        buff.reset()
        return str(buff)





