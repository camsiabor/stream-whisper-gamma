import io
import logging
import threading
import traceback
import typing

from faster_whisper import WhisperModel

from src import rtask
from src.common import sim


# import cutlet

class RTranscriber(threading.Thread):
    lang_src: str
    beam_size: int
    model_size: str
    download_root: str
    local_files_only: bool
    device: str
    compute_type: str
    prompt: str

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            index: int = 1,
    ) -> None:
        super().__init__()

        self.task_ctrl = task_ctrl
        self.index = index

        self.do_run = True
        self.model = None

        self.logger = logging.getLogger(f'transcriber-{self.index}')
        self.configure()

    """ FasterWhisper 语音转写
            Args:
                model_size (str): 模型大小，可选项为 "tiny", "base", "small", "medium", "large" 。
                    更多信息参考：https://github.com/openai/whisper
                device (str, optional): 模型运行设备。
                compute_type (str, optional): 计算类型。默认为"default"。
                prompt (str, optional): 初始提示。如果需要转写简体中文，可以使用简体中文提示。
            """

    def configure(self) -> 'RTranscriber':
        cfg = sim.getv(self.task_ctrl.cfg, {}, "transcriber")
        self.lang_src = sim.getv(cfg, None, "lang_src")
        self.beam_size = sim.getv(cfg, 5, "beam_size")
        self.model_size = sim.getv(cfg, "large-v3", "model_size")
        self.download_root = sim.getv(cfg, "./models", "download_root")
        self.local_files_only = sim.getv(cfg, True, "local_files_only")
        self.device = sim.getv(cfg, "cuda", "device")
        self.compute_type = sim.getv(cfg, "default", "compute_type")
        self.prompt = sim.getv(cfg, "transcriber here", "prompt")
        return self

    def init(self, force: bool = False) -> 'RTranscriber':
        if self.model is not None and force is False:
            return self
        # local_file_only = True if len(self.download_root) > 0 else False
        self.model = WhisperModel(
            model_size_or_path=self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=self.download_root,
            local_files_only=self.local_files_only
        )
        return self

    def __enter__(self) -> 'RTranscriber':
        return self.init()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def process(self, task: rtask.RTask) -> typing.Generator[str, None, None]:

        data = task.audio

        segments, info = self.model.transcribe(
            audio=io.BytesIO(data),
            # the pathes explored by the beam search
            beam_size=self.beam_size,
            # language
            # language=self.lang_src,
            #
            initial_prompt=self.prompt,
            #
            vad_filter=True
        )

        task.text_info = info

        # if info.language != "zh":
        #     return {"error": "transcribe Chinese only"}
        for segment in segments:
            t = segment.text
            task.text_start = segment.start
            task.text_end = segment.end
            if self.prompt in t.strip():
                continue
            if t.strip().replace('.', ''):
                yield t
        pass

    ignore_list_single = [
        "♪"
    ]

    ignore_list_pair = [
        ("(", ")"), ("[", "]"), ("*", "*"),
        ("（", "）"), ("【", "】"), ("［", "］"),
    ]

    def ignore(self, text):
        head = text[0]
        if head in self.ignore_list_single:
            return True
        tail = text[-1]
        for pair in self.ignore_list_pair:
            if head == pair[0] and tail == pair[1]:
                return True
        return False

    def run(self):
        self.logger.info(f"running | source language: {self.lang_src} | model: {self.model_size}")
        error_count = 0
        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_transcribe.get()
                if task.audio is None:
                    continue

                # text = codefast.fp.cyan('')
                text = ''
                for seg in self.process(task):
                    text += seg
                    # text += codefast.fp.cyan(seg)

                text = text.strip()
                if len(text) <= 0:
                    continue

                if self.ignore(text):
                    self.logger.info("ignore text: %s" % text)
                    continue

                task.text_transcribe = text
                task.info.time_set("transcribe")
                task.info.time_diff("slice", "transcribe", store="transcribe")
                self.task_ctrl.queue_translate.put(task)
            except Exception:
                traceback.print_exc()
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1
        self.logger.info("[transcriber] end")
