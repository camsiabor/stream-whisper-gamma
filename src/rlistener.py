import logging
import threading

import pyaudiowpatch as pyaudio

from src import rtask, rrecord, rslice, rtranscribe, rtranslate, rmanifest


class RListener(threading.Thread):
    def __init__(
            self,
            cfg, p: pyaudio.PyAudio = None):
        super().__init__()
        self.p = p
        if self.p is None:
            self.p = pyaudio.PyAudio()
        self.cfg = cfg

        self.task_ctrl = rtask.RTaskControl(cfg)

        self.recorder = None
        self.slicer = None
        self.transcriber = None
        self.translator = None
        self.renderer = None

        self.logger = logging.getLogger('listener')

    def configure_recorder(self):
        self.recorder = rrecord.Recorder(
            p_audio=self.p,
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

            while True:
                cmd: rtask.RCommand = self.task_ctrl.queue_command.get()
                if cmd is None or len(cmd.action) <= 0:
                    continue

                if cmd.action == "exit":
                    self.task_ctrl.terminate()
                    break

        except Exception as e:
            self.logger.error(e, exc_info=True, stack_info=True)
        finally:
            self.logger.info("end")
