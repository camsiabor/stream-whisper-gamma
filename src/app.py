import os
import traceback

import pyaudiowpatch as pyaudio
import yaml

from src import rlistener

if __name__ == "__main__":

    print("start =========== ")

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    with open('../config/def.yaml', mode='r', encoding='utf-8') as config_file:
        cfg = yaml.safe_load(config_file)

    p = pyaudio.PyAudio()

    rlistener = rlistener.RListener(
        cfg=cfg,
        p=p,
    )

    try:
        rlistener.start()
        rlistener.join()
    except KeyboardInterrupt:
        print("KeyboardInterrupt: terminating...")
    except Exception as e:
        traceback.print_exc()
        # logging.error(e, exc_info=True, stack_info=True)


