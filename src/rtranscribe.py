import io
import threading
import traceback
import typing

import codefast as cf
from faster_whisper import WhisperModel

from src import rtask


class RTranscriber(threading.Thread):
    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            model_size: str = "large-v3",
            device: str = "cuda",
            compute_type: str = "default",
            download_root: str = "../models",
            prompt: str = 'Greetings!'
    ) -> None:
        """ FasterWhisper 语音转写

        Args:
            model_size (str): 模型大小，可选项为 "tiny", "base", "small", "medium", "large" 。
                更多信息参考：https://github.com/openai/whisper
            device (str, optional): 模型运行设备。
            compute_type (str, optional): 计算类型。默认为"default"。
            prompt (str, optional): 初始提示。如果需要转写简体中文，可以使用简体中文提示。
        """
        super().__init__()
        self.task_ctrl = task_ctrl

        self.model_size = model_size
        self.download_root = download_root
        self.device = device
        self.compute_type = compute_type
        self.prompt = prompt

        self.do_run = True

        self._model = None

    def init(self, force: bool = False) -> 'RTranscriber':

        if self._model is not None and force is False:
            return self

        local_file_only = True if len(self.download_root) > 0 else False
        self._model = WhisperModel(
            model_size_or_path=self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=self.download_root,
            local_files_only=local_file_only
        )
        return self

    def __enter__(self) -> 'RTranscriber':
        return self.init()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def __call__(self, task: rtask.RTask) -> typing.Generator[str, None, None]:

        segments, info = self._model.transcribe(
            io.BytesIO(task.audio),
            initial_prompt=self.prompt,
            vad_filter=True
        )

        task.text_info = info

        # if info.language != "zh":
        #     return {"error": "transcribe Chinese only"}
        for segment in segments:
            t = segment.text
            if self.prompt in t.strip():
                continue
            if t.strip().replace('.', ''):
                yield t

    def run(self):
        print("[transcriber] running")
        error_count = 0
        while self.do_run:
            try:
                task = self.task_ctrl.queue_transcribe.get()
                text = ''
                for seg in self(task.audio):
                    print(cf.fp.cyan(seg))
                    text += seg
                self.task_ctrl.queue_translate.put(text)
            except Exception:
                traceback.print_exc()
                if error_count > 3:
                    print("[transcriber] error_count > 3, breaking...")
                    break
                error_count += 1
        print("[transcriber] end")
