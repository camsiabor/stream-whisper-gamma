import os
import wave

import pyaudiowpatch as pyaudio

from src import rqueue, rtrans
from src.recorder import Recorder

if __name__ == "__main__":
    print("start =========== ")
    p = pyaudio.PyAudio()

    task_queue = rqueue.RQueue()

    recorder = Recorder(
        p_audio=p,
        # 512 works
        task_queue=task_queue,
        # 512 works too
        chunk_size=4096,
        # ONLY 10 works
        frame_duration=15,
        # watcher max len, 10 works pretty well
        watcher_maxlen=10,
    )

    transcriber = rtrans.RTranscriber(

        task_queue=task_queue,
    )

    help_msg = 30 * "-" + ("\n\n\nStatus:\nRunning=%s | Device=%s | output=%s\n\nCommands:\nlist\nrecord {"
                           "device_index\\default}\npause\ncontinue\nstop {*.wav\\default}\n")

    device_def = recorder.get_default_wasapi_device()

    try:
        while True:
            print(help_msg % (
                recorder.stream_status, device_def["index"] if device_def is not None else "None", ""))
            com = input("Enter command: ").split()
            if com[0] == "list":
                p.print_detailed_system_info()
            elif com[0] == "record":
                recorder.start_recording(None, True)
            elif com[0] == "pause":
                recorder.stop_stream()
            elif com[0] == "continue":
                recorder.start_stream()
            elif com[0] == "stop":
                recorder.close_stream()

                filename = "../temp/a.wav"

                if len(com) > 1 and com[1].endswith(".wav") and os.path.exists(
                        os.path.dirname(os.path.realpath(com[1]))):
                    filename = com[1]

                wave_file = wave.open(filename, 'wb')
                wave_file.setnchannels(recorder.get_output_channels())
                wave_file.setsampwidth(recorder.get_sample_width())
                wave_file.setframerate(recorder.get_sample_rate())

                while not recorder.output_queue.empty():
                    wave_file.writeframes(recorder.output_queue.get())
                wave_file.close()

                print(f"The audio is written to a [{filename}]. Exit...")
                break

            else:
                print(f"[{com[0]}] is unknown command")

    except KeyboardInterrupt:
        print("\n\nExit without saving...")
    finally:
        recorder.close_stream()
        p.terminate()

    print("end ============= ")
