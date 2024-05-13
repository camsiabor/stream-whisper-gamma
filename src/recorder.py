import os
import typing
import wave
from queue import Queue

import pyaudiowpatch as pyaudio


# import wave
# import os


class ARException(Exception):
    """Base class for AudioRecorder`s exceptions"""


class WASAPINotFound(ARException):
    ...


class InvalidDevice(ARException):
    ...


class AudioRecorder:
    CHUNK_SIZE = 512

    def __init__(self,
                 p_audio: pyaudio.PyAudio = pyaudio.PyAudio(),
                 output_queue: Queue = Queue(),
                 output_channels: int = 1,
                 sample_rate: int = 16000,
                 data_format: int = pyaudio.paInt16,
                 chunk: int = 256,
                 frame_duration: int = 30
                 ):

        self.p = p_audio
        self.output_queue = output_queue
        self.stream = None
        self.device = None

        self.sample_rate = sample_rate
        self.data_format = data_format
        self.output_channels = output_channels
        self.chunk = chunk
        self.frame_size = (sample_rate * frame_duration // 1000)

        self.__frames: typing.List[bytes] = []

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
                    break
            else:
                raise InvalidDevice(
                    "Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available "
                    "devices")

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

        if split:
            self.splitting()

        return self.stream

    def splitting(self):
        pass

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


if __name__ == 'main':
    print("start =========== ")
    p = pyaudio.PyAudio()
    audio_queue = Queue()
    ar = AudioRecorder(
        p_audio=p,
        output_queue=audio_queue,
    )

    help_msg = 30 * "-" + ("\n\n\nStatus:\nRunning=%s | Device=%s | output=%s\n\nCommands:\nlist\nrecord {"
                           "device_index\\default}\npause\ncontinue\nstop {*.wav\\default}\n")

    device_def = ar.get_default_wasapi_device()

    try:
        while True:
            print(help_msg % (
                ar.stream_status, device_def["index"] if device_def is not None else "None"))
            com = input("Enter command: ").split()
            if com[0] == "list":
                p.print_detailed_system_info()
            elif com[0] == "record":
                ar.start_recording()
            elif com[0] == "pause":
                ar.stop_stream()
            elif com[0] == "continue":
                ar.start_stream()
            elif com[0] == "stop":
                ar.close_stream()

                filename = "../temp/a.wav"

                if len(com) > 1 and com[1].endswith(".wav") and os.path.exists(
                        os.path.dirname(os.path.realpath(com[1]))):
                    filename = com[1]

                wave_file = wave.open(filename, 'wb')
                wave_file.setnchannels(ar.output_channels)
                wave_file.setsampwidth(pyaudio.get_sample_size(device_def))
                wave_file.setframerate(int(device_def["defaultSampleRate"]))

                while not audio_queue.empty():
                    wave_file.writeframes(audio_queue.get())
                wave_file.close()

                print(f"The audio is written to a [{filename}]. Exit...")
                break

            else:
                print(f"[{com[0]}] is unknown command")

    except KeyboardInterrupt:
        print("\n\nExit without saving...")
    finally:
        ar.close_stream()
        p.terminate()

    print("end ============= ")
