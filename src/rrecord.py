import logging
import queue
import threading
import time

import pyaudiowpatch as pyaudio
import webrtcvad

from src import rtask


class ARException(Exception):
    """Base class for AudioRecorder`s exceptions"""


class WASAPINotFound(ARException):
    ...


class InvalidDevice(ARException):
    ...


class Recorder(threading.Thread):

    def __init__(self,
                 p_audio: pyaudio.PyAudio,
                 task_ctrl: rtask.RTaskControl,
                 ):

        super().__init__()

        self.p = p_audio

        # 设置 VAD 的敏感度。参数是一个 0 到 3 之间的整数。0 表示对非语音最不敏感，3 最敏感。
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(1)

        self.stream = None
        self.device = None

        self.sample_rate = 48000
        self.data_format = pyaudio.paInt16
        self.output_channels = 0
        self.chunk_size = 512
        self.frame_size = 0

        self.frame_duration = 10

        self.task_ctrl = task_ctrl

        self.output_data = queue.Queue()

        self.frame_cache = []
        self.frame_lock = threading.Lock()
        self.flush_interval = 0.1
        self.flush_thread = None

        self.logger = logging.getLogger('recorder')

        self.configure(self.task_ctrl.cfg)

        self.do_run = True

    def configure(self, cfg: dict):

        r_cfg = cfg.get("recorder", {})

        self.sample_rate = r_cfg.get("sample_rate", 48000)
        self.data_format = r_cfg.get("data_format", pyaudio.paInt16)
        self.chunk_size = r_cfg.get("chunk_size", 512)
        self.flush_interval = r_cfg.get("flush_interval", 0.1)
        self.frame_duration = r_cfg.get("frame_duration", 10)

    def __enter__(self) -> 'Recorder':
        pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close_stream()

    """
    def to_wav(self, path: str = "", clear=True):
        if path is None or len(path) <= 0:
            current_datetime = datetime.datetime.now()
            datetime_string = current_datetime.strftime("%Y%m%d-%H%M%S.%f")[:-3]
            path = f"../temp/{datetime_string}.wav"

        path = os.path.abspath(path)
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        frames = self.get_current_frames()
        with open(path, "wb") as file:
            file.write(frames)

        return path
    """

    def get_default_wasapi_device(self):
        try:  # Get default WASAPI info
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            raise WASAPINotFound("Looks like WASAPI is not available on the system")


        # Get default WASAPI speakers
        sys_default_speakers = self.p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

        if not sys_default_speakers["isLoopbackDevice"]:
            for loopback in self.p.get_loopback_device_info_generator():
                if sys_default_speakers["name"] in loopback["name"]:
                    return loopback
            else:
                raise InvalidDevice(
                    "Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available "
                    "devices")

    def get_sample_width(self):
        return self.p.get_sample_size(self.data_format)

    def get_sample_rate(self):
        if self.sample_rate is None or self.sample_rate <= 0:
            if self.device is not None:
                self.sample_rate = int(self.device["defaultSampleRate"])
        return self.sample_rate

    def get_frame_size(self):
        sample_rate = self.get_sample_rate()
        self.frame_size = (sample_rate * self.frame_duration) // 1000
        return self.frame_size

    def get_sample_channels(self):
        if self.output_channels is None or self.output_channels <= 0:
            if self.device is not None:
                self.output_channels = self.device["maxInputChannels"]
        return self.output_channels

    def stream_callback(self, in_data, frame_count, time_info, status):
        """Write frames and return PA flag"""
        self.output_data.put(in_data)
        return in_data, pyaudio.paContinue

    def init(self):

        self.close_stream()

        if self.device is None:
            self.device = self.get_default_wasapi_device()

        device_index = self.device["index"]
        device_channels = self.get_sample_channels()
        sample_rate = self.get_sample_rate()

        # self.p.print_detailed_system_info()

        self.logger.info(f"init | device: {self.device}")

        self.stream = self.p.open(format=self.data_format,
                                  channels=device_channels,
                                  rate=sample_rate,
                                  frames_per_buffer=self.chunk_size,
                                  input=True,
                                  input_device_index=device_index,
                                  # stream_callback=stream_callback
                                  )

        return self.stream

    def flush(self, callback=None):

        sample_rate = self.get_sample_rate()
        sample_width = self.get_sample_width()
        sample_channels = self.get_sample_channels()

        while self.do_run:
            time.sleep(self.flush_interval)

            all_frames = None
            self.frame_lock.acquire()
            try:
                if len(self.frame_cache) <= 0:
                    continue

                all_frames = b''.join(self.frame_cache)
                self.frame_cache = []
            finally:
                self.frame_lock.release()

            if all_frames is None or len(all_frames) <= 0:
                continue

            self.to_slice(all_frames, sample_rate, sample_width, sample_channels, callback)

    def to_slice(
            self,
            frame,
            sample_rate,
            sample_width,
            sample_channels,
            callback=None
    ):

        task = rtask.RTask(
            audio=frame,
            sample_rate=sample_rate,
            sample_width=sample_width,
            sample_channels=sample_channels,
        )

        if callback is not None:
            r = callback(frame, task)
            if r is not None and r is False:
                return

        self.task_ctrl.queue_slice.put(task)

    def record(self, callback=None):

        self.do_run = True

        if self.flush_interval > 0:
            self.flush_thread = threading.Thread(target=self.flush, args=(callback,))
            self.flush_thread.start()

        frame_size = self.get_frame_size()
        sample_rate = self.get_sample_rate()
        sample_width = self.get_sample_width()
        sample_channels = self.get_sample_channels()
        while self.do_run:
            frame = self.stream.read(frame_size, exception_on_overflow=False)
            if not frame:
                continue

            if self.flush_interval > 0:
                self.frame_lock.acquire()
                try:
                    self.frame_cache.append(frame)
                finally:
                    self.frame_lock.release()
                continue

            self.to_slice(frame, sample_rate, sample_width, sample_channels, callback)

        self.do_run = False

    def run(self):
        self.logger.info("running")
        try:
            if self.stream is None:
                self.init()
            self.record()
        except Exception as e:
            self.logger.error(e, exc_info=True, stack_info=True)
        finally:
            self.logger.info("end")

    def stop_stream(self):
        self.stream.stop_stream()

    def start_stream(self):
        self.stream.start_stream()

    def close_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    @property
    def stream_status(self):
        return "closed" if self.stream is None else "stopped" if self.stream.is_stopped() else "running"
