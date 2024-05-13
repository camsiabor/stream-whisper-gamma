import os
import traceback

import pyaudiowpatch as pyaudio

from src import rtask, rtranscribe, rtranslate, rmanifest, rrecord, rslice

if __name__ == "__main__":

    print("start =========== ")

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    p = pyaudio.PyAudio()

    task_ctrl = rtask.RTaskControl()

    recorder = rrecord.Recorder(
        p_audio=p,
        # 512 works
        task_ctrl=task_ctrl,
        # 512 works too
        chunk_size=4096,
        # ONLY 10 works
        frame_duration=10,
    )

    slicer = rslice.RSlice(
        task_ctrl=task_ctrl,
        # watcher max len, 10 works pretty well
        slicer_maxlen=10,
        slicer_ratio=0.5,
    )

    transcriber = rtranscribe.RTranscriber(
        task_ctrl=task_ctrl,
        device="cuda",
    ).init(force=True)

    translater = rtranslate.RTranslater(
        task_ctrl=task_ctrl,
    )

    renderer = rmanifest.RManifest(
        task_ctrl=task_ctrl,
    )

    try:

        renderer.start()
        translater.start()
        transcriber.start()
        recorder.start()

        while True:
            com = input("Enter command: ").split()
            if com[0] == "exit":
                recorder.do_run = False
                transcriber.do_run = False
                translater.do_run = False
                renderer.do_run = False
                break

        recorder.join()
        transcriber.join()
        translater.join()
        renderer.join()

    except KeyboardInterrupt:
        print("KeyboardInterrupt: terminating...")
    except Exception as e:
        traceback.print_exc()
        # logging.error(e, exc_info=True, stack_info=True)

"""
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

"""
