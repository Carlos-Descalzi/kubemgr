from ..texts import FILTER_TEMPLATE, GLOBAL_FILTER_TEMPLATE
from ..util import misc
from ..views.resource import Filter
import subprocess
import logging

class EditFilterAction:
    def __init__(self, app):
        self._app = app
    
    def __call__(self,target):
        current_filter = target.model.filter

        text = current_filter.filter_string if current_filter else FILTER_TEMPLATE

        new_text = self._app.edit_file(text,".py")

        if new_text is not None: # None means didn't change
            if not new_text.strip():
                self._app.save_filter(target.model.resource_kind, None)
                target.model.filter = None
            elif new_text != text:
                self._app.save_filter(target.model.resource_kind, new_text)
                target.model.filter = Filter(new_text)
            

class EditGlobalFilterAction:
    def __init__(self, app):
        self._app = app

    def __call__(self, target):
        
        text = self._app.get_global_filter() or GLOBAL_FILTER_TEMPLATE
        logging.info(f'Old filter: {text}')

        new_text = self._app.edit_file(text,".py")

        if new_text is not None: # None means didn't change
            if not new_text.strip():
                self._app.set_global_filter(None)
            elif new_text != text:
                self._app.set_global_filter(new_text)
