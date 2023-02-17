import json
import logging

from typing import Optional
from cdtui import ListView
from jinja2 import Template

from kubemgr.cluster import UnknownResource, Cluster

from .util import BASE_JINJA_CONTEXT, AsyncListModel

_DEFAULT_PATH_PREFIX = "api/v1"

_logger = logging.getLogger(__name__)


class Filter:
    def __init__(self, filter_string):
        self._filter_string = filter_string
        self._template = Template(filter_string)

    @property
    def filter_string(self):
        return self._filter_string

    def __call__(self, item):
        ctx = dict(BASE_JINJA_CONTEXT)
        ctx["item"] = item
        result = self._template.render(ctx).strip()
        return result == "True"


class ResourceListModel(AsyncListModel):
    def __init__(self, application, resource_kind, api_group=_DEFAULT_PATH_PREFIX):
        super().__init__(application)
        self._resource_kind = resource_kind
        self._api_group = api_group
        self._cluster = None
        self._namespace = None
        self._global_filter = None
        self._filter = None

    def set_global_filter(self, global_filter):
        self._global_filter = global_filter
        self.refresh()

    def get_global_filter(self):
        return self._global_filter

    global_filter = property(get_global_filter, set_global_filter)

    def set_filter(self, filter):
        self._filter = filter
        self.refresh()

    def get_filter(self):
        return self._filter

    filter = property(get_filter, set_filter)

    @property
    def api_group(self):
        return self._api_group

    @property
    def resource_kind(self):
        return self._resource_kind

    def set_cluster(self, cluster: Optional[Cluster]):
        self._cluster = cluster
        self.refresh()

    def get_cluster(self) -> Optional[Cluster]:
        return self._cluster

    cluster = property(get_cluster, set_cluster)

    @property
    def enabled(self) -> bool:
        return self._cluster is not None and self._cluster.connected

    def set_namespace(self, namespace):
        self._namespace = namespace

    def get_namespace(self):
        return self._namespace

    namespace = property(get_namespace, set_namespace)

    def fetch_data(self):
        if self.enabled:
            try:
                result = self._cluster.do_get(self._api_group, self._resource_kind, namespace=self._namespace)
                return self._filter_data(json.loads(result.decode())["items"])
            except UnknownResource:
                _logger.info(f"Unknown resource {self._api_group} {self._resource_kind} ns:{self._namespace}")
            except Exception:
                _logger.exception("Error fetching data")
        return []

    def _filter_data(self, items):
        if self._global_filter:
            _logger.debug("Applying global filter")
            items = filter(self._global_filter, items)
        if self._filter:
            _logger.debug("Applying filter")
            items = filter(self._filter, items)
        return list(items)


class ResourceListView(ListView):
    def __init__(self, rect=None, model=None, selectable=False):
        super().__init__(rect, model, selectable)
        self._key_handlers = {}
        self._formatter = None

    def set_key_handler(self, key, handler):
        self._key_handlers[key] = handler

    def on_key_press(self, input_key):
        if self._model.enabled and input_key in self._key_handlers:
            self._key_handlers[input_key](self)
        else:
            super().on_key_press(input_key)
