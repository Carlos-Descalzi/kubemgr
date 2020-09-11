import logging

logging.basicConfig(filename="kubemgr.log", format="%(message)s", level=logging.INFO)
import os
import tty
import sys
import time
import yaml
import atexit
import tempfile
import subprocess
import configparser
from kubernetes import client, config
from kubernetes.client import configuration
from collections import defaultdict
from abc import ABCMeta, abstractmethod
from .util import ansi
from .util.ui import (
    COLORS,
    Application,
    Rect,
    TitledView,
    TabbedView,
    TextView,
    FileChooser,
    QuestionDialog,
)
from .util.executor import TaskExecutor
from .views.clusters import ClusterListView, ClustersListModel
from .views.namespaces import NamespacesListModel, NamespacesListView
from .views.resource import ResourceListModel, ResourceListView
from .cluster import Cluster
from .texts import (
    CLUSTERS_CONFIG_TEMPLATE,
    KUBEMGR_DEFAUL_CONFIG_TEMPLATE,
    HELP_CONTENTS,
)


class TabInfo:
    def __init__(self, title, model, view):
        self.title = title
        self.model = model
        self.view = view


class MainApp(Application):
    def __init__(self, config_dir):
        super().__init__()
        self._task_executor = TaskExecutor()
        self._clusters = []
        self._config = {}
        first_time = self._read_configuration(config_dir)

        self._clusters_model = ClustersListModel(self)
        self._clusters_view = ClusterListView(
            model=self._clusters_model, selectable=True
        )
        self._clusters_view.set_on_select(self.set_selected_cluster)
        self._nodes_model = ResourceListModel(self, "Node")
        self._nodes_view = ResourceListView(model=self._nodes_model)
        self._nodes_view.set_key_handler(ord("l"), self._show_labels)

        self._namespaces_model = NamespacesListModel(self)
        self._namespaces_view = NamespacesListView(
            model=self._namespaces_model, selectable=True
        )
        self._namespaces_view.set_on_select(self._on_namespace_selected)

        self._pods_model = ResourceListModel(self, "Pod")
        self._pods_view = ResourceListView(model=self._pods_model)
        self._pods_view.set_key_handler(ord("l"), self._show_pod_logs)

        self._custom_tabs = []

        tabs_config = self.get_tabs_config()

        for tabname, config in tabs_config.items():
            if tabname != "podstab":
                model = ResourceListModel(self, config["kind"], config["group_version"])
                view = ResourceListView(model=model)
                view.set_item_format(config.get("format"))
                self._custom_tabs.append(TabInfo(config["title"], model, view))
            else:
                self._pods_view.set_item_format(config.get("format"))

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

        if self._clusters:
            self._clusters_view.set_selected_index(0)# set_selected_cluster(self._clusters[0])

    def _on_finish(self):
        self._task_executor.finish()

    def on_key_press(self, input_key):
        if input_key == ord("c"):
            self._load_file()
            return True

        return False

    def _load_file(self):
        chooser = FileChooser(
            rect=Rect(width=70, height=20), file_filter=lambda p, f: ".yaml" in f
        )

        def file_selected(path):
            self.close_popup()
            self._create_resource(path)

        chooser.set_on_file_selected(file_selected)
        self.open_popup(chooser)

    def get_selected_cluster(self):
        return self._clusters_view.get_selected_item()

    def set_selected_cluster(self, cluster):
        models = [self._nodes_model, self._namespaces_model, self._pods_model] + [
            tab.model for tab in self._custom_tabs
        ]
        for model in models:
            model.set_cluster(cluster)

    selected_cluster = property(get_selected_cluster, set_selected_cluster)

    def _on_namespace_selected(self, item):
        ns_name = item.name if item.selected else None
        logging.info(f"Namespace filter: {ns_name}")
        self._set_namespace_filter(ns_name)

    def _set_namespace_filter(self, namespace):
        models = [self._pods_model] + [tab.model for tab in self._custom_tabs]
        for model in models:
            logging.info(f"Setting filter to {model}")
            model.namespace = namespace
        self._update_view()

    def add_task(self, task, loop=True):
        self._task_executor.add_task(task, loop)

    @property
    def clusters(self):
        return self._clusters

    def get_general_config(self):
        return self._config["general"]

    def get_tabs_config(self):
        config = defaultdict(dict)
        tabs_config = self._config["tabs"]
        for key in tabs_config:
            tabname, entry = key.split(".")
            config[tabname][entry] = tabs_config[key]
        return config

    def show_help(self):
        self.show_text_popup(HELP_CONTENTS.split("\n"))

    def _show_pod_logs(self):
        current = self._pods_view.current_item

        name = current["metadata"]["name"]
        namespace = current["metadata"]["namespace"]

        cluster = self.get_selected_cluster()

        if cluster:
            api = cluster.api_client
            logs, _, _ = api.call_api(
                f"/api/v1/namespaces/{namespace}/pods/{name}/log",
                "GET",
                response_type="str",
                _preload_content=True,
            )

        self.show_file(logs, "log")

    def _create_resource(self, yaml_file_path):
        try:
            from yaml import SafeLoader

            with open(yaml_file_path, "r") as f:
                resources = yaml.full_load_all(f)

                for resource in resources:
                    cluster = self.selected_cluster
                    api_client = cluster.api_client
                    path = cluster.build_path_for_resource(
                        resource["apiVersion"],
                        resource["kind"],
                        resource["metadata"].get("namespace"),
                        None,
                    )
                    logging.info(f"Path: {path}")
                    response = api_client.call_api(path, "POST", body=resource)
                    logging.info(response)
        except Exception as e:
            import traceback

            logging.error(f"{e} {traceback.format_exc()}")

    def _show_labels(self):
        current = self._nodes_view.current_item
        labels = current["metadata"]["labels"]
        name = current["metadata"]["name"]
        labels_text = (
            [f"Labels for node {name}", "======================", ""]
            + [f"{k:50} : {v}" for k, v in labels.items()]
            + [""]
        )
        self.show_text_popup(labels_text)

    def show_question_dialog(self, title, message, options):
        def _wrap_op(f):
            def call():
                f()
                self.close_popup()

            return call

        options = [(k, l, _wrap_op(f)) for k, l, f in options]
        dialog = QuestionDialog(title, message, options)
        self.open_popup(dialog)

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

    def show_file(self, text, format_hint=None):
        viewer = self.get_general_config().get("viewer")

        if viewer:
            tf = self._make_tempfile(text, format_hint)
            subprocess.run([viewer, tf.name])
            self.refresh()
        else:
            self.show_text_popup(text.split("\n"))

    def edit_file(self, text, format_hint=None):
        editor = self.get_general_config().get("editor")
        if editor:
            tf = self._make_tempfile(text, format_hint)
            result = subprocess.run([editor, tf.name])
            self.refresh()
            if result.returncode == 0:
                tf.seek(0)
                new_text = tf.read()
                if new_text != text:
                    return new_text
        return None

    def _make_tempfile(self, text, format_hint=None):
        suffix = f".{format_hint}" if format_hint else None
        tf = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=suffix)
        tf.write(text)
        tf.flush()
        return tf

    def _read_configuration(self, config_dir):

        first_time = not os.path.isdir(config_dir)

        if first_time:
            os.makedirs(config_dir)

        self._read_general_config(config_dir)
        self._read_colors_config(config_dir)
        self._read_clusters_config(config_dir)

        return first_time

    def _read_general_config(self, config_dir):
        general_config_file = os.path.join(config_dir, "kubemgr.ini")

        if not os.path.isfile(general_config_file):
            with open(general_config_file, "w") as f:
                f.write(KUBEMGR_DEFAUL_CONFIG_TEMPLATE)

        parser = configparser.ConfigParser()
        parser.read(general_config_file)
        self._config = parser

    def _read_colors_config(self, config_dir):
        colors_config_file = os.path.join(config_dir, "colors.ini")

        if os.path.isfile(colors_config_file):
            parser = configparser.ConfigParser(default_section="colors")
            parser.read(colors_config_file)

            colors_section = parser["colors"]

            for key in colors_section:
                color_val = colors_section[key]
                color = bytes(color_val, "utf-8").decode("unicode_escape")
                COLORS[key] = color
        else:
            # Write default colors if file not present.
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

            for cluster_name in parser.sections():
                config_file = parser[cluster_name]["configfile"]
                cluster = Cluster(self, cluster_name, config_file)
                self._clusters.append(cluster)
                cluster.connect()

        else:
            # Write a default empty clusters file.
            with open(config_file, "w") as f:
                f.write(CLUSTERS_CONFIG_TEMPLATE)


if __name__ == "__main__":
    mgr = MainApp("/home/carlos/.kubemgr")
    mgr.main_loop()
