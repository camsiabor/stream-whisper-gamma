import codecs
import logging
import os
import sys

import pyaudiowpatch as pyaudio
import yaml

from src import rlistener
from src.common import sim


def init_logger():
    log_config_path = "../config/log.yaml"
    with open(log_config_path, mode='r', encoding="utf-8") as log_config_file:
        config = yaml.safe_load(log_config_file)
        log_path = sim.get(config, "", "handlers", "file_handler", "filename")
        if not os.path.exists(log_path):
            log_dir_path = os.path.dirname(log_path)
            os.makedirs(log_dir_path, exist_ok=True)
        # noinspection PyUnresolvedReferences
        logging.config.dictConfig(config)

    logging.getLogger("faster_whisper").setLevel(logging.ERROR)


def load_config():
    config_path = "../config/def.yaml"
    if os.path.exists("../config/cfg.yaml"):
        config_path = "../config/cfg.yaml"

    with open(config_path, mode='r', encoding='utf-8') as config_file:
        cfg = yaml.safe_load(config_file)
    return cfg


def init_env():
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    if sys.stdout.encoding != 'cp850':
        sys.stdout = codecs.getwriter('cp850')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'cp850':
        sys.stderr = codecs.getwriter('cp850')(sys.stderr.buffer, 'strict')


if __name__ == "__main__":

    init_env()

    init_logger()
    logger = logging.getLogger('main')
    try:
        cfg = load_config()
        p = pyaudio.PyAudio()
        rlistener = rlistener.RListener(
            cfg=cfg,
            p=p,
        )
        rlistener.start()
        rlistener.join()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: terminating...")
    except Exception as e:
        logger.error(e, exc_info=True, stack_info=True)
