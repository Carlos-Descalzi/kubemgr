import logging
from datetime import datetime, timedelta, timezone
from jinja2 import Template


class ItemRenderer:
    def __init__(self, app):
        self._app = app
        self._templates = {}
        self._default_context = {"fill": self._do_fill, "age": self._do_age, "str": str}

    def _do_fill(self, string, length):
        # > 0 means left padding, < 0 right padding.
        l = abs(length)
        if len(string) > l:
            string = string[0:l]
        elif len(string) < l:
            padding = " " * (l - len(string))
            if length > 0:
                string += padding
            else:
                string = padding + string
        return string

    def _do_age(self, date_string):
        now = datetime.now(tz=timezone.utc)
        dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
        delta = now - dt

        if delta.days > 0:
            return f"{delta.days}d"

        minutes = int(delta.seconds / 60) % 60
        hours = int(delta.seconds / (60 * 60)) % 24
        delta_str = ""
        if hours > 0:
            delta_str += f"{hours}h"
        delta_str += f"{minutes}m"
        return delta_str

    def __call__(self, view, item):
        template = self._get_template(view.model.resource_kind)
        if not template:
            return item["metadata"]["name"]
        ctx = dict(self._default_context)
        ctx.update({"item": item, "width": view._rect.width})
        return template.render(ctx).replace("\n", "").strip()

    def _get_template(self, kind):
        if not kind in self._templates:
            if kind in self._app._templates:
                template = self._app._templates[kind]
                self._templates[kind] = Template(template)
        return self._templates.get(kind)
