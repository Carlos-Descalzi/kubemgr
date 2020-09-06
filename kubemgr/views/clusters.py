from kubemgr.util.ui import ListModel, ListView
from ..util import ansi


class ClustersListModel(ListModel):
    def __init__(self, application):
        self._application = application
        self._clusters = sorted(list(self._application.clusters.keys()))

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
            buff.write(f"<{item}>")
        else:
            buff.write(f" {item} ")
        buff.reset()
        return str(buff)
