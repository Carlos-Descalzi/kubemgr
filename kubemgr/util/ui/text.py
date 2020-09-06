from .view import View
from kubemgr.util import kbd, ansi


class TextView(View):
    def __init__(self, rect=None, text=[]):
        super().__init__(rect)
        self._text = text
        self._scroll_x = 0
        self._scroll_y = 0

    def update(self):
        height = self._rect.height
        width = self._rect.width

        chunk = self._text[self._scroll_y : self._scroll_y + height]
        chunk = [l[self._scroll_x : self._scroll_x + width] for l in chunk]

        for i, line in enumerate(chunk):
            ansi.begin().write(self.get_color("bg")).write(self.get_color("fg")).gotoxy(
                self._rect.x, self._rect.y + i
            ).writefill(line, self._rect.width).reset().put()

    def on_key_press(self, input_key):
        if input_key == kbd.KEY_DOWN:
            self._scroll_down()
        elif input_key == kbd.KEY_UP:
            self._scroll_up()
        elif input_key == kbd.KEY_LEFT:
            self._scroll_left()
        elif input_key == kbd.KEY_RIGHT:
            self._scroll_right()
        elif input_key == kbd.KEY_PGUP:
            self._page_up()
        elif input_key == kbd.KEY_PGDN:
            self._page_down()
        elif input_key == kbd.KEY_HOME:
            self._home()

    def _home(self):
        self._scroll_y = 0
        self._scroll_x = 0
        self.update()

    def _page_down(self):
        self._scroll_y += self._rect.height
        if self._scroll_y + self._rect.height >= len(self._text):
            self._scroll_y = len(self._text) - self._rect.height - 1
        self.update()

    def _page_up(self):
        self._scroll_y -= self._rect.height
        if self._scroll_y < 0:
            self._scroll_y = 0
        self.update()

    def _scroll_down(self):
        self._scroll_y += 1
        self.update()

    def _scroll_up(self):
        if self._scroll_y > 0:
            self._scroll_y -= 1
            self.update()

    def _scroll_right(self):
        self._scroll_x += 1
        self.update()

    def _scroll_left(self):
        if self._scroll_x > 0:
            self._scroll_x -= 1
            self.update()
