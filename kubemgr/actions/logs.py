class ShowLogs:
    def __init__(self, app):
        self._app = app

    def __call__(self, *_):
        current = self.app._pods_view.current_item

        name = current["metadata"]["name"]
        namespace = current["metadata"]["namespace"]

        cluster = self.app.get_selected_cluster()

        if cluster:
            api = cluster.api_client
            logs, _, _ = api.call_api(
                f"/api/v1/namespaces/{namespace}/pods/{name}/log",
                "GET",
                response_type="str",
                _preload_content=True,
            )

        self.app.show_file(logs, "log")

