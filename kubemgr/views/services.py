from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView


class ServicesListModel(AsyncListModel):
    def __init__(self, application):
        super().__init__(application)
        self._namespace = None

    def set_namespace(self, namespace):
        self._namespace = namespace

    def fetch_data(self):
        cluster = self._application.selected_cluster

        if cluster:
            api_client = cluster.api_client

            core_api = client.CoreV1Api(api_client)

            if self._namespace:
                pods = core_api.list_namespaced_service(self._namespace)
            else:
                pods = core_api.list_service_for_all_namespaces()

            self._items = pods.items
        else:
            self._items = []


class ServicesListView(ResourceListView):
    def do_render_item(self, item, width):
        return item.metadata.name
