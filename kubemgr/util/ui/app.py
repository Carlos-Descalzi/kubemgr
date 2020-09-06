from kubemgr.util import ansi, kbd
import time
import sys
import tty


class Application:
    def __init__(self):
        self._components = []
        self._focused_index = 0
        self._active_popup = None
        self._active = True
        self._queue = []

    def add_component(self, component):
        component.set_application(self)
        self._components.append(component)

    def remove_component(self, component):
        self._components.remove(component)
        component.application = None
        if self._focused_index >= len(self._components):
            self._cycle_focus()

    def main_loop(self):
        import fcntl
        import os

        tty.setraw(sys.stdin)
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        ansi.begin().clrsrc().put()
        count = 0
        while self._active:
            self.empty_queue()
            if count == 0:
                self._update_view()
            self._check_keyboard()
            count += 1
            if count >= 49:
                count = 0
            time.sleep(0.01)

        tty.setcbreak(sys.stdin)

    def empty_queue(self):
        queue = self._queue
        self._queue = []
        for task in queue:
            try:
                task()
            except Exception as e:
                print(e)


    def queue_task(self, task):
        if not self._active_popup:
            self._queue.append(task)

    def _check_keyboard(self):
        read = sys.stdin.read(3)

        if len(read) > 0:
            keystroke = kbd.make_keystroke(list(map(ord, read)))
            if keystroke == kbd.KEY_ESC:
                self._handle_exit()
            elif keystroke == kbd.KEY_TAB:
                self._cycle_focus()
            else:
                self._send_key_event(keystroke)

    def _handle_exit(self):
        if self._active_popup:
            self.close_popup()
        else:
            self._active = False

    def _cycle_focus(self):
        if self._active_popup:
            self._active_popup.set_focused(True)

        if self._components:
            active = self._components[self._focused_index]
            active.set_focused(False)
            self._focused_index += 1
            if self._focused_index >= len(self._components):
                self._focused_index = 0
            active = self._components[self._focused_index]
            active.set_focused(True)

    def _send_key_event(self, input_key):
        if self._active_popup:
            self._active_popup.on_key_press(input_key)
        else:
            if self._components:
                self._components[self._focused_index].on_key_press(input_key)

    def _update_view(self):
        if self._active_popup:
            self._active_popup.update()
        else:
            for component in self._components:
                component.update()

    def open_popup(self, view):
        self._active_popup = view
        self._active_popup.update()

    def close_popup(self):
        if self._active_popup:
            self._active_popup.set_application(None)
            self._active_popup = None

        ansi.begin().clrsrc().put()
        self._update_view()
