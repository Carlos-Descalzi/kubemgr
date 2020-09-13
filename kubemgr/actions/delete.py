import logging

class DeleteResource:
    def __init__(self, app):
        self._app = app

    def __call__(self, target):

        def confirm():
            self._do_delete(target)

        def cancel():
            pass

        self._app.show_question_dialog(
            "Warning",
            "Sure you want to delete the resource?",
            [
                ("y", "Yes", confirm),
                ("n", "No", cancel),
            ],
        )

    def _do_delete(self, target):
        cluster = self._app.selected_cluster
        if cluster:
            item = target.current_item
            if item:
                api_client = cluster.api_client
                resource = cluster.get_resource(
                    target.model.api_group, 
                    target.model.resource_kind
                )

                path = cluster.build_path(
                    target.model.api_group,
                    resource, 
                    item["metadata"]["name"], 
                    item["metadata"]["namespace"]
                )
                response = api_client.call_api(path, "DELETE")
                logging.info(response)

            target.update()

