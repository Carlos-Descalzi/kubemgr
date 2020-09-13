from kubemgr.util.ui import Rect, TextView, ListView
from kubernetes import client
from ..util import ansi
from .util import AsyncListModel
from .format import Formatter
from abc import ABCMeta, abstractclassmethod
import yaml
import tempfile
import subprocess
import logging
import json
import traceback
import io

_DEFAULT_PATH_PREFIX = "api/v1"


class ResourceListModel(AsyncListModel):
    def __init__(self, application, resource_kind, api_group=_DEFAULT_PATH_PREFIX):
        super().__init__(application)
        self._resource_kind = resource_kind
        self._api_group = api_group
        self._cluster = None
        self._namespace = None

    @property
    def api_group(self):
        return self._api_group

    @property
    def resource_kind(self):
        return self._resource_kind

    def set_cluster(self, cluster):
        self._cluster = cluster

    def get_cluster(self):
        return self._cluster

    cluster = property(get_cluster, set_cluster)

    @property
    def enabled(self):
        return self._cluster is not None and self._cluster.connected

    def set_namespace(self, namespace):
        self._namespace = namespace

    def get_namespace(self):
        return self._namespace

    namespace = property(get_namespace, set_namespace)

    """
    def get_api_client_and_resource(self):
        cluster = self._application.selected_cluster
        if cluster and cluster.api_client:
            try:
                return (
                    cluster.api_client,
                    cluster.get_resource(self._api_group, self._resource_kind),
                )
            except Exception as e:
                logging.error(
                    (
                        f"unable to get client, resource for {self._api_group}, {self._resource_kind} - {e}"
                        + traceback.format_exc()
                    )
                )
        return None, None
    """

    def _build_path(self, resource, name=None, namespace=None):
        cluster = self._application.selected_cluster
        return cluster.build_path(self._api_group, resource, name, namespace)

    def update(self, item, contents):

        if self.enabled:
            api_client = self._cluster.api_client
            resource = self._cluster.get_resource(self._api_group, self._resource_kind)
            path = self._build_path(
                resource, item["metadata"]["name"], item["metadata"]["namespace"]
            )
            logging.info(path)
            logging.info(contents)
            response, status, _ = api_client.call_api(
                path,
                "PATCH",
                body=contents,
                header_params={"Content-Type": "application/json-patch+json"},
            )
            logging.info(f"{response},{status}")

    def fetch_data(self):
        self._items = []
        if self.enabled:
            api_client = self._cluster.api_client
            resource = self._cluster.get_resource(self._api_group, self._resource_kind)

            if api_client:
                path = self._build_path(resource, namespace=self.namespace)
                result = api_client.call_api(path, "GET", _preload_content=False)
                response, status_code, _ = result
                if status_code == 200:
                    self._items = json.loads(response.data.decode())["items"]
                else:
                    logging.error("Unable to get data: {status_code} - {response.data}")


class ResourceListView(ListView):
    def __init__(self, rect=None, model=None, selectable=False):
        super().__init__(rect, model, selectable)
        self._key_handlers = {}
        self._formatter = None

    def set_item_format(self, item_format):
        self._formatter = Formatter(item_format) if item_format else None

    def set_key_handler(self, key, handler):
        self._key_handlers[key] = handler

    def render_item(self, item, current, selected):
        width = self._rect.width
        buff = ansi.begin()

        if self.focused and current:
            buff.underline()

        return str(buff.write(self.do_render_item(item, width)).reset())

    def do_render_item(self, item, width):
        if self._formatter:
            return self._formatter.format(item, width)
        return item["metadata"]["name"]

    def on_key_press(self, input_key):
        if self._model.enabled:
            if input_key == ord("e"):
                self._edit_selected()
            elif input_key in self._key_handlers:
                self._key_handlers[input_key](self)
            else:
                super().on_key_press(input_key)
        else:
            super().on_key_press(input_key)

    def _edit_selected(self):
        current = self.current_item
        if current:
            self._edit_item(current)

    def _edit_item(self, item):
        contents = yaml.dump(item, Dumper=yaml.SafeDumper)
        new_contents = self._application.edit_file(contents, "yaml")
        if new_contents:
            new_yaml = yaml.load(io.StringIO(new_contents), Loader=yaml.SafeLoader)
            json_content = json.dumps(new_yaml)
            self._model.update(item, json_content)
