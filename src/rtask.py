import queue


class RParam:
    do_translate: bool
    lang_src: str
    lang_des: str

    sample_rate: int
    sample_width: int
    sample_channels: int


class RCommand:

    def __init__(
            self,
            action: str,
            params: dict = None,
            extra=None,
    ):
        self.action = action
        self.params = params
        self.extra = extra



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

        self.text_start = "",
        self.text_end = "",

        self.param = param
        self.param.sample_rate = sample_rate
        self.param.sample_width = sample_width
        self.param.sample_channels = sample_channels


class RTaskControl:
    queue_command = queue.Queue()
    queue_slice = queue.Queue()
    queue_transcribe = queue.Queue()
    queue_translate = queue.Queue()
    queue_manifest = queue.Queue()

    def __init__(self):
        pass

    def end_all(self):
        self.queue_command.put("exit")
        self.queue_slice.put(None)
        self.queue_transcribe.put(None)
        self.queue_translate.put(None)
        self.queue_manifest.put(None)
        pass
