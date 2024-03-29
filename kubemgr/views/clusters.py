from cdtui import ansi, ListModel, ListView
import logging
from typing import List, Optional
from kubemgr.cluster import Cluster


class ClustersListModel(ListModel):
    _clusters = None

    def __init__(self, application):
        super().__init__()
        self._application = application
        self.set_clusters([])

    def set_clusters(self, clusters:Optional[List[Cluster]]=None):
        if self._clusters:
            for cluster in self._clusters:
                cluster.on_connect.remove(self._connected)
                cluster.on_error.remove(self._error)
        self._clusters = sorted(clusters or [], key=lambda x: x.name)
        for cluster in self._clusters:
            cluster.on_connect.add(self._connected)
            cluster.on_error.add(self._error)

    def _connected(self, cluster:Cluster):
        self.notify_list_changed()
        logging.info(f"{cluster} Connected!")

    def _error(self, cluster, error):
        self.notify_list_changed()
        logging.error(f"Connection error! {cluster} {error}")

    def get_item_count(self) -> int:
        return len(self._clusters) if self._clusters else 0

    def get_item(self, index):
        return self._clusters[index] if self._clusters else None


class ClusterListView(ListView):
    def render_item(self, item, current, selected):
        buff = ansi.begin()
        if self.focused and current:
            buff.underline()
        if selected:
            buff.writefill(f"<{item.name}>", self._rect.width - 4)
        else:
            buff.writefill(f" {item.name} ", self._rect.width - 4)
        if item.connected:
            buff.fg(2).write("(C)")
        elif item.connecting:
            buff.write("...")
        elif item.connection_error:
            buff.fg(1).write("<X>")
        buff.reset()
        return str(buff)
