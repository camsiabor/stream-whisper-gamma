import queue


class RParam:
    do_translate: bool
    lang_src: str
    lang_des: str


class RTask:

    def __init__(
            self,
            audio,
            param=RParam()
    ):
        self.audio = audio
        self.text_src = ""
        self.text_des = ""
        self.param = param


class RTaskControl:
    queue_record = queue.Queue()
    queue_transcribe = queue.Queue()
    queue_translate = queue.Queue()
    queue_render = queue.Queue()
