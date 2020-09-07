from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView


class NodesListModel(AsyncListModel):
    def fetch_data(self):
        cluster = self._application.selected_cluster

        if cluster:
            api_client = cluster.api_client

            core_api = client.CoreV1Api(api_client)

            nodes = core_api.list_node()

            self._items = nodes.items
        else:
            self._items = []


class NodesListView(ResourceListView):
    def do_render_item(self, item, width):
        return item.metadata.name

    def on_key_press(self, input_key):

        if input_key == ord("l"):
            self._show_labels()
        else:
            super().on_key_press(input_key)

    def _show_labels(self):
        current = self.current_item

        labels = current.metadata.labels

        labels_text = [f"{k} : {v}" for k, v in labels.items()]
        self._show_text(labels_text)
