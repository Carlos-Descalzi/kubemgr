from kubemgr.util.ui import ListModel, ListView
from ..util import ansi
import logging


class ClustersListModel(ListModel):
    def __init__(self, application):
        self._application = application
        self._clusters = None

    def set_clusters(self, clusters=[]):
        self._clusters = sorted(self._application.clusters, key=lambda x: x.name)
        for cluster in self._clusters:
            cluster.set_on_connect_handler(self._connected)
            cluster.set_on_error_handler(self._error)

    def _connected(self, cluster):
        logging.info(f"{cluster} Connected!")

    def _error(self, cluster, error):
        logging.error(f"Connection error! {cluster} {error}")

    def get_item_count(self):
        return len(self._clusters)

    def get_item(self, index):
        return self._clusters[index]


_SPINNER = "-\\|/"


class ClusterListView(ListView):
    _ticks = 0

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
            buff.write(" ").write(_SPINNER[self._ticks % 4])
        elif item.connection_error:
            buff.fg(1).write("<X>")
        buff.reset()
        if item == self._model.get_item(self._model.get_item_count() - 1):
            self._ticks += 1
        return str(buff)
