import os
import traceback

import pyaudiowpatch as pyaudio
import yaml

from src import rtask, rtranscribe, rtranslate, rmanifest, rrecord, rslice

if __name__ == "__main__":

    print("start =========== ")

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    with open('../config/def.yaml', 'r') as config_file:
        cfg = yaml.safe_load(config_file)

    p = pyaudio.PyAudio()

    task_ctrl = rtask.RTaskControl()

    recorder = rrecord.Recorder(
        p_audio=p,
        # 512 works
        task_ctrl=task_ctrl,
        #
        data_format=cfg['recorder'].get('data_format', pyaudio.paInt16),
        # 512 works too
        chunk_size=cfg['recorder'].get('chunk_size', 512),
        # ONLY 10 works in 48000 sample rate
        frame_duration=cfg['recorder'].get('frame_duration', 10),

    )

    slicer = rslice.RSlice(
        task_ctrl=task_ctrl,
        # watcher max len, 10 works pretty well
        slicer_maxlen=cfg['slicer'].get('slicer_maxlen', 10),
        slicer_ratio=cfg['slicer'].get('slicer_ratio', 0.5),
    )

    transcriber = rtranscribe.RTranscriber(
        task_ctrl=task_ctrl,
        # model_size="large-v3",
        model_size=cfg['transcriber'].get('model_size', 'large-v3'),
        local_files_only=cfg['transcriber'].get('local_files_only', False),
        device=cfg['transcriber'].get('device', 'auto'),
        # prompt="hello",
        prompt=cfg['transcriber'].get('prompt', 'hello world'),

    ).init(force=True)

    translater = rtranslate.RTranslator(
        task_ctrl=task_ctrl,
        lang_des=cfg['translater'].get('lang_des', 'en'),
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


