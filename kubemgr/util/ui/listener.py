class ListenerHandler:
    def __init__(self, source):
        self._source = source
        self._listeners = []

    def add(self, listener):
        self._listeners.append(listener)
        return self

    def remove(self, listener):
        self._listeners.remove(listener)
        return self

    def __call__(self, *args, **kwargs):
        for listener in self._listeners:
            listener(self._source, *args, **kwargs)
