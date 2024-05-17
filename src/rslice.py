import collections
import io
import logging
import threading
import traceback
import typing
import wave

import webrtcvad

from src import rtask


class RSlice(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            slicer_maxlen: int = 10,
            slicer_ratio: float = 0.5,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.do_run = True

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(1)

        self.slicer_maxlen = slicer_maxlen
        self.slicer_ratio = slicer_ratio

        self.__frames: typing.List[bytes] = []

        self.logger = logging.getLogger('slicer')

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

    def run(self):
        self.logger.info("running")
        error_count = 0

        watcher = collections.deque(maxlen=self.slicer_maxlen)
        triggered = False

        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_slice.get()
                if task is None:
                    break

                try:
                    is_speech = self.vad.is_speech(task.audio, task.param.sample_rate)
                except Exception as ex:
                    is_speech = True
                    self.logger.error(f"[recorder] vad.is_speech() failed: {ex}")
                    self.logger.error(ex, exc_info=True, stack_info=True)

                watcher.append(is_speech)
                self.__frames.append(task.audio)
                if not triggered:
                    num_voiced = len([x for x in watcher if x])
                    if num_voiced > self.slicer_ratio * watcher.maxlen:
                        # logging.info("start recording...")
                        triggered = True
                        watcher.clear()
                        self.__frames = self.__frames[-self.slicer_maxlen:]
                else:
                    num_unvoiced = len([x for x in watcher if not x])
                    if num_unvoiced > self.slicer_ratio * watcher.maxlen:
                        triggered = False
                        task.audio = self.get_current_frames(task, clear=True)
                        self.task_ctrl.queue_transcribe.put(task)

            except Exception:
                traceback.print_exc()
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1

        self.logger.info("end")
