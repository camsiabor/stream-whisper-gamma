
import logging
import os

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
    logging.getLogger("huggingface_hub.file_download").setLevel(logging.INFO)


def load_config():
    config_path = "../config/def.yaml"
    if os.path.exists("../config/cfg.yaml"):
        config_path = "../config/cfg.yaml"

    with open(config_path, mode='r', encoding='utf-8') as config_file:
        cfg = yaml.safe_load(config_file)
    return cfg


def init_env():
    # os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    """
    import sys
    import codecs
    if sys.stdout.encoding != 'cp850':
        sys.stdout = codecs.getwriter('cp850')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'cp850':
        sys.stderr = codecs.getwriter('cp850')(sys.stderr.buffer, 'strict')

    import subprocess
    # Run the 'chcp 65001' command as a subprocess
    subprocess.run('chcp 65001', shell=True)
    """


if __name__ == "__main__":

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
