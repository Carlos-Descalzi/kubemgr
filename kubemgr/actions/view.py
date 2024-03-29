import logging
import yaml
from ..views.util import BASE_JINJA_CONTEXT
import logging

_logger = logging.getLogger(__name__)

class ViewResource:
    def __init__(self, app):
        self._app = app

    def __call__(self, target):
        current = target.current_item
        if current:
            _logger.debug(f"View resource {current}")
            result = yaml.dump(current, Dumper=yaml.SafeDumper)
            self._app.show_file(result, "yaml")


class CustomViewResource:
    def __init__(self, app):
        self._app = app

    def __call__(self, target):
        kind = target.model.resource_kind

        item = target.current_item
        template = self._app._detail_templates.get(kind)

        _logger.debug(f"Has template for {kind}? {template is not None}")

        if item and template:
            ctx = dict(BASE_JINJA_CONTEXT)
            ctx.update({"item": item})
            result = template.render(ctx)
            self._app.show_file(result, None, True)
