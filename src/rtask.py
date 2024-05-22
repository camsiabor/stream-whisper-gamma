import datetime
import logging
import multiprocessing
import os
import queue
import time
from concurrent.futures import ThreadPoolExecutor

import redis

from src.service.gui.root import RGuiRoot

NANO_TO_MILLI = 1_000_000

class RBot:
    def __init__(
            self,
            bot_id: any = "",
            model: any = "",
            chat_id: any = None,
            key: str = "",
            lang: any = "",
            prompt_type: str = "",
            info=None,
    ):
        if info is None:
            info = {}
        self.id = bot_id
        self.model = model
        self.chat_id = chat_id
        self.lang = lang
        self.key = key
        self.info = info
        self.prompt_type = prompt_type


class RParam:
    do_translate: bool
    lang_src: str
    lang_des: str

    sample_rate: int
    sample_width: int
    sample_channels: int


class RInfo:
    times = {}
    elapsed = {}
    sequence = 0

    def __init__(self):
        self.time_set("create")
        # self.time_set_as_str("create_str")

    def time_set(self, name: str):
        self.times[name] = time.time_ns() // NANO_TO_MILLI

    def time_elapsed(self, name: str, src: int = 0):
        if src <= 0:
            src = time.time_ns()
        self.elapsed[name] = round(src // NANO_TO_MILLI - self.times[name])

    def time_set_as_str(self, name: str):
        self.times[name] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def time_get(self, name: str, raise_if_none=False):
        ret = self.times[name]
        if ret is None:
            if raise_if_none:
                raise Exception(f"Time {name} is None")
            return 0
        return ret

    def time_elapsed_get(self, name: str):
        return self.elapsed.get(name, None)

    def time_diff(self, head: str, tail: str, store: str = None, raise_if_none=False):
        diff = self.time_get(tail, raise_if_none) - self.time_get(head, raise_if_none)
        if diff < 0:
            logging.warning(f"Time diff {head} -> {tail} is negative: {diff}")

        if store is not None:
            self.elapsed[store] = diff

        return diff

    def sequence_set(self, sequence: int = 0):
        if sequence <= 0:
            sequence = time.time_ns() // NANO_TO_MILLI
        self.sequence = sequence


class RCommand:

    def __init__(
            self,
            action: str,
            params: dict = None,
            extra=None,
    ):
        self.action = action
        self.params = params
        self.extra = extra


class RTask:

    def __init__(
            self,
            audio,
            sample_rate: int,
            sample_width: int,
            sample_channels: int,
            param=RParam(),
            info=None,
    ):
        self.audio = audio
        self.text_transcribe = ""
        self.text_translate = ""
        self.text_phoneme = ""
        self.text_info = None

        self.text_start = "",
        self.text_end = "",

        self.param = param
        self.param.sample_rate = sample_rate
        self.param.sample_width = sample_width
        self.param.sample_channels = sample_channels

        self.info = info
        if self.info is None:
            self.info = RInfo()


class RTaskControl:
    redis: redis.Redis
    queue_command = queue.Queue()
    queue_slice = queue.Queue()
    queue_transcribe = queue.Queue()
    queue_translate = queue.Queue()
    queue_manifest = queue.Queue()

    def __init__(
            self,
            cfg: dict,
            gui_root: RGuiRoot,
            thread_pool_size: int = 0,
    ):
        self.cfg = cfg
        self.gui_root = gui_root
        self.working_dir = os.getcwd()
        if thread_pool_size <= 0:
            thread_pool_size = multiprocessing.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_pool_size)

    def terminate(self):
        self.queue_command.put("exit")
        self.queue_slice.put(None)
        self.queue_transcribe.put(None)
        self.queue_translate.put(None)
        self.queue_manifest.put(None)
        self.thread_pool.shutdown()
