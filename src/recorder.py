import typing
from queue import Queue

import pyaudiowpatch as pyaudio


# import wave
# import os

# filename = "loopback_record_class.wav"
# data_format = pyaudio.paInt24


class ARException(Exception):
    """Base class for AudioRecorder`s exceptions"""


class WASAPINotFound(ARException):
    ...


class InvalidDevice(ARException):
    ...


class AudioRecorder:
    CHUNK_SIZE = 512

    def __init__(self,
                 p_audio: pyaudio.PyAudio,
                 output_queue: Queue,
                 channels: int = 1,
                 sample_rate: int = 16000,
                 data_format: int = pyaudio.paInt16,
                 chunk: int = 256,
                 frame_duration: int = 30
                 ):

        if p_audio is None:
            p_audio = pyaudio.PyAudio()

        self.p = p_audio
        self.output_queue = output_queue
        self.stream = None
        self.device = None

        self.sample_rate = sample_rate
        self.data_format = data_format
        self.channels = channels
        self.chunk = chunk
        self.frame_size = (sample_rate * frame_duration // 1000)

        self.__frames: typing.List[bytes] = []

    @staticmethod
    def get_default_wasapi_device(p_audio: pyaudio.PyAudio):

        try:  # Get default WASAPI info
            wasapi_info = p_audio.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            raise WASAPINotFound("Looks like WASAPI is not available on the system")

        # Get default WASAPI speakers
        sys_default_speakers = p_audio.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

        if not sys_default_speakers["isLoopbackDevice"]:
            for loopback in p_audio.get_loopback_device_info_generator():
                if sys_default_speakers["name"] in loopback["name"]:
                    return loopback
                    break
            else:
                raise InvalidDevice(
                    "Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available devices")

    def callback(self, in_data, frame_count, time_info, status):
        """Write frames and return PA flag"""
        self.output_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def start_recording(self, target_device: dict, split: bool = True):

        self.close_stream()

        if target_device is None:
            target_device = self.get_default_wasapi_device(self.p)

        self.device = target_device

        stream_callback = split if None else self.callback

        self.stream = self.p.open(format=self.data_format,
                                  channels=target_device["maxInputChannels"],
                                  rate=int(target_device["defaultSampleRate"]),
                                  frames_per_buffer=self.CHUNK_SIZE,
                                  input=True,
                                  input_device_index=target_device["index"],
                                  stream_callback=stream_callback
                                  )

        if not split:
            return self.stream

        return self.stream

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
