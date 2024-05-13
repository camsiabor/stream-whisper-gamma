import pyaudio

import sounddevice as sd
import numpy as np
import soundfile as sf
import scipy.io.wavfile as wavfile

import pyaudiowpatch

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 10
OUTPUT_FILENAME = "../temp/pyaudio.wav"


def run():
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    for i in range(device_count):
        print(p.get_device_info_by_index(i))

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK,
                    # input_host_api_specific_stream_info=p.get_default_output_device_info()["hostApi"],
                    # as_loopback=True
                    )

    print("Recording system audio...")
    frames = []
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio to a file (e.g., "output.wav")
    with open(OUTPUT_FILENAME, "wb") as wf:
        wf.write(b"".join(frames))


def run2():
    # Set your desired parameters
    duration = 7  # Recording duration in seconds
    fs = 44100  # Sample rate

    # Record audio
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait for recording to finish

    # Save the recorded audio to a file (e.g., "output.wav")
    # sf.write("../temp/sounddevice.wav", recording, fs)

    wavfile.write("../temp/sd.wav", fs, recording)


def run3():
    devices = sd.query_devices(None, "output")
    print(devices)


def run4():
    p = pyaudiowpatch.PyAudio()
    device_count = p.get_device_count()
    for i in range(device_count):
        print(p.get_device_info_by_index(i))

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    # output=True,
                    frames_per_buffer=CHUNK,
                    # input_host_api_specific_stream_info=p.get_default_output_device_info()["hostApi"],
                    # as_loopback=True
                    )

    print("Recording system audio...")
    frames = []
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio to a file (e.g., "output.wav")
    with open("../temp/watch.wav", "wb") as wf:
        wf.write(b"".join(frames))


def device_list():
    p = pyaudiowpatch.PyAudio()
    for i in range(p.get_device_count()):
        print(p.get_device_info_by_index(i))




def run_mix():
    print("run mix")


if __name__ == '__main__':
    print("[dev] start")
    # run2()
    device_list()
    print("[dev] end")
