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
        self.do_run = True

    def close(self):
        self.do_run = False
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

    def flush_one(self, task: rtask.RTask):

        lang_src = task.param.lang_src
        lang_des = task.param.lang_des

        manifest = task.param.manifest

        if manifest.transcribe and len(task.text_transcribe) > 0:
            self.file.write(f"[[{lang_src}]] {task.text_transcribe}\n")

        if manifest.phoneme and len(task.text_phoneme) > 0:
            self.file.write(f"[[**]] {task.text_phoneme}\n")

        if manifest.translated and len(task.text_translate) > 0:
            self.file.write(f"[[{lang_des}]] {task.text_translate}\n")

        self.file.write("\n")
        self.file.flush()

    def flush(self):
        array = None
        try:
            self.lock.acquire()
            if len(self.buffer) <= 0:
                return
            array = list(self.buffer)
            self.buffer.clear()
        finally:
            self.lock.release()

        for task in array:
            self.flush_one(task)

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
