import logging
import threading

import pyaudiowpatch as pyaudio

from src import rtask, rrecord, rslice, rtranscribe, rtranslate, rmanifest
from src.service.gui.root import RGuiRoot


class RListener(threading.Thread):
    def __init__(
            self,
            cfg, p: pyaudio.PyAudio = None):
        super().__init__()
        self.py_audio = p
        if self.py_audio is None:
            self.py_audio = pyaudio.PyAudio()
        self.cfg = cfg

        self.gui_root = RGuiRoot(cfg)
        self.task_ctrl = rtask.RTaskControl(cfg, gui_root=self.gui_root)

        self.recorder = None
        self.slicer = None
        self.transcriber = None
        self.translator = None
        self.renderer = None

        self.do_run = True

        self.logger = logging.getLogger('listener')

    def configure_recorder(self):
        self.recorder = rrecord.Recorder(
            p_audio=self.py_audio,
            task_ctrl=self.task_ctrl,
        )

    def configure_slicer(self):
        self.slicer = rslice.RSlice(
            task_ctrl=self.task_ctrl,
        )

    def configure_transcriber(self):

        self.transcriber = rtranscribe.RTranscriber(
            task_ctrl=self.task_ctrl,
        ).init(force=True)

    def configure_translator(self):
        self.translator = rtranslate.RTranslator(
            task_ctrl=self.task_ctrl,
            lang_des=self.cfg['translator'].get('lang_des', 'en'),
        )

    def configure_renderer(self):
        self.renderer = rmanifest.RManifest(
            task_ctrl=self.task_ctrl,
        )

    def terminiate(self):

        self.task_ctrl.queue_command.put("exit")

    def run(self):
        self.logger.info("start")
        try:
            self.configure_recorder()
            self.configure_slicer()
            self.configure_transcriber()
            self.configure_translator()
            self.configure_renderer()

            self.renderer.start()
            self.translator.start()
            self.transcriber.start()
            self.slicer.start()
            self.recorder.start()

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
