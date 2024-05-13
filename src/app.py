import os
import wave

import pyaudiowpatch as pyaudio

from src.recorder import Recorder

if __name__ == "__main__":
    print("start =========== ")
    p = pyaudio.PyAudio()

    ar = Recorder(
        p_audio=p,
        # 512 works
        chunk_size=4096,
        # ONLY 10 works
        frame_duration=15,
        # watcher max len, 10 works pretty well
        watcher_maxlen=10,
    )

    help_msg = 30 * "-" + ("\n\n\nStatus:\nRunning=%s | Device=%s | output=%s\n\nCommands:\nlist\nrecord {"
                           "device_index\\default}\npause\ncontinue\nstop {*.wav\\default}\n")

    device_def = ar.get_default_wasapi_device()

    try:
        while True:
            print(help_msg % (
                ar.stream_status, device_def["index"] if device_def is not None else "None", ""))
            com = input("Enter command: ").split()
            if com[0] == "list":
                p.print_detailed_system_info()
            elif com[0] == "record":
                ar.start_recording(None, True)
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
                wave_file.setnchannels(ar.get_output_channels())
                wave_file.setsampwidth(ar.get_sample_width())
                wave_file.setframerate(ar.get_sample_rate())

                while not ar.output_queue.empty():
                    wave_file.writeframes(ar.output_queue.get())
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
