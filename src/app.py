import logging
import os

import pyaudiowpatch as pyaudio

from src import rlistener
from src.common.sim import LogUtil, ConfigUtil


def init_logger():
    log_config_path = "./config/log.yaml"
    LogUtil.load_yaml(log_config_path)
    logging.getLogger("faster_whisper").setLevel(logging.ERROR)
    logging.getLogger("huggingface_hub.file_download").setLevel(logging.INFO)


def load_config():
    return ConfigUtil.load_yaml("./config/def.yaml", "./config/cfg.yaml")


def init_env():
    # os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


if __name__ == "__main__":

    print(f"[app] working directory {os.getcwd()}")

    init_env()
    init_logger()

    logger = logging.getLogger('main')

    try:
        cfg = load_config()
        py_audio = pyaudio.PyAudio()
        rlistener = rlistener.RListener(
            cfg=cfg,
            py_audio=py_audio,
        )
        rlistener.start()
        rlistener.gui_mainloop()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: terminating...")
    except Exception as e:
        logger.error(e, exc_info=True, stack_info=True)
