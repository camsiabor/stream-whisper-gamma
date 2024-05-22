import collections
import threading
import time


class RPersistFiler(threading.Thread):
    def __init__(self, flush_interval: int = 5, output_dir: str = "./output"):
        super().__init__()
        self.buffer = collections.deque()
        self.flush_interval = flush_interval
        self.file = None
        self.do_run = True
        pass

    def init(self, file):
        if file is None:
            self.file = file

    def run(self):
        while self.do_run:
            time.sleep(self.flush_interval)
