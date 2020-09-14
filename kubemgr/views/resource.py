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
        self.refresh()

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

    def fetch_data(self):
        if self.enabled:
            try:
                result = self._cluster.do_get(
                    self._api_group, self._resource_kind, namespace=self._namespace
                )
                return json.loads(result.decode())["items"]
            except Exception as e:
                logging.error(e)
        return []


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
        if self._model.enabled and input_key in self._key_handlers:
            self._key_handlers[input_key](self)
        else:
            super().on_key_press(input_key)
