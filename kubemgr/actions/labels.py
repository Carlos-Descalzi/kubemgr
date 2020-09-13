
class ShowNodeLabels:

    def __init__(self, app):
        self._app = app

    def __call__(self, *_):
        current = self.app._nodes_view.current_item
        labels = current["metadata"]["labels"]
        name = current["metadata"]["name"]
        labels_text = (
            [f"Labels for node {name}", "======================", ""]
            + [f"{k:50} : {v}" for k, v in labels.items()]
            + [""]
        )
        self.app.show_text_popup(labels_text)

