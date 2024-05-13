import queue


class RParam:
    do_translate: bool
    lang_src: str
    lang_des: str

    sample_rate: int
    sample_width: int
    sample_channels: int


class RTask:

    def __init__(
            self,
            audio,
            sample_rate: int,
            sample_width: int,
            sample_channels: int,
            param=RParam()
    ):
        self.audio = audio
        self.text_transcribe = ""
        self.text_translate = ""
        self.text_info = None

        self.param = param
        self.param.sample_rate = sample_rate
        self.param.sample_width = sample_width
        self.param.sample_channels = sample_channels




class RTaskControl:
    queue_slice = queue.Queue()
    queue_transcribe = queue.Queue()
    queue_translate = queue.Queue()
    queue_render = queue.Queue()
