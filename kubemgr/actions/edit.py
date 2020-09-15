import io
import yaml
import json
import logging


class EditResource:
    def __init__(self, app):
        self._app = app

    def __call__(self, target):
        item = target.current_item
        cluster = self._app.selected_cluster
        if item and cluster:
            item["kind"] = target.model.resource_kind
            item["apiVersion"] = target.model.api_group
            contents = yaml.dump(item, Dumper=yaml.SafeDumper)
            new_contents = self._app.edit_file(contents, "yaml")
            if new_contents:
                new_json = self._to_dict(new_contents)
                self._update(cluster, target, item, new_json)

    def _to_dict(self, yaml_string):
        return yaml.load(io.StringIO(yaml_string), Loader=yaml.SafeLoader)

    def _update(self, cluster, target, item, contents):
        model = target.model
        try:
            cluster.do_patch(
                model.api_group,
                model.resource_kind,
                item["metadata"]["name"],
                item["metadata"]["namespace"],
                body=contents,
                content_type="application/merge-patch+json",
            )
        except Exception as e:
            self._app.show_error(e)
