import logging
from cdtui import FileChooser, Rect
import yaml
import traceback


class CreateResource:
    def __init__(self, app):
        self._app = app

    def __call__(self, *_):
        if self._app.selected_cluster and self._app.selected_cluster.connected:
            chooser = FileChooser(
                rect=Rect(width=70, height=20), file_filter=lambda p, f: ".yaml" in f
            )
            chooser.on_file_selected.add(self._file_selected)
            self._app.open_popup(chooser)

    def _file_selected(self, source, path):
        self._app.close_popup()
        self._create_resource(path)

    def _create_resource(self, yaml_file_path):
        try:
            cluster = self._app.selected_cluster
            with open(yaml_file_path, "r") as f:
                resources = yaml.full_load_all(f)
                for resource in resources:
                    cluster.do_post(
                        resource["apiVersion"],
                        resource["kind"],
                        namespace=resource["metadata"].get("namespace"),
                        body=resource,
                    )
        except Exception as e:
            self._app.show_error(e)
