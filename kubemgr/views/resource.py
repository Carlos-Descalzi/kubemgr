from kubemgr.util.ui import Rect, TextView, ListView
from kubernetes import client
from ..util import ansi
from .util import AsyncListModel
from abc import ABCMeta, abstractclassmethod
import yaml
import tempfile
import subprocess
import logging
import json
import traceback

_DEFAULT_PATH_PREFIX='api/v1'

class ResourceListModel(AsyncListModel):
    def __init__(self, application, resource_name, api_group=_DEFAULT_PATH_PREFIX):
        super().__init__(application)
        self._resource_name = resource_name
        self._api_group = api_group
        self._namespace = None
        
    def set_namespace(self, namespace):
        self._namespace = namespace

    def get_api_client_and_resource(self):
        cluster = self._application.selected_cluster
        if cluster and cluster.api_client:
            try:
                return cluster.api_client, cluster.get_resource(self._api_group, self._resource_name)
            except Exception as e:
                logging.error((
                    f'unable to get client, resource for {self._api_group}, {self._resource_name} - {e}'
                    +traceback.format_exc()))
        return None, None

    def _build_path(self, resource):
        resource_name = resource['name']
        path = '/'
        if self._api_group != _DEFAULT_PATH_PREFIX:
            path+='apis/'
        path += self._api_group
        if self._namespace and resource['namespaced']:
            path+= f'/namespaces/{self._namespace}'
        path+=f'/{resource_name}'

        return path

    def fetch_data(self):
        api_client, resource = self.get_api_client_and_resource()

        if api_client:
            path = self._build_path(resource)
            result = api_client.call_api(
                path,
                'GET',
                _preload_content=False
            )
            response,status_code,_ = result
            if status_code == 200:
                self._items = json.loads(response.data.decode())['items']
            else:
                logging.error('Unable to get data: {status_code} - {response.data}')
        else:
            self._items = []


class ResourceListView(ListView):

    def __init__(self, rect=None, model=None, selectable=False):
        super().__init__(rect, model, selectable)
        self._key_handlers = {}

    def set_key_handler(self, key, handler):
        self._key_handlers[key] = handler

    def render_item(self, item, current, selected):
        width = self._rect.width
        buff = ansi.begin()

        if self.focused and current:
            buff.underline()

        return str(buff.write(self.do_render_item(item, width)).reset())

    def do_render_item(self, item, width):
        return item['metadata']['name']

    def can_edit(self):
        return True

    def on_key_press(self, input_key):

        if input_key == ord("v"):
            self._show_selected()
        elif input_key == ord("e"):
            self._edit_selected()
        elif input_key in self._key_handlers:
            self._key_handlers[input_key]()
        else:
            super().on_key_press(input_key)

    def _edit_selected(self):

        if self.can_edit():
            current = self.current_item
            if current:
                editor = self._model._application.get_config().get("editor")
                if editor:
                    tf = tempfile.NamedTemporaryFile(mode="w+", delete=False)
                    yaml.dump(current.to_dict(), tf, Dumper=yaml.SafeDumper)
                    tf.flush()
                    result = subprocess.run([editor, tf.name])
                    if result.returncode == 0:
                        tf.seek(0)
                        new_contents = yaml.load(tf, Loader=yaml.SafeLoader)

    def _show_selected(self):
        current = self.current_item
        if current:
            result = yaml.dump(current, Dumper=yaml.SafeDumper).split("\n")
            self._application.show_text_popup(result)

