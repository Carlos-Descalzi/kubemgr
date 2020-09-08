from kubernetes import client
import logging
import traceback
from kubernetes.client.rest import ApiException
import json

class Cluster:
    def __init__(self, config_file, config):
        self.config_file = config_file
        self.config = config
        self._api_client = None
        self._connection_error = None
        self._resources = {}

    @property
    def api_client(self):
        if not self._api_client:
            self._create_connection()
        return self._api_client

    def _create_connection(self):
        try:
            api_client = client.ApiClient(self.config)
            apis = client.ApisApi(api_client).get_api_versions()
            for api_group in apis.groups:
                for version in api_group.versions:
                    api_group_version = version.group_version
                    logging.info(api_group)
                    try:
                        self._resources[api_group_version] = self._get_resources(
                            api_client, 
                            f'/apis/{api_group_version}/'
                        )
                    except ApiException:
                        logging.info(f'No info for api group {api_group_version}')

            self._resources['api/v1'] = self._get_resources(api_client, '/api/v1/')
            self._log_resource_types(self._resources)
            self._api_client = api_client

        except Exception as e:
            logging.error(str(e)+str(traceback.format_exc()))

    def _get_resources(self, api_client, path):
        response, status, _ = api_client.call_api(
            path,
            'GET',
            _preload_content=False
        )
        return json.loads(response.data.decode())['resources']

    def _log_resource_types(self, resources):
        for k,rl in resources.items():
            logging.info(f'{k}:')
            for i in rl:
                logging.info(f"\t{i['name']},{i['kind']}")


    def get_api_group(self, name):
        found = list(
            filter(
                lambda x:x.name == name,
                self._apis
            )
        )
        return found[0] if found else None

    def get_resource(self, api_group,resource_name):
        #logging.info(self._resources[api_group])
        found = list(
            filter(
                lambda x:x['kind'] == resource_name,
                self._resources[api_group]
            )
        )
        return found[0] if found else None

