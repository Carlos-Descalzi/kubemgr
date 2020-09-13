from kubemgr.util import ansi, kbd
from .base import Rect, COLORS
from .view import View
import time
import sys
import tty
import logging


class TabbedView(View):
    class Tab:
        def __init__(self, title, view):
            self.title = title
            self.view = view

    def __init__(self, rect=None):
        super().__init__(rect)
        self._tabs = []
        self._active = 0

    @property
    def active_tab(self):
        return self._tabs[self._active] if self._tabs else None

    def add_tab(self, title, view):
        view.application = self.application
        self._tabs.append(TabbedView.Tab(title, view))

    def set_application(self, application):
        super().set_application(application)
        for tab in self._tabs:
            tab.view.set_application(application)

    def set_focused(self, focused):
        super().set_focused(focused)
        active = self.active_tab
        if active:
            active.view.set_focused(focused)

    def _get_visible_tabs(self):
        # Tabs may not fit in available terminal width.
        max_width = max([len(i.title) + 1 for i in self._tabs])
        visible_tab_count = int(self._rect.width / max_width)
        scroll_x = int(self._active / visible_tab_count) * visible_tab_count
        return self._tabs[scroll_x : scroll_x + visible_tab_count], max_width

    def update(self):

        header_buff = ansi.begin()

        tabs, max_width = self._get_visible_tabs()

        active_tab = self._tabs[self._active] if self._tabs else None

        for tab in tabs:
            if tab == active_tab:
                header_buff.write(self.get_color("selected.bg")).write(
                    self.get_color("selected.fg")
                )
            else:
                header_buff.write(self.get_color("bg")).write(self.get_color("fg"))
            header_buff.writefill(f"{tab.title}", max_width).reset()

        (
            ansi.begin()
            .gotoxy(self._rect.x, self._rect.y)
            .write(self.get_color("bg"))
            .writefill("", self._rect.width)
        ).put()

        header = str(header_buff)

        (ansi.begin().gotoxy(self._rect.x, self._rect.y).write(header).reset()).put()

        if active_tab:
            inner_rect = self._rect.copy()
            inner_rect.y += 1
            inner_rect.height -= 1
            active_tab.view.set_rect(inner_rect)
            active_tab.view.queue_update()

    def _set_active(self, active):
        self._tabs[self._active].view.visible = False
        self._tabs[self._active].view.set_focused(False)
        self._active = active
        self._tabs[self._active].view.visible = True
        self._tabs[self._active].view.set_focused(True)
        self.queue_update()

    def on_key_press(self, key):

        if key == kbd.KEY_RIGHT:
            if self._active < len(self._tabs) - 1:
                self._set_active(self._active + 1)
        elif key == kbd.KEY_LEFT:
            if self._active > 0:
                self._set_active(self._active - 1)
        else:
            active = self.active_tab
            if active:
                active.view.on_key_press(key)
