import collections
import io
import logging
import os
import queue
import threading
import typing
import wave

import pyaudio
import webrtcvad
from faster_whisper import WhisperModel

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"



class Queues:
    audio = queue.Queue()
    text = queue.Queue()


class AudioRecorder(threading.Thread):
    """ Audio recorder.
    Args:
        channels (int, 可选): 通道数，默认为1（单声道）。
        rate (int, 可选): 采样率，默认为16000 Hz。
        chunk (int, 可选): 缓冲区中的帧数，默认为256。
        frame_duration (int, 可选): 每帧的持续时间（单位：毫秒），默认为30。
    """

    def __init__(self,
                 channels: int = 1,
                 sample_rate: int = 16000,
                 chunk: int = 256,
                 frame_duration: int = 30) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.frame_size = (sample_rate * frame_duration // 1000)
        self.__frames: typing.List[bytes] = []

    def __enter__(self) -> 'AudioRecorder':
        self.vad = webrtcvad.Vad()
        # 设置 VAD 的敏感度。参数是一个 0 到 3 之间的整数。0 表示对非语音最不敏感，3 最敏感。
        self.vad.set_mode(1)

        self.audio = pyaudio.PyAudio()
        self.sample_width = self.audio.get_sample_size(pyaudio.paInt16)
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=self.channels,
                                      rate=self.sample_rate,
                                      input=True,
                                      frames_per_buffer=self.chunk)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def __bytes__(self) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.__frames))
            self.__frames.clear()
        return buf.getvalue()

    def run(self):
        """ Record audio until silence is detected.
        """
        MAXLEN = 30
        watcher = collections.deque(maxlen=MAXLEN)
        triggered, ratio = False, 0.5
        while True:
            frame = self.stream.read(self.frame_size)
            is_speech = self.vad.is_speech(frame, self.sample_rate)
            watcher.append(is_speech)
            self.__frames.append(frame)
            if not triggered:
                num_voiced = len([x for x in watcher if x])
                if num_voiced > ratio * watcher.maxlen:
                    logging.info("start recording...")
                    triggered = True
                    watcher.clear()
                    self.__frames = self.__frames[-MAXLEN:]
            else:
                num_unvoiced = len([x for x in watcher if not x])
                if num_unvoiced > ratio * watcher.maxlen:
                    logging.info("stop recording...")
                    triggered = False
                    Queues.audio.put(bytes(self))
                    logging.info("audio task number: {}".format(
                        Queues.audio.qsize()))


def load_whisper():
    model = WhisperModel(
        model_size_or_path="large-v3",
        device="cuda",
        compute_type="default",
        download_root="../models",
        local_files_only=True
    )


def test():
    try:
        with AudioRecorder(channels=1, sample_rate=16000) as recorder:
            recorder.start()
            recorder.join()

    except KeyboardInterrupt:
        print("KeyboardInterrupt: terminating...")
    except Exception as e:
        logging.error(e, exc_info=True, stack_info=True)

    print("========done")


if __name__ == "__main__":
    print("=======start")
    test()
    print("=======end")
