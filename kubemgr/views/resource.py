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

class ResourceListModel(AsyncListModel):
    def __init__(self, application, resource_name):
        super().__init__(application)
        self._resource_name = resource_name
        self._namespace = None
        
    def set_namespace(self, namespace):
        self._namespace = namespace

    def get_api_client_and_resource(self):
        cluster = self._application.selected_cluster
        if cluster and cluster.api_client:
            return cluster.api_client, cluster.get_resource(self._resource_name)
        return None, None

    def _build_path(self, resource):
        path = '/api/v1'
        if self._namespace:
            path+= f'/namespaces/{self._namespace}'
        path+=f'/{resource.name}'

        return path

    def fetch_data(self):
        api_client, resource = self.get_api_client_and_resource()

        if api_client:
            path = self._build_path(resource)
            logging.info(path)
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


class ResourceListView(ListView, metaclass=ABCMeta):
    def render_item(self, item, current, selected):
        width = self._rect.width
        buff = ansi.begin()

        if self.focused and current:
            buff.underline()

        return str(buff.write(self.do_render_item(item, width)).reset())

    @abstractclassmethod
    def do_render_item(self, item, width):
        pass

    def can_edit(self):
        return True

    def on_key_press(self, input_key):

        if input_key == ord("v"):
            self._show_selected()
        elif input_key == ord("e"):
            self._edit_selected()
        else:
            super().on_key_press(input_key)

    def _edit_selected(self):

        if self.can_edit():
            editor = self._model._application.get_config().get("editor")
            if editor:
                current = self.current_item
                tf = tempfile.NamedTemporaryFile(mode="w+", delete=False)
                yaml.dump(current.to_dict(), tf, Dumper=yaml.SafeDumper)
                tf.flush()
                result = subprocess.run([editor, tf.name])
                if result.returncode == 0:
                    tf.seek(0)
                    new_contents = yaml.load(tf, Loader=yaml.SafeLoader)

    def _show_selected(self):
        current = self.current_item
        result = yaml.dump(current, Dumper=yaml.SafeDumper).split("\n")

        self._show_text(result)

    def _show_text(self, text):
        max_height, max_width = ansi.terminal_size()

        popup_width = int(max_width * 0.75)
        popup_height = int(max_height * 0.75)

        rect = Rect(
            int((max_width - popup_width) / 2),
            int((max_height - popup_height) / 2),
            popup_width,
            popup_height,
        )
        text_view = TextView(rect=rect, text=text)
        self.application.open_popup(text_view)

class DefaultResourceListView(ResourceListView):
    def do_render_item(self, item, width):
        return item['metadata']['name']
