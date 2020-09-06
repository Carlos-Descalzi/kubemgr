from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView

class NamespacesListModel(AsyncListModel):

    def fetch_data(self):
        cluster = self._application.selected_cluster

        if cluster:
            api_client = cluster.api_client

            core_api = client.CoreV1Api(api_client)

            namespaces = core_api.list_namespace()

            self._items = namespaces.items
        else:
            self._items = []

class NamespacesListView(ResourceListView):

    def do_render_item(self, item, width):
        return item.metadata.name
