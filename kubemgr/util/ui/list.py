from kubemgr.util import ansi, kbd
from .base import Rect
from .view import View
import time
import sys
import tty
from abc import ABCMeta, abstractmethod


class ListModel(metaclass=ABCMeta):

    _on_item_added = None
    _on_item_removed = None
    _on_item_changed = None
    _on_list_changed = None

    def set_on_item_added(self, on_item_added):
        self._on_item_added = on_item_added

    def set_on_item_removed(self, on_item_removed):
        self._on_item_removed = on_item_removed

    def set_on_item_changed(self, on_item_changed):
        self._on_item_changed = on_item_changed

    def set_on_list_changed(self, on_list_changed):
        self._on_list_changed = on_list_changed

    @abstractmethod
    def get_item_count(self):
        pass

    @abstractmethod
    def get_item(self, index):
        pass


class ListView(View):
    def __init__(self, rect=None, model=None, selectable=False):
        super().__init__(rect)
        self._model = None
        self._scroll_y = 0
        self._selectable = selectable
        self._current_index = 0
        self._selected_index = -1
        self._on_select = None
        self.set_model(model)

    def set_selectable(self, selectable):
        self._selectable = selectable

    def get_selectable(self):
        return self._selectable

    selectable = property(get_selectable, set_selectable)

    def set_on_select(self, listener):
        self._on_select = listener

    def get_on_select(self):
        return self._on_select

    on_select = property(get_on_select, set_on_select)

    @property
    def current_item(self):
        return self._model.get_item(self._current_index)

    def set_model(self, model):
        if self._model:
            self._model.set_on_item_added(None)
            self._model.set_on_item_removed(None)
            self._model.set_on_item_changed(None)
            self._model.set_on_list_changed(None)

        self._model = model

        if self._model:
            self._model.set_on_item_added(self._mark_dirty)
            self._model.set_on_item_removed(self._mark_dirty)
            self._model.set_on_item_changed(self._mark_dirty)
            self._model.set_on_list_changed(self._mark_dirty)

    def _mark_dirty(self):
        self._dirty = True

    def get_model(self):
        return self._model

    model = property(get_model, set_model)

    def render_item(self, item, current, selected):
        return str(item) if item else ""

    def update(self):
        max_items = self._rect.height

        from_index = self._scroll_y
        to_index = min(self._scroll_y + max_items - 1, self._model.get_item_count() - 1)

        current_index = self._scroll_y + self._current_index
        selected_index = (
            (self._scroll_y + self._selected_index)
            if self._selected_index != -1
            else -1
        )

        for i in range(from_index, to_index + 1):
            item = self._model.get_item(i)
            item_index = self._scroll_y + i

            current = item_index == current_index
            selected = self._selectable and item_index == selected_index

            text = self.render_item(item, current, selected)
            (
                ansi.begin()
                .gotoxy(self._rect.x, self._rect.y + i)
                .writefill(text, self._rect.width)
            ).put()

        last_y = self._rect.y + (to_index + 1 - from_index)
        max_y = self._rect.y + self._rect.height - 2

        ui_buff = ansi.begin()
        while last_y < max_y:
            ui_buff.gotoxy(self._rect.x, last_y).write(" " * self._rect.width)
            last_y += 1
        ui_buff.put()

    def on_key_press(self, key):
        if key == kbd.KEY_UP:
            if self._current_index > 0:
                self._current_index -= 1
                self.queue_update()
        elif key == kbd.KEY_DOWN:
            if self._current_index < self._model.get_item_count() - 1:
                self._current_index += 1
                self.queue_update()
        elif key == 13:
            if self._selectable:
                self._select(self._current_index)

    def _select(self, index):
        self._selected_index = index
        self._notify_selected(index)
        self.update()

    def get_selected_item(self):
        if self._selected_index != -1:
            return self._model.get_item(self._selected_index)

    def get_selected_index(self):
        return self._selected_index

    def _notify_selected(self, index):
        if self._on_select:
            item = self._model.get_item(index) if index != -1 else None
            self._on_select(item)
