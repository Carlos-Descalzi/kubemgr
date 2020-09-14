from kubernetes import client
from kubernetes.config.kube_config import KubeConfigLoader
import logging
import traceback
from kubernetes.client.rest import ApiException
import json
import yaml
import threading
from .util.ui.listener import ListenerHandler


class Cluster:
    @classmethod
    def from_config(cls, application, name, config):

        config_file = config["configfile"]
        timeout = int(config.get("timeout", 5))

        return Cluster(application, name, config_file, timeout)

    def __init__(self, application, name, config_file, request_timeout=5):
        self._application = application
        self.name = name
        self.config_file = config_file
        self._request_timeout = request_timeout
        self.config = None
        self._api_client = None
        self._connection_error = None
        self._resources = {}
        self._connection_thread = None
        self._on_connect= ListenerHandler(self)
        self._on_error= ListenerHandler(self)

    @property
    def on_connect(self):
        return self._on_connect

    @property
    def on_error(self):
        return self._on_error

    @property
    def connected(self):
        return self._api_client is not None

    @property
    def connecting(self):
        return (
            self._connection_thread is not None
            and self._connection_thread.is_alive()
            and self._api_client is None
        )

    @property
    def api_client(self):
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
            self._connection_thread = threading.Thread(
                target=self._do_connect, daemon=True
            )
            self._connection_thread.start()

    def _do_connect(self):
        try:
            self._create_connection()
            self._on_connect()
        except Exception as e:
            logging.error(f"Error connecting to cluster {e}")
            self._connection_error = e
            self._on_error(e)

    def build_path_for_resource(
        self, api_group, resource_kind, namespace=None, name=None
    ):
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

    def _create_connection(self):
        self.config = self._read_kube_config(self.config_file)
        api_client = client.ApiClient(self.config)
        apis = client.ApisApi(api_client).get_api_versions()
        for api_group in apis.groups:
            for version in api_group.versions:
                api_group_version = version.group_version
                try:
                    self._resources[api_group_version] = self._get_resources(
                        api_client, f"/apis/{api_group_version}/"
                    )
                except ApiException:
                    logging.info(f"No info for api group {api_group_version}")

        self._resources["api/v1"] = self._get_resources(api_client, "/api/v1/")
        self._resources["v1"] = self._get_resources(
            api_client, "/api/v1/"
        )  # TODO Fix this
        self._api_client = api_client

    def _get_resources(self, api_client, path):
        response, status, _ = api_client.call_api(
            path, "GET", _preload_content=False, _request_timeout=self._request_timeout
        )
        return json.loads(response.data.decode())["resources"]

    def _read_kube_config(self, config_file_path):
        with open(config_file_path, "r") as f:
            loader = KubeConfigLoader(config_dict=yaml.safe_load(f))
            config = client.Configuration()
            loader.load_and_set(config)
            return config

    def get_resource(self, api_group, resource_name):
        found = list(
            filter(lambda x: x["kind"] == resource_name, self._resources[api_group])
        )
        return found[0] if found else None

    def do_simple_get(self, path):
        response, status, _ = self.api_client.call_api(
            path, "GET", _preload_content=False, _request_timeout=self._request_timeout
        )

        if status != 200:
            raise Exception(f"{status} - {response.data}")

        return response.data

    def do_get(self, api_group, resource_kind, name=None, namespace=None, verb=None):
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(
            api_group, resource, name=name, namespace=namespace, verb=verb
        )
        return self.do_simple_get(path)

    def do_post(self, api_group, resource_kind, name=None, namespace=None, body=None):
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(api_group, resource, name=name, namespace=namespace)
        response, status, _ = self._api_client.call_api(path, "POST", body=body)

        if status not in [200,201]:
            raise Exception(f"{status} - {response}")

    def do_delete(self, api_group, resource_kind, name, namespace=None):
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(api_group, resource, name=name, namespace=namespace)
        response, status, _ = self.api_client.call_api(path, "DELETE")
        if status != 200:
            raise Exception(f"{status} - {response}")

    def do_patch(
        self,
        api_group,
        resource_kind,
        name,
        namespace=None,
        body=None,
        content_type=None,
    ):
        resource = self.get_resource(api_group, resource_kind)
        path = self.build_path(api_group, resource, name=name, namespace=namespace)

        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        response, status, _ = self.api_client.call_api(
            path, "PATCH", body=body, header_params=headers
        )

        if status != 200:
            raise Exception(f"{status} - {response.data}")

        return response.data
