import logging
import threading

import pyaudiowpatch as pyaudio
import redis

from src import rtask, rrecord, rslice, rtranscribe, rtranslate, rmanifest
from src.common import sim
from src.service.gui.root import RGuiRoot


class RListener(threading.Thread):
    recorders = []
    slicers = []
    transcribers = []
    translators = []
    renderers = []

    def __init__(
            self,
            cfg: dict,
            py_audio: pyaudio.PyAudio = None):
        super().__init__()
        self.py_audio = py_audio

        if self.py_audio is None:
            self.py_audio = pyaudio.PyAudio()

        self.cfg: dict = cfg
        self.gui_root = RGuiRoot(cfg)
        self.task_ctrl = rtask.RTaskControl(
            cfg=cfg, gui_root=self.gui_root
        )

        self.do_run = True
        self.lock = threading.Lock()
        self.logger = logging.getLogger('listener')
        self.configure()

    def configure(self):
        cfg_me = self.cfg.get("listener", {})
        redis_active = sim.get(cfg_me, False, "redis")
        if not redis_active:
            return
        cfg_redis = self.cfg.get("redis", {})
        host = cfg_redis["host"]
        port = cfg_redis["port"]
        self.task_ctrl.redis = redis.Redis(**cfg_redis)
        self.logger.info(f"redis client - {host}:{port}", )

    def gen_recorder(self, start=True):
        recorder = rrecord.Recorder(
            p_audio=self.py_audio,
            task_ctrl=self.task_ctrl,
        )
        self.recorders.append(recorder)
        if start:
            recorder.start()

    def gen_slicer(self, start=True):
        number = sim.get(self.cfg, 1, "slicer", "number")
        for i in range(number):
            slicer = rslice.RSlicer(
                task_ctrl=self.task_ctrl,
                index=i + 1,
            )
            self.slicers.append(slicer)
            if start:
                slicer.start()

    def gen_transcriber(self, start=True):
        number = sim.get(self.cfg, 1, "transcriber", "number")
        for i in range(number):
            transcriber = rtranscribe.RTranscriber(
                task_ctrl=self.task_ctrl,
                index=i + 1,
            ).init(force=True)
            self.transcribers.append(transcriber)
            if start:
                transcriber.start()

    def gen_translator(self, start=True):
        number = sim.get(self.cfg, 1, "translator", "number")
        for i in range(number):
            translator = rtranslate.RTranslator(
                task_ctrl=self.task_ctrl,
                index=i + 1,
            )
            self.translators.append(translator)
            if start:
                translator.start()

    def gen_renderer(self, start=True):
        number = sim.get(self.cfg, 1, "renderer", "number")
        for i in range(number):
            renderer = rmanifest.RManifest(
                task_ctrl=self.task_ctrl,
                index=i + 1,
            )
            self.renderers.append(renderer)
            if start:
                renderer.start()

    def terminiate(self):
        self.lock.acquire()
        try:
            self.task_ctrl.queue_command.put("exit")
            self.recorders.clear()
            self.slicers.clear()
            self.transcribers.clear()
            self.translators.clear()
            self.renderers.clear()
        finally:
            self.lock.release()

    def run(self):
        self.logger.info("start")
        try:

            self.lock.acquire()
            try:
                self.gen_renderer()
                self.gen_translator()
                self.gen_transcriber()
                self.gen_slicer()
                self.gen_recorder()
            finally:
                self.lock.release()

            while self.do_run:
                cmd: rtask.RCommand = self.task_ctrl.queue_command.get()
                if cmd is None or len(cmd.action) <= 0:
                    continue
                if cmd.action == "exit":
                    self.task_ctrl.terminate()
                    break

        except Exception as e:
            self.do_run = False
            self.logger.error(e, exc_info=True, stack_info=True)
        finally:
            self.logger.info("end")

    def gui_mainloop(self):
        self.gui_root.init()
        self.gui_root.run_mainloop()
