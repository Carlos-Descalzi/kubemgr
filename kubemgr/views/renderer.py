import logging
from jinja2 import Template
from .util import BASE_JINJA_CONTEXT


class ItemRenderer:
    def __init__(self, app):
        self._app = app

    def __call__(self, view, item):
        template = self._get_template(view.model.resource_kind)
        if not template:
            return item["metadata"]["name"]
        ctx = dict(BASE_JINJA_CONTEXT)
        ctx.update({"item": item, "width": view._rect.width})
        return template.render(ctx).replace("\n", "").strip()

    def _get_template(self, kind):
        return self._app._item_templates.get(kind)
