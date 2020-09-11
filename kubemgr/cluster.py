from kubernetes import client
from kubernetes.config.kube_config import KubeConfigLoader
import logging
import traceback
from kubernetes.client.rest import ApiException
import json
import yaml


class Cluster:
    def __init__(self, application, name, config_file):
        self._application = application
        self.name = name
        self.config_file = config_file
        self.config = None
        self._api_client = None
        self._connection_error = None
        self._resources = {}

    @property
    def connected(self):
        return self._api_client is not None

    @property
    def api_client(self):
        if not self._api_client:
            self._create_connection()
        return self._api_client

    def disconnect(self):
        if self._api_client:
            self._api_client.close()
            self._resources = {}

    def connect(self, on_success=None, on_error=None):
        def _connect():
            try:
                self._create_connection()
                if on_success:
                    on_success(self)
            except Exception as e:
                logging.error(e)
                if on_error:
                    on_error(self, e)

        self._application.add_task(_connect, False)

    def build_path_for_resource(
        self, api_group, resource_kind, namespace=None, name=None
    ):
        resource = self.get_resource(api_group, resource_kind)
        return self.build_path(api_group, resource, name=name, namespace=namespace)

    def build_path(self, api_group, resource, name=None, namespace=None):
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
        response, status, _ = api_client.call_api(path, "GET", _preload_content=False)
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
