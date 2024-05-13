import io
import threading
import typing

import codefast as cf
from faster_whisper import WhisperModel

from src import rqueue


class RTranscriber(threading.Thread):
    def __init__(
            self,
            task_queue: rqueue.RQueue,
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
        self.task_queue = task_queue

        self.model_size = model_size
        self.download_root = download_root
        self.device = device
        self.compute_type = compute_type
        self.prompt = prompt

    def __enter__(self) -> 'RTranscriber':

        local_file_only = True if len(self.download_root) > 0 else False
        self._model = WhisperModel(
            model_size_or_path=self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=self.download_root,
            local_files_only=local_file_only
        )

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def __call__(self, audio: bytes) -> typing.Generator[str, None, None]:

        segments, info = self._model.transcribe(
            io.BytesIO(audio),
            initial_prompt=self.prompt,
            vad_filter=True
        )

        # if info.language != "zh":
        #     return {"error": "transcribe Chinese only"}
        for segment in segments:
            t = segment.text
            if self.prompt in t.strip():
                continue
            if t.strip().replace('.', ''):
                yield t

    def run(self):
        while True:
            audio = self.task_queue.audio.get()
            text = ''
            for seg in self(audio):
                print(cf.fp.cyan(seg))
                text += seg
            self.task_queue.text.put(text)
