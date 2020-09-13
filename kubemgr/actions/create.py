import logging
from kubemgr.util.ui import FileChooser, Rect
import yaml
import traceback

class CreateResource:
    def __init__(self, app):
        self._app = app

    def __call__(self, *_):
        chooser = FileChooser(
            rect=Rect(width=70, height=20), file_filter=lambda p, f: ".yaml" in f
        )
        chooser.set_on_file_selected(self._file_selected)
        self.app.open_popup(chooser)

    def _file_selected(self, path):
        self._app.close_popup()
        self._create_resource(path)

    def _create_resource(self, yaml_file_path):
        try:

            with open(yaml_file_path, "r") as f:
                resources = yaml.full_load_all(f)

                for resource in resources:
                    cluster = self.app.selected_cluster
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
            logging.error(f"{e} {traceback.format_exc()}")
