import collections
import io
import logging
import threading
import typing
import wave

import noisereduce
import numpy
import webrtcvad

from src import rtask


# from pyAudioAnalysis import audioSegmentation

class RSlice(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.do_run = True

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(1)

        self.buffer_len = 10
        self.speech_len = 5
        self.non_speech_len = 5
        self.silence_ratio = 0.5
        self.slice_mode = ""
        self.denoise_ratio = 0

        self.__frames: typing.List[bytes] = []

        self.logger = logging.getLogger('slicer')

        self.configure()

    def configure(self) -> 'RSlice':
        cfg = self.task_ctrl.cfg.get("slicer", {})
        self.buffer_len = cfg.get("buffer_len", 10)
        self.speech_len = cfg.get("speech_len", 5)
        self.non_speech_len = cfg.get("non_speech_len", 5)
        self.denoise_ratio = cfg.get("denoise_ratio", 0)
        self.slice_mode = cfg.get("slice_mode", "vad").lower()
        return self

    def get_current_frames(
            self,
            task: rtask.RTask,
            clear: bool = True
    ) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(task.param.sample_channels)
            wf.setsampwidth(task.param.sample_width)
            wf.setframerate(task.param.sample_rate)
            wf.writeframes(b''.join(self.__frames))
        if clear:
            self.__frames.clear()
        return buf.getvalue()

    def slice_by_interval(self):
        error_count = 0
        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_slice.get()
                if task is None:
                    break
                task.info.time_set("slice")

                if self.denoise_ratio > 0:
                    try:
                        # librosa may get some numpy.float error, fix librosa utils to do the hack
                        data = numpy.frombuffer(task.audio, dtype=numpy.int16)
                        task.audio = noisereduce.reduce_noise(
                            y=data,
                            prop_decrease=self.denoise_ratio,
                            # use_torch=True,
                            sr=int(task.param.sample_rate)
                        )
                    except Exception as ex:
                        self.logger.error(f"noisereduce.reduce_noise failed: {ex}", stack_info=True)

                task.audio = self.get_current_frames(task, clear=True)
                self.task_ctrl.queue_transcribe.put(task)
            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1

    def slice_by_vad(self):
        error_count = 0

        watcher = collections.deque(maxlen=self.buffer_len)
        triggered = False

        task_head = None


        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_slice.get()
                if task is None:
                    break

                if task_head is None:
                    task.info.time_set("slice")
                    task_head = task

                if self.denoise_ratio > 0:
                    try:
                        # librosa may get some numpy.float error, fix librosa utils to do the hack
                        data = numpy.frombuffer(task.audio, dtype=numpy.int16)
                        task.audio = noisereduce.reduce_noise(
                            y=data,
                            prop_decrease=self.denoise_ratio,
                            # use_torch=True,
                            sr=int(task.param.sample_rate)
                        )
                    except Exception as ex:
                        self.logger.error(f"noisereduce.reduce_noise failed: {ex}", stack_info=True)

                try:
                    is_speech = self.vad.is_speech(task.audio, task.param.sample_rate)
                except Exception as ex:
                    is_speech = False
                    self.logger.error(f"vad.is_speech() failed - speech len {len(task.audio)}- {ex}")
                    self.logger.error(ex, exc_info=True, stack_info=True)

                watcher.append(is_speech)
                self.__frames.append(task.audio)
                if not triggered:
                    num_voiced = len([x for x in watcher if x])
                    if num_voiced > self.speech_len:
                        # logging.info("start recording...")
                        triggered = True
                        watcher.clear()
                        self.__frames = self.__frames[-self.slicer_maxlen:]
                else:
                    num_unvoiced = len([x for x in watcher if not x])
                    if num_unvoiced > self.non_speech_len:
                        triggered = False
                        task.audio = self.get_current_frames(task, clear=True)
                        task_head.info.time_diff("slice", "create", store="slice")
                        task.info = task_head.info
                        self.task_ctrl.queue_transcribe.put(task)
                        task_head = None

            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1

    def run(self):
        self.logger.info("running")
        if self.slice_mode == "vad":
            self.slice_by_vad()
        if self.slice_mode == "interval":
            self.slice_by_interval()
        self.logger.info("end")
