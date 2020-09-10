import threading
import time
import logging
import traceback


class TaskExecutor:
    def __init__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._tasks = []
        self._active = True

    def add_task(self, task, loop=True):
        self._tasks.append((task, loop))

    def start(self):
        self._thread.start()

    def finish(self):
        if self._active and self._thread:
            self._active = False
            self._thread.join()

    def _run(self):
        while self._active:
            to_remove = []
            for item in self._tasks:
                task, loop = item
                try:
                    task()
                except Exception as e:
                    logging.error(str(e) + str(traceback.format_exc()))
                if not loop:
                    to_remove.append(item)

            for task in to_remove:
                self._tasks.remove(task)

            time.sleep(0.5)
