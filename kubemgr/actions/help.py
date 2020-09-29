from kubemgr.texts import HELP_CONTENTS


class ShowHelp:
    def __init__(self, app):
        self._app = app

    def __call__(self, *_):
        self._app.show_text_popup(HELP_CONTENTS)
