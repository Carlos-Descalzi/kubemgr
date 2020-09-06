from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView


class DeploymentsListModel(AsyncListModel):
    def __init__(self, application):
        super().__init__(application)
        self._namespace = None

    def fetch_data(self):
        cluster = self._application.selected_cluster

        if cluster:
            api_client = cluster.api_client
            api = client.AppsV1Api(api_client)

            if self._namespace:
                cronjobs = api.list_namespaced_deployment(self._namespace)
            else:
                cronjobs = api.list_deployment_for_all_namespaces()

            self._items = cronjobs.items
        else:
            self._items = []


class DeploymentsListView(ResourceListView):
    def do_render_item(self, item, width):
        return item.metadata.name
