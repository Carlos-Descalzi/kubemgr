import json
import logging
import os
import threading

import yaml
from cdtui import ListenerHandler
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.config.kube_config import KubeConfigLoader
from typing import Dict, Any, Optional

_logger = logging.getLogger(__name__)


class UnknownResource(Exception):
    def __init__(self, api_group, name):
        self.api_group = api_group
        self.name = name

    def __str__(self):
        return f"Unknown resource {self.api_group} {self.name}"

class ServiceError(Exception):

    def __init__(self, status_code: int, response: str):
        self._status_code = status_code
        self._response = response

    def __str__(self):
        return "Service error: {self.status_code} - {self.response}"


class Cluster:
    @classmethod
    def from_config(cls, application, name, config):

        config_file = config["configfile"]
        timeout = int(config.get("timeout", 5))

        return Cluster(application, name, config_file, timeout)

    def __init__(self, application, name, config_file, request_timeout=5):
        self._application = application
        self._config_loader = None
        self._config_name = name
        self._name = None
        self.config_file = config_file
        self._request_timeout = request_timeout
        self.config = None
        self._api_client = None
        self._connection_error = None
        self._resources = {}
        self._connection_thread = None
        self._on_connect = ListenerHandler(self)
        self._on_error = ListenerHandler(self)

    @property
    def name(self):
        return self.config_file

    def __str__(self):
        return f"Cluster connection {self.name}"

    def __repr__(self):
        return str(self)

    @property
    def on_connect(self):
        return self._on_connect

    @property
    def on_error(self):
        return self._on_error

    @property
    def connected(self) -> bool:
        return self._api_client is not None

    @property
    def connecting(self):
        return self._connection_thread is not None and self._connection_thread.is_alive() and self._api_client is None

    @property
    def api_client(self) -> client.ApiClient:
        return self._api_client

    def disconnect(self):
        if self.connected:
            self._api_client.close()
            self._resources = {}

    @property
    def connection_error(self):
        return self._connection_error

    def connect(self):
        if not self.connecting:
            self._connection_thread = threading.Thread(target=self._do_connect, daemon=True)
            self._connection_thread.start()

    def _do_connect(self):
        try:
            self._create_connection()
            self._on_connect()
        except Exception as e:
            _logger.exception("Error connecting to cluster")
            self._connection_error = e
            self._on_error(e)

    def build_path_for_resource(self, api_group, resource_kind, namespace=None, name=None):
        resource = self.get_resource(api_group, resource_kind)

        return self.build_path(api_group, resource, name=name, namespace=namespace)

    def build_path(self, api_group, resource, name=None, namespace=None, verb=None):
        resource_name = resource["name"]
        namespaced = resource["namespaced"]
        path = "/"
        if api_group != "api/v1":  # TODO Fix
            if api_group == "v1":
                path += "api/"
            else:
                path += "apis/"
        path += api_group
        if namespaced and namespace:
            path += f"/namespaces/{namespace}"
        path += f"/{resource_name}"

        if name:
            path += f"/{name}"

        if verb:
            path += f"/{verb}"

        return path

    def get_contexts(self):
        if self._config_loader:
            return self._config_loader.list_contexts()
        return []

    def get_active_context(self):
        return self._config_loader.current_context

    def _create_connection(self):

        self._config_loader = self._create_config_loader(self.config_file)
        self._name = self._config_loader.current_context["name"]

        self.config = self._read_kube_config(self._config_loader)
        _logger.info(f"Config: {self.config.__dict__}")
        api_client = client.ApiClient(self.config)
        self._api_client = api_client
        apis = client.ApisApi(api_client).get_api_versions()
        for api_group in apis.groups:
            for version in api_group.versions:
                _logger.debug(f"Api group version {version.group_version}")
                api_group_version = version.group_version
                try:
                    self._resources[api_group_version] = self._get_resources(api_client, f"/apis/{api_group_version}/")
                except ApiException:
                    _logger.info(f"No info for api group {api_group_version}")

        self._resources["api/v1"] = self._get_resources(api_client, "/api/v1/")
        self._resources["v1"] = self._get_resources(api_client, "/api/v1/")  # TODO Fix this

    def _get_resources(self, api_client, path):
        _logger.info(f"get resource {path}")
        try:
            data = self.do_simple_get(path)
            return json.loads(data.decode())["resources"]
        except Exception:
            _logger.exception(f"Unable to get resource {path}")
            return {}

    def _read_kube_config(self, config_loader: KubeConfigLoader) -> client.Configuration:
        config = client.Configuration()
        config_loader.load_and_set(config)
        return config

    def _create_config_loader(self, config_file: str) -> KubeConfigLoader:
        base_path = os.path.dirname(config_file)
        with open(config_file, "r") as f:
            return KubeConfigLoader(config_dict=yaml.safe_load(f), config_base_path=base_path)

    def get_resource(self, api_group, resource_name) -> Dict[str, Any]:
        found = list(filter(lambda x: x["kind"] == resource_name, self._resources.get(api_group, [])))
        if found:
            return found[0]

        raise UnknownResource(api_group, resource_name)

    def do_simple_get(self, path) -> bytes:
        response, status, _ = self.api_client.call_api(
            path, "GET", _preload_content=False, **self._request_args()
        )

        if status != 200:
            raise ServiceError(status, response.data)

        return response.data

    def do_get(self, api_group, resource_kind, name=None, namespace=None, verb=None) -> bytes:
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(api_group, resource, name=name, namespace=namespace, verb=verb)
        return self.do_simple_get(path)

    def do_post(self, api_group, resource_kind, name=None, namespace=None, body=None) -> None:
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(api_group, resource, name=name, namespace=namespace)
        response, status, _ = self._api_client.call_api(path, "POST", body=body, **self._request_args())

        if status not in [200, 201]:
            raise ServiceError(status, response)

    def do_delete(self, api_group, resource_kind, name, namespace=None) -> None:
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(api_group, resource, name=name, namespace=namespace)
        response, status, _ = self.api_client.call_api(path, "DELETE", **self._request_args())
        if status != 200:
            raise ServiceError(status,response)

    def do_patch(
        self,
        api_group,
        resource_kind,
        name,
        namespace=None,
        body=None,
        content_type=None,
    ) -> None:
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(api_group, resource, name=name, namespace=namespace)

        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        response, status, _ = self.api_client.call_api(
            path, "PATCH", body=body, header_params=headers, **self._request_args()
        )

        if status not in [200, 201]:
            raise ServiceError(status, response)

    def _request_args(self) -> Dict[str, Any]:
        return dict(auth_settings=["BearerToken"], _request_timeout=self._request_timeout)
