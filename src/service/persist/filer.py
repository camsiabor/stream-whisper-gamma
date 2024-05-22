import collections
import datetime
import logging
import threading
import time

from src import rtask
from src.common import sim


class RPersistToFile(threading.Thread):
    def __init__(
            self,
            name: str = "",
            filename: str = "",
            output_dir: str = "./output",
            flush_interval: int = 5,
    ):
        super().__init__()

        self.buffer = collections.deque()
        self.lock = threading.Lock()

        self.name = name
        self.filename = filename
        self.output_dir = output_dir
        self.flush_interval = flush_interval
        self.filepath = ""
        self.file = None

        self.do_run = True

        self.logger = logging.getLogger(f"file-persist-{self.name}")
        pass

    def __enter__(self):
        self.init()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def init(self):
        if len(self.filename) <= 0:
            self.filename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
        self.filepath = f"{self.output_dir}/{self.filename}"
        self.file = sim.FileIO.fopen(self.filepath, "a")

    def close(self):
        if self.file is not None:
            self.file.close()

    def push(self, task: rtask.RTask):
        try:
            self.lock.acquire()
            sim.Collection.insort_ex(
                self.buffer,
                task,
                key=lambda item: item.info.times["create"]
            )
            self.buffer.append(task)
        finally:
            self.lock.release()

    def flush(self):
        try:
            self.lock.acquire()

        finally:
            self.lock.release()

    def run(self):
        try:
            self.init()
            self.logger.info(f"Start persisting to file: {self.filepath}")
            while self.do_run:
                time.sleep(self.flush_interval)
                self.flush()
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)
        finally:
            self.close()
