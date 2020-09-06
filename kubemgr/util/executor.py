import threading
import time


class TaskExecutor:
    def __init__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._tasks = []
        self._active = True

    def add_task(self, task):
        self._tasks.append(task)

    def start(self):
        self._thread.start()

    def _run(self):
        while self._active:
            for task in self._tasks:
                try:
                    task()
                except Exception as e:
                    print(e)
            time.sleep(0.5)
