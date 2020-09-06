from kubemgr.util.ui import Rect, TextView, ListView
from kubernetes import client
from ..util import ansi
from .util import AsyncListModel
from abc import ABCMeta, abstractclassmethod
import yaml


class ResourceListView(ListView, metaclass=ABCMeta):

    def render_item(self, item, current, selected):
        width = self._rect.width
        buff = ansi.begin()

        if self.focused and current:
            buff.underline()

        return str(
            buff.write(
                self.do_render_item(item, width)
            ).reset()
        )

    @abstractclassmethod
    def do_render_item(self, item, width):
        pass

    def on_key_press(self, input_key):

        if input_key == ord('v'):
            self._show_selected() 
        else:
            super().on_key_press(input_key)

    def _show_selected(self):
        current = self.current_item

        max_height, max_width = ansi.terminal_size()

        popup_width = int(max_width * 0.75)
        popup_height = int(max_height * 0.75)

        rect = Rect(
            int((max_width - popup_width)/2),
            int((max_height - popup_height)/2),
            popup_width,
            popup_height
        )
        result = yaml.dump(current.to_dict(),Dumper=yaml.SafeDumper).split('\n')#, tf)
        text_view = TextView(rect=rect, text=result)
        self.application.open_popup(text_view)
