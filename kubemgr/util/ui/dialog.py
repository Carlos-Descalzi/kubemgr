from .view import View
from kubemgr.util import ansi
from .base import Rect

class QuesstionDialog(View):
    
    class Option:
        def __init__(self, label, handler):
            self.label = label
            self.handler = handler

    def __init__(self, title, message, options={}):
        super().__init__()
        self._title = title
        self._message = message
        self._options = options
        self._options_text = ' '.join([
            f'{chr(k)}: {v.label}' for k,v in self._options.items()
        ])
        self._rect = Rect(0,0,max(map(len,[self._title,self._message,self._options_text]))+2,5)

    def update(self):

        options_text = (' '* (self._rect.width-len(self._options_text))) + self._options_text

        (ansi
            .begin()
            .reverse()
            .gotoxy(self._rect.x, self._rect.y).
            .writefill(self._title,self._rect.width).
            .reset()
            .gotoxy(self._rect.x, self._rect.y+1)
            .writefill('',self._rect.width)
            .gotoxy(self._rect.x, self._rect.y+2)
            .writefill(self._message,self._rect.width)
            .gotoxy(self._rect.x, self._rect.y+3)
            .writefill('',self._rect.width)
            .gotoxy(self._rect.x, self._rect.y+4)
            .reverse()
            .writefill(self._options_text)
            .reset()
        ).put()

    def on_key_press(self, input_key):
        if input_key in self.options:
            self.options[input_key].handler()


