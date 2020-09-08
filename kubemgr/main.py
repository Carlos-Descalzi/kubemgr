import logging

logging.basicConfig(filename="kubemgr.log", format="%(message)s", level=logging.INFO)
import os
import time
import configparser
import yaml
from .util import ansi
from .util.ui import COLORS, Application, Rect, TitledView, TabbedView, TextView
from .util.executor import TaskExecutor
from .views.clusters import ClusterListView, ClustersListModel
from .views.namespaces import NamespacesListModel, NamespacesListView
from .views.resource import ResourceListModel, ResourceListView
from .cluster import Cluster
from kubernetes import client, config
from kubernetes.client import configuration
from kubernetes.config.kube_config import KubeConfigLoader
from abc import ABCMeta, abstractmethod
import tty
import sys
import atexit
from collections import defaultdict
from .texts import CLUSTERS_CONFIG_TEMPLATE, KUBEMGR_DEFAUL_CONFIG_TEMPLATE, HELP_CONTENTS

class TabInfo:
    def __init__(self, title, model, view):
        self.title = title
        self.model = model
        self.view = view

class MainApp(Application):
    def __init__(self, config_dir):
        super().__init__()
        self._task_executor = TaskExecutor()
        self._clusters = {}
        self._config = {}
        self._selected_cluster_name = None
        self._read_configuration(config_dir)

        self._clusters_model = ClustersListModel(self)
        self._clusters_view = ClusterListView(
            model=self._clusters_model, selectable=True
        )
        self._nodes_model = ResourceListModel(self,'Node')
        self._nodes_view = ResourceListView(model=self._nodes_model)
        self._nodes_view.set_key_handler(ord('l'),self._show_labels)

        self._namespaces_model = NamespacesListModel(self)
        self._namespaces_view = NamespacesListView(
            model=self._namespaces_model, selectable=True
        )
        self._namespaces_view.set_on_select(self._on_namespace_selected)

        self._pods_model = ResourceListModel(self,'Pod')
        self._pods_view = ResourceListView(model=self._pods_model)
        self._pods_view.set_key_handler(ord('l'),self._show_pod_logs)
        
        self._custom_tabs = []

        tabs_config = self.get_tabs_config()

        for tabname, config in tabs_config.items():
            if tabname != 'podstab':
                model = ResourceListModel(self,config['kind'],config['group_version'])
                view = ResourceListView(model=model)
                view.set_item_format(config.get('format'))
                self._custom_tabs.append(TabInfo(config['title'],model, view))
            else:
                self._pods_view.set_item_format(config.get('format'))

        max_height, max_width = ansi.terminal_size()

        h_divider_pos = int(max_width * 0.25)

        v_clusters_height = int(max_height * 0.3)
        v_nodes_start = v_clusters_height + 1
        v_nodes_height = int(max_height * 0.3)
        v_namespaces_start = v_nodes_start + v_nodes_height + 1
        v_namespaces_height = max_height - v_namespaces_start - 1

        tab_width = max_width - (h_divider_pos + 1)

        self.add_component(
            TitledView(
                rect=Rect(1, 1, h_divider_pos, v_clusters_height),
                title="Clusters",
                inner=self._clusters_view,
            )
        )
        self.add_component(
            TitledView(
                rect=Rect(1, v_nodes_start, h_divider_pos, v_nodes_height),
                title="Nodes",
                inner=self._nodes_view,
            )
        )
        self.add_component(
            TitledView(
                rect=Rect(1, v_namespaces_start, h_divider_pos, v_namespaces_height),
                title="Namespaces",
                inner=self._namespaces_view,
            )
        )
        tabs = TabbedView(rect=Rect(h_divider_pos + 1, 1, tab_width, 30))

        tabs.add_tab("Pods", self._pods_view)
        for tab in self._custom_tabs:
            tabs.add_tab(tab.title, tab.view)

        self.add_component(tabs)
        self._task_executor.start()


    def _on_namespace_selected(self, item):
        ns_name = item.name if item.selected else None
        self._set_namespace_filter(ns_name)

    def _set_namespace_filter(self, namespace):
        models = [self._pods_model] + [tab.model for tab in self._custom_tabs]
        for model in models:
            model.set_namespace(namespace)
        self._update_view()

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

    def get_general_config(self):
        return self._config['general']

    def get_tabs_config(self):
        config = defaultdict(dict)
        tabs_config = self._config['tabs']
        for key in tabs_config:
            tabname, entry = key.split('.')
            config[tabname][entry] = tabs_config[key]
        return config

    def show_help(self):
        self.show_text_popup(HELP_CONTENTS.split("\n"))

    def _show_pod_logs(self):
        current = self._pods_view.current_item

        name = current['metadata']['name']
        namespace = current['metadata']['namespace']

        cluster = self.selected_cluster

        if cluster:
            api = cluster.api_client
            logs, _,_ = api.call_api(
                f'/api/v1/namespaces/{namespace}/pods/{name}/log', 
                'GET',
                response_type='str',
                _preload_content=True
            )

        self.show_text_popup(logs.split('\n'))

    def _show_labels(self):
        current = self._nodes_view.current_item
        labels = current['metadata']['labels']
        name = current['metadata']['name']
        labels_text = (
            [f"Labels for node {name}",
            "======================",
            ""] 
            + [f"{k:50} : {v}" for k, v in labels.items()] 
            + [""]
        )
        self.show_text_popup(labels_text)

    def show_text_popup(self, text):
        max_height, max_width = ansi.terminal_size()

        popup_width = int(max_width * 0.75)
        popup_height = int(max_height * 0.75)

        rect = Rect(
            int((max_width - popup_width) / 2),
            int((max_height - popup_height) / 2),
            popup_width,
            popup_height,
        )
        text_view = TextView(rect=rect, text=text)
        self.open_popup(text_view)

    def _read_configuration(self, config_dir):
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)

        self._read_general_config(config_dir)
        self._read_colors_config(config_dir)
        self._read_clusters_config(config_dir)

    def _read_general_config(self, config_dir):
        general_config_file = os.path.join(config_dir, "kubemgr.ini")

        if not os.path.isfile(general_config_file):
            with open(general_config_file,'w') as f:
                f.write(KUBEMGR_DEFAUL_CONFIG_TEMPLATE)

        parser = configparser.ConfigParser()
        parser.read(general_config_file)
        self._config = parser

    def _read_colors_config(self, config_dir):
        colors_config_file = os.path.join(config_dir, "colors.ini")

        if os.path.isfile(colors_config_file):
            parser = configparser.ConfigParser(default_section="colors")
            parser.read(colors_config_file)

            for key in parser["colors"]:
                color_val = parser["colors"][key]
                color = bytes(color_val, "utf-8").decode("unicode_escape")
                COLORS[key] = color
        else:
            with open(colors_config_file, "w") as f:
                f.write("[colors]\n")
                for k, v in COLORS.items():
                    v = v.encode("unicode_escape").decode("utf-8")
                    f.write(f"{k}={v}\n")

    def _read_clusters_config(self, config_dir):
        clusters_config_file = os.path.join(config_dir, "clusters.ini")

        if os.path.isfile(clusters_config_file):
            parser = configparser.ConfigParser()
            parser.read(clusters_config_file)

            for section in parser.sections():
                config_file = parser[section]["configfile"]
                self._clusters[section] = Cluster(
                    config_file, self._read_kube_config(config_file)
                )

            if self._clusters:
                self._selected_cluster_name = next(iter(self._clusters.keys()))
        else:
            with open(config_file, "w") as f:
                f.write(CLUSTERS_CONFIG_TEMPLATE)

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
