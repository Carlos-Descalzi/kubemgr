from kubernetes import client
from .util import AsyncListModel
from .resource import ResourceListView


class CronJobsListModel(AsyncListModel):
    def __init__(self, application):
        super().__init__(application)
        self._namespace = None

    def set_namespace(self, namespace):
        self._namespace = namespace

    def fetch_data(self):
        cluster = self._application.selected_cluster

        if cluster:
            api_client = cluster.api_client

            api = client.BatchV1beta1Api(api_client)

            if self._namespace:
                cronjobs = api.list_namespaced_cron_job(self._namespace)
            else:
                cronjobs = api.list_cron_job_for_all_namespaces()

            self._items = cronjobs.items
        else:
            self._items = []


class CronJobsListView(ResourceListView):
    def do_render_item(self, item, width):

        name_width = width - 10
        cronjob_name = item.metadata.name[0:name_width]
        cronjob_name += " " * (name_width - len(cronjob_name))

        return f"{cronjob_name} {item.spec.schedule}"
