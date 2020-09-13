class ShowLogs:
    def __init__(self, app):
        self._app = app

    def __call__(self, target):

        cluster = self._app.get_selected_cluster()

        if cluster:
            current = target.current_item

            if current:
                name = current["metadata"]["name"]
                namespace = current["metadata"]["namespace"]


                if cluster:
                    api = cluster.api_client
                    logs, _, _ = api.call_api(
                        f"/api/v1/namespaces/{namespace}/pods/{name}/log",
                        "GET",
                        response_type="str",
                        _preload_content=True,
                    )

                self._app.show_file(logs, "log")

