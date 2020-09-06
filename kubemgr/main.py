import os
import time
import configparser
import yaml
from .util import ansi
from .util.ui import COLORS, Application, Rect, TitledView, TabbedView
from .util.executor import TaskExecutor
from .views.clusters import ClusterListView, ClustersListModel
from .views.nodes import NodesListView, NodesListModel
from .views.pods import PodsListView, PodsListModel
from .views.cronjobs import CronJobsListModel, CronJobsListView
from .views.jobs import JobsListModel, JobsListView
from .views.namespaces import NamespacesListModel, NamespacesListView
from .views.services import ServicesListModel, ServicesListView
from .views.configmaps import ConfigMapsListModel, ConfigMapsListView
from .views.deployments import DeploymentsListModel, DeploymentsListView
from kubernetes import client, config
from kubernetes.client import configuration
from kubernetes.config.kube_config import KubeConfigLoader
from abc import ABCMeta, abstractmethod
import tty
import sys
import atexit


class Cluster:
    def __init__(self, config_file, config, api_client=None):
        self.config_file = config_file
        self.config = config
        self._api_client = api_client

    @property
    def api_client(self):
        if not self._api_client:
            self._api_client = client.ApiClient(self.config)
        return self._api_client


class MainApp(Application):
    def __init__(self, config_dir):
        super().__init__()
        self._task_executor = TaskExecutor()
        self._clusters = {}
        self._selected_cluster_name = None
        self._read_configuration(config_dir)

        self._clusters_model = ClustersListModel(self)
        self._clusters_view = ClusterListView(model=self._clusters_model)
        self._clusters_view.selectable = True
        self._nodes_model = NodesListModel(self)
        self._nodes_view = NodesListView(model=self._nodes_model)
        self._pods_model = PodsListModel(self)
        self._pods_view = PodsListView(model=self._pods_model)
        self._cron_jobs_model = CronJobsListModel(self)
        self._cron_jobs_view = CronJobsListView(model=self._cron_jobs_model)
        self._jobs_model = JobsListModel(self)
        self._jobs_view = JobsListView(model=self._jobs_model)
        self._services_model = ServicesListModel(self)
        self._services_view = ServicesListView(model=self._services_model)
        self._namespaces_model = NamespacesListModel(self)
        self._namespaces_view = NamespacesListView(model=self._namespaces_model)
        self._configmaps_model = ConfigMapsListModel(self)
        self._configmaps_view = ConfigMapsListView(model=self._configmaps_model)
        self._deployments_model = DeploymentsListModel(self)
        self._deployments_view = DeploymentsListView(model=self._deployments_model)

        max_height, max_width = ansi.terminal_size()

        h_divider_pos = int(max_width * 0.25)

        v_clusters_height = int(max_height * 0.3)
        v_nodes_start = v_clusters_height + 1
        v_nodes_height = int(max_height * 0.3)
        v_namespaces_start = v_nodes_start + v_nodes_height + 1
        v_namespaces_height = max_height - v_namespaces_start -1

        tab_width = max_width - (h_divider_pos + 1)

        self.add_component(
            TitledView(
                rect=Rect(1, 1, h_divider_pos, v_clusters_height), 
                title="Clusters", 
                inner=self._clusters_view
            )
        )
        self.add_component(
            TitledView(
                rect=Rect(1, v_nodes_start, h_divider_pos, v_nodes_height), 
                title="Nodes", 
                inner=self._nodes_view
            )
        )
        self.add_component(
            TitledView(
                rect=Rect(1, v_namespaces_start, h_divider_pos, v_namespaces_height),
                title="Namespaces",
                inner=self._namespaces_view
            )
        )
        tabs = TabbedView(
            rect=Rect(h_divider_pos + 1, 1, tab_width, 30)
        )
        
        tabs.add_tab("Pods", self._pods_view)
        tabs.add_tab("Cronjobs", self._cron_jobs_view)
        tabs.add_tab("Jobs", self._jobs_view)
        tabs.add_tab("Services", self._services_view)
        tabs.add_tab("Deployments", self._deployments_view)
        tabs.add_tab("ConfigMaps", self._configmaps_view)
        self.add_component(tabs)

        self._task_executor.start()

    def add_task(self, task):
        self._task_executor.add_task(task)

    def set_selected_cluster_name(self, cluster_name):
        self._selected_cluster_name = cluster_name

    def get_selected_cluster_name(self):
        return self._selected_cluster_name

    selected_cluster_name = property(
        get_selected_cluster_name, set_selected_cluster_name
    )

    @property
    def clusters(self):
        return self._clusters

    @property
    def selected_cluster(self):
        if self._selected_cluster_name:
            return self._clusters[self._selected_cluster_name]
        return None

    def _read_configuration(self, config_dir):

        colors_config_file = os.path.join(config_dir, "colors.ini")

        if os.path.isfile(colors_config_file):
            parser = configparser.ConfigParser()
            parser.read(colors_config_file)

            for key in parser['DEFAULT']:
                color_val = parser['DEFAULT'][key]
                color = bytes(color_val, "utf-8").decode("unicode_escape")
                COLORS[key] = color

        config_file = os.path.join(config_dir, "clusters.ini")

        if os.path.isfile(config_file):
            parser = configparser.ConfigParser()
            parser.read(config_file)

            for section in parser.sections():
                config_file = parser[section]["configfile"]
                self._clusters[section] = Cluster(
                    config_file, self._read_kube_config(config_file)
                )

            if self._clusters:
                self._selected_cluster_name = next(iter(self._clusters.keys()))

    def _read_kube_config(self, config_file_path):
        with open(config_file_path, "r") as f:
            loader = KubeConfigLoader(config_dict=yaml.safe_load(f))
            config = client.Configuration()
            loader.load_and_set(config)
            return config

    def _get_api_client(self, cluster_name):
        cluster = self._clusters[cluster_name]
        if not cluster.api_client:
            cluster.api_client = client.ApiClient(cluster["config"])
        return cluster.api_client


if __name__ == "__main__":
    mgr = MainApp("/home/carlos/.kubemgr")
    ansi.cursor_off()
    mgr.main_loop()
    ansi.cursor_on()
