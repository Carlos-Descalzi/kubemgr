class ShowLogs:
    def __init__(self, app):
        self._app = app

    def __call__(self, target):

        cluster = self._app.get_selected_cluster()
        current = target.current_item

        if cluster and current:

            name = current["metadata"]["name"]
            namespace = current["metadata"]["namespace"]

            try:
                logs = cluster.do_get(
                    target.model.api_group,
                    target.model.resource_kind,
                    name,
                    namespace,
                    "log",
                )

                self._app.show_file(logs.decode(), "log")
            except Exception as e:
                self._app.show_error(e)
