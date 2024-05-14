import threading
import traceback

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

    def configure_recorder(self):
        self.recorder = rrecord.Recorder(
            p_audio=self.p,
            task_ctrl=self.task_ctrl,
            data_format=self.cfg['recorder'].get('data_format', pyaudio.paInt16),
            chunk_size=self.cfg['recorder'].get('chunk_size', 512),
            frame_duration=self.cfg['recorder'].get('frame_duration', 10),
        )

    def configure_slicer(self):
        self.slicer = rslice.RSlice(
            task_ctrl=self.task_ctrl,
            slicer_maxlen=self.cfg['slicer'].get('slicer_maxlen', 10),
            slicer_ratio=self.cfg['slicer'].get('slicer_ratio', 0.5),
        )

    def configure_transcriber(self):
        self.transcriber = rtranscribe.RTranscriber(
            task_ctrl=self.task_ctrl,
            model_size=self.cfg['transcriber'].get('model_size', 'large-v3'),
            local_files_only=self.cfg['transcriber'].get('local_files_only', False),
            device=self.cfg['transcriber'].get('device', 'auto'),
            prompt=self.cfg['transcriber'].get('prompt', 'hello world'),
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

        print("[listener] start")
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

        except KeyboardInterrupt:
            print("KeyboardInterrupt: terminating...")
        except Exception as e:
            traceback.print_exc()
        finally:
            print("[listener] end")
