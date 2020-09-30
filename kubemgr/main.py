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
from .util import misc
from cdtui import (
    ansi,
    kbd,
    COLORS,
    Application,
    Rect,
    TitledView,
    TabbedView,
    TextView,
    FileChooser,
    QuestionDialog,
    ListView,
)
from .util.executor import TaskExecutor
from .views.clusters import ClusterListView, ClustersListModel
from .views.namespaces import NamespacesListModel, NamespacesListView
from .views.resource import ResourceListModel, ResourceListView
from .views.renderer import ItemRenderer
from .actions import (
    CreateResource,
    ShowLogs,
    ShowNodeLabels,
    ShowHelp,
    DeleteResource,
    ViewResource,
    EditResource,
)
from .cluster import Cluster
from .texts import (
    CLUSTERS_CONFIG_TEMPLATE,
    CLUSTERS_CONFIG_EMPTY_TEMPLATE,
    KUBEMGR_DEFAUL_CONFIG_TEMPLATE,
    HELP_CONTENTS,
    POD_TEMPLATE,
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
        self._templates = {}
        first_time = self._read_configuration(config_dir)

        self._clusters_model = ClustersListModel(self)
        self._clusters_view = ClusterListView(
            model=self._clusters_model, selectable=True
        )
        self._clusters_view.on_select.add(self.set_selected_cluster)
        self._nodes_model = ResourceListModel(self, "Node")
        self._nodes_view = ResourceListView(model=self._nodes_model)
        self._nodes_view.set_item_renderer(lambda x, y: y["metadata"]["name"])

        self._namespaces_model = NamespacesListModel(self)
        self._namespaces_view = NamespacesListView(model=self._namespaces_model)
        self._namespaces_view.on_select.add(self._on_namespace_selected)

        self._item_renderer = ItemRenderer(self)
        self._pods_model = ResourceListModel(self, "Pod")
        self._pods_view = ResourceListView(model=self._pods_model)
        self._pods_view.set_item_renderer(self._item_renderer)

        self._custom_tabs = []

        tabs_config = self._get_tabs_config()

        for tabname, config in tabs_config.items():
            if tabname != "podstab":
                model = ResourceListModel(self, config["kind"], config["group_version"])
                view = ResourceListView(model=model)
                self._custom_tabs.append(TabInfo(config["title"], model, view))
                view.set_item_renderer(self._item_renderer)

        max_height, max_width = ansi.terminal_size()

        h_divider_pos = int(max_width * 0.25)

        v_clusters_height = int(max_height * 0.3)
        v_nodes_start = v_clusters_height + 1
        v_nodes_height = int(max_height * 0.3)
        v_namespaces_start = v_nodes_start + v_nodes_height + 1
        v_namespaces_height = max_height - v_namespaces_start - 1

        tab_width = max_width - (h_divider_pos + 1)

        clusters_title = TitledView(
            rect=Rect(1, 1, h_divider_pos, v_clusters_height),
            title="Clusters",
            inner=self._clusters_view,
        )

        self.add_component(clusters_title)
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
        tabs = TabbedView(rect=Rect(h_divider_pos + 1, 1, tab_width, max_height))

        tabs.add_tab("Pods", self._pods_view)
        for tab in self._custom_tabs:
            tabs.add_tab(tab.title, tab.view)

        self.add_component(tabs)

        delete_action = DeleteResource(self)
        view_action = ViewResource(self)
        edit_action = EditResource(self)
        help_action = ShowHelp(self)

        self.set_key_handler(kbd.keystroke_from_str("h"), help_action)
        self.set_key_handler(kbd.keystroke_from_str("c"), CreateResource(self))
        self._pods_view.set_key_handler(kbd.keystroke_from_str("l"), ShowLogs(self))
        self._nodes_view.set_key_handler(
            kbd.keystroke_from_str("l"), ShowNodeLabels(self)
        )

        resource_views = [self._pods_view, self._nodes_view, self._namespaces_view] + [
            tab.view for tab in self._custom_tabs
        ]

        for view in resource_views:
            view.set_key_handler(kbd.keystroke_from_str("d"), delete_action)
            view.set_key_handler(kbd.keystroke_from_str("v"), view_action)
            view.set_key_handler(kbd.keystroke_from_str("e"), edit_action)

        self._task_executor.start()

        self._clusters_model.set_clusters(self._clusters)
        if self._clusters:
            self._clusters_view.set_selected_index(0)

        self.set_focused_view(clusters_title)

        if first_time:
            help_action()

    def get_selected_cluster(self):
        return self._clusters_view.get_selected_item()

    def set_selected_cluster(self, source, cluster):

        if cluster.connection_error:
            self.show_error(cluster.connection_error)
        else:
            models = [self._nodes_model, self._namespaces_model, self._pods_model] + [
                tab.model for tab in self._custom_tabs
            ]
            for model in models:
                model.set_cluster(cluster)

    selected_cluster = property(get_selected_cluster, set_selected_cluster)

    def show_error(self, error):
        logging.error(error)
        error_str = self._format_error(error)
        self.show_text_popup(error_str)

    @property
    def clusters(self):
        return self._clusters

    def add_task(self, task, loop=True):
        self._task_executor.add_task(task, loop)

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
            tf = misc.make_tempfile(text, format_hint)
            subprocess.run([viewer, tf.name])
            self.refresh()
        else:
            self.show_text_popup(text)

    def edit_file(self, text, format_hint=None):
        editor = self.get_general_config().get("editor")
        if editor:
            tf = misc.make_tempfile(text, format_hint)
            result = subprocess.run([editor, tf.name])
            self.refresh()
            if result.returncode == 0:
                tf.seek(0)
                new_text = tf.read()
                if new_text != text:
                    return new_text
        return None

    def _format_error(self, error):
        error_str = misc.word_wrap_text(str(error), 70)
        return f"An error has occurred:\n\n{error_str}"

    def _on_finish(self):
        self._task_executor.finish()

    def _on_namespace_selected(self, source, item):
        namespace = item.name if item.selected else None
        models = [self._pods_model] + [tab.model for tab in self._custom_tabs]
        for model in models:
            model.namespace = namespace
        self._update_view()

    def get_general_config(self):
        return self._config["general"]

    def _get_tabs_config(self):
        config = defaultdict(dict)
        tabs_config = self._config["tabs"]
        for key in tabs_config:
            tabname, entry = key.split(".")
            config[tabname][entry] = tabs_config[key]
        return config

    def _read_configuration(self, config_dir):

        first_time = not os.path.isdir(config_dir)

        if first_time:
            os.makedirs(config_dir)

        self._read_general_config(config_dir)
        self._read_colors_config(config_dir)
        self._read_clusters_config(config_dir)
        self._read_templates(config_dir)

        return first_time

    def _read_general_config(self, config_dir):
        general_config_file = os.path.join(config_dir, "kubemgr.ini")

        if not os.path.isfile(general_config_file):
            with open(general_config_file, "w") as f:
                f.write(KUBEMGR_DEFAUL_CONFIG_TEMPLATE)

        parser = configparser.ConfigParser()
        parser.read(general_config_file)
        self._config = parser

    def _make_default_cluster_config(self):

        cluster_name = None
        cluster_file = os.environ.get("KUBECONFIG")

        if cluster_file:
            cluster_name = "Default cluster"
        else:
            path = os.path.join(os.environ["HOME"], ".kube", "config")
            if os.path.isfile(path):
                cluster_file = path
                cluster_name = "Local cluster"

        if not (cluster_name or cluster_file):
            return CLUSTERS_CONFIG_EMPTY_TEMPLATE

        return CLUSTERS_CONFIG_TEMPLATE.format(
            cluster_name=cluster_name, cluster_file=cluster_file
        )

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

        if not os.path.isfile(clusters_config_file):
            with open(clusters_config_file, "w") as f:
                f.write(self._make_default_cluster_config())

        parser = configparser.ConfigParser()
        parser.read(clusters_config_file)

        for cluster_name in parser.sections():
            config = parser[cluster_name]
            cluster = Cluster.from_config(self, cluster_name, config)
            self._clusters.append(cluster)
            cluster.connect()

    def _read_templates(self, config_dir):
        templates_dir = os.path.join(config_dir, "templates")

        if not os.path.isdir(templates_dir):
            os.makedirs(templates_dir)
            with open(os.path.join(templates_dir, "Pod.tpl"), "w") as f:
                f.write(POD_TEMPLATE)

        templates = {}
        for fname in os.listdir(templates_dir):
            if fname[-4:] == ".tpl":
                logging.info(fname)
                try:
                    with open(os.path.join(templates_dir, fname), "r") as f:
                        templates[fname.replace(".tpl", "")] = f.read()
                except Exception as e:
                    logging.error(f"Error loading template {fname} - {e}")
        self._templates = templates


def main():
    mgr = MainApp(os.path.join(os.environ["HOME"], ".kubemgr"))
    mgr.main_loop()


if __name__ == "__main__":
    main()
