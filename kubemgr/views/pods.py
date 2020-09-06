from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView


class PodsListModel(AsyncListModel):
    def __init__(self, application):
        super().__init__(application)
        self._namespace = None

    def get_core_api(self):
        cluster = self._application.selected_cluster
        if cluster:
            api_client = cluster.api_client
            return client.CoreV1Api(api_client)
        return None

    def fetch_data(self):

        core_api = self.get_core_api()

        if core_api:
            if self._namespace:
                pods = core_api.list_namespaced_pod(self._namespace)
            else:
                pods = core_api.list_pod_for_all_namespaces()

            self._items = pods.items
        else:
            self._items = []


class PodsListView(ResourceListView):
    def on_key_press(self, input_key):
        if input_key == ord("l"):
            self._show_logs()
        else:
            super().on_key_press(input_key)

    def _show_logs(self):

        core_api = self._model.get_core_api()

        if core_api:
            current = self.current_item
            pod_name = current.metadata.name
            namespace = current.metadata.namespace
            logs = core_api.read_namespaced_pod_log(pod_name, namespace).split("\n")

            self._show_text(logs)

    def do_render_item(self, item, width):

        name_width = width - 10
        pod_name = item.metadata.name[0:name_width]
        pod_name += " " * (name_width - len(pod_name))
        status = item.status.phase

        return f"{pod_name}{status:>10}"
