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
            contents = yaml.dump(item, Dumper=yaml.SafeDumper)
            new_contents = self._app.edit_file(contents, "yaml")
            if new_contents:
                new_yaml = yaml.load(io.StringIO(new_contents), Loader=yaml.SafeLoader)
                json_content = json.dumps(new_yaml)
                self.update(cluster, target, item, json_content)

    def update(self, cluster, target, item, contents):

        model = target.model

        try:
            cluster.do_patch(
                model.api_group,
                model.resource_kind,
                item["metadata"]["name"],
                item["metadata"]["namespace"],
                body=contents,
                content_type="application/json-patch+json",
            )
        except Exception as e:
            self._app.show_error(e)
