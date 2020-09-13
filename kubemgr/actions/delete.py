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
            [("y", "Yes", confirm), ("n", "No", cancel),],
        )

    def _do_delete(self, target):
        cluster = self._app.selected_cluster
        item = target.current_item
        if cluster and item:
            try:
                cluster.do_delete(
                    target.model.api_group,
                    target.model.resource_kind,
                    item["metadata"]["name"],
                    item["metadata"]["namespace"],
                )
                target.update()
            except Exception as e:
                self._app.show_error(e)
