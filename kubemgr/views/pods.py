from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView


class PodsListModel(AsyncListModel):
    def __init__(self, application):
        super().__init__(application)
        self._namespace = None

    def fetch_data(self):
        cluster = self._application.selected_cluster

        if cluster:
            api_client = cluster.api_client

            core_api = client.CoreV1Api(api_client)

            if self._namespace:
                pods = core_api.list_namespaced_pod(self._namespace)
            else:
                pods = core_api.list_pod_for_all_namespaces()

            self._items = pods.items
        else:
            self._items = []


class PodsListView(ResourceListView):

    def do_render_item(self, item, width):

        name_width = width - 10
        pod_name = item.metadata.name[0:name_width]
        pod_name += " " * (name_width - len(pod_name))
        status = item.status.phase

        return f"{pod_name}{status:>10}"
