from kubemgr.util import ansi, kbd
import logging
import time
import sys
import tty
import os
import termios
import atexit
import fcntl


class Application:
    def __init__(self):
        self._components = []
        self._focused_index = 0
        self._active_popup = None
        self._popup_closeable = True
        self._active = True
        self._queue = set()
        self._key_handlers = {}

    def add_component(self, component):
        component.set_application(self)
        self._components.append(component)

    def remove_component(self, component):
        self._components.remove(component)
        component.application = None
        if self._focused_index >= len(self._components):
            self._cycle_focus()

    def main_loop(self):

        term_attrs = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin)
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        def on_exit():
            ansi.begin().clrscr().cursor_on().put()
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, term_attrs)

        atexit.register(on_exit)

        self.refresh()

        count = 0
        while self._active:
            self.empty_queue()
            #if count == 0:
                # Force some refresh
                #self._update_view()
            self._check_keyboard()
            count += 1
            if count >= 49:
                count = 0
            time.sleep(0.01)

        self._on_finish()

    def refresh(self):
        ansi.begin().clrscr().cursor_off().put()
        self._update_view()

    def _on_finish(self):
        """
        Placeholder for any release of resources
        """
        pass

    def empty_queue(self):
        queue = self._queue
        self._queue = set()
        try:
            for view in queue:
                view.update()
        except Exception as e:
            logging.error(e)

    def queue_update(self, view):
        if not self._active_popup:
            self._queue.add(view)

    def set_key_handler(self, keystroke, handler):
        self._key_handlers[keystroke] = handler

    def unset_key_handler(self, keystroke):
        self._key_handlers.pop(keystroke)

    def _check_keyboard(self):
        read = sys.stdin.read(3)

        if len(read) > 0:
            keystroke = kbd.keystroke_from_str(read)
            if keystroke == kbd.KEY_ESC:
                self._handle_exit()
            elif keystroke == kbd.KEY_TAB:
                self._cycle_focus()
            else:
                key_handler = self._key_handlers.get(keystroke)

                if key_handler:
                    key_handler(self)
                else:
                    # if not self.on_key_press(keystroke):
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

    def open_popup(self, view, closeable=True):
        max_height, max_width = ansi.terminal_size()
        view._rect.x = int((max_width - view._rect.width) / 2)
        view._rect.y = int((max_height - view._rect.height) / 2)
        self._active_popup = view
        self._active_popup.update()
        self._popup_closeable = closeable

    def close_popup(self):
        if self._active_popup:
            if self._popup_closeable:
                self._active_popup.set_application(None)
                self._active_popup = None
                ansi.begin().clrscr().put()
                self._update_view()
