import logging
import yaml

class ViewResource:

    def __init__(self, app):
        self._app = app

    def __call__(self, target):
        current = target.current_item
        if current:
            result = yaml.dump(current, Dumper=yaml.SafeDumper)
            self._app.show_file(result, "yaml")

