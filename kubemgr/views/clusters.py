from kubemgr.util.ui import ListModel, ListView
from ..util import ansi


class ClustersListModel(ListModel):
    def __init__(self, application):
        self._application = application
        self._clusters = sorted(self._application.clusters, key=lambda x: x.name)

    def get_item_count(self):
        return len(self._clusters)

    def get_item(self, index):
        return self._clusters[index]


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
            buff.write("(C)")
        buff.reset()
        return str(buff)
