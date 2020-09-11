import threading
import time
import logging
import traceback


class TaskExecutor:
    """
    A background thread where to push things when we don't want to 
    block UI. 
    Cycles over tasks every second. Tasks can run only once or on every loop.
    """

    def __init__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._tasks = []
        self._active = True
        self._lock = threading.Lock()

    def start(self):
        self._thread.start()

    def add_task(self, task, loop=True):
        with self._lock:
            self._tasks.append((task, loop))

    def finish(self):
        if self._active and self._thread:
            self._tasks.clear()
            self._active = False

    def _run(self):
        while self._active:
            try:
                to_remove = set()
                for item in self._tasks:
                    task, loop = item
                    try:
                        task()
                    except Exception as e:
                        logging.error(str(e) + str(traceback.format_exc()))
                    if not loop:
                        to_remove.add(item)

                with self._lock:
                    self._tasks = [t for t in self._tasks if not t in to_remove]
            except Exception as e:
                logging.error(str(e) + str(traceback.format_exc()))

            time.sleep(1)
