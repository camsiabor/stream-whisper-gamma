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
        model_size="zh-plus/faster-whisper-large-v2-japanese-5k-steps",
        local_files_only=True,
        device="cuda",
        # prompt="hello",
        prompt="こんにちは",

    ).init(force=True)

    translater = rtranslate.RTranslator(
        task_ctrl=task_ctrl,
        lang_des="zh",
    )

    renderer = rmanifest.RManifest(
        task_ctrl=task_ctrl,
    )

    try:

        renderer.start()
        translater.start()
        transcriber.start()
        slicer.start()
        recorder.start()

        while True:
            com = input("Enter command: ").split()
            if len(com) <= 0:
                continue
            if com[0] == "exit":
                recorder.do_run = False
                slicer.do_run = False
                transcriber.do_run = False
                translater.do_run = False
                renderer.do_run = False
                break

        recorder.join()
        slicer.join()
        transcriber.join()
        translater.join()
        renderer.join()

    except KeyboardInterrupt:
        print("KeyboardInterrupt: terminating...")
    except Exception as e:
        traceback.print_exc()
        # logging.error(e, exc_info=True, stack_info=True)


