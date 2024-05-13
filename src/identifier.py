import threading

from faster_whisper import WhisperModel


class Transcriber(threading.Thread):
    def __init__(
            self,
            model_size: str,
            device: str = "auto",
            compute_type: str = "default",
            prompt: str = '实时/低延迟语音转写服务，林黛玉、倒拔、杨柳树、鲁迅、周树人、关键词、转写正确') -> None:
        """ FasterWhisper 语音转写

        Args:
            model_size (str): 模型大小，可选项为 "tiny", "base", "small", "medium", "large" 。
                更多信息参考：https://github.com/openai/whisper
            device (str, optional): 模型运行设备。
            compute_type (str, optional): 计算类型。默认为"default"。
            prompt (str, optional): 初始提示。如果需要转写简体中文，可以使用简体中文提示。
        """
        super().__init__()
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.prompt = prompt

    def __enter__(self) -> 'Transcriber':

        """
        self._model = WhisperModel(self.model_size,
                                   device=self.device,
                                   compute_type=self.compute_type,
                                   )
        """

        self._model = WhisperModel(
            model_size_or_path="large-v3",
            device="cuda",
            compute_type="default",
            download_root="../models",
            local_files_only=True
        )

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def __call__(self, audio: bytes) -> typing.Generator[str, None, None]:
        segments, info = self._model.transcribe(BytesIO(audio),
                                                initial_prompt=self.prompt,
                                                vad_filter=True)
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
            audio = Queues.audio.get()
            text = ''
            for seg in self(audio):
                logging.info(cf.fp.cyan(seg))
                text += seg
            Queues.text.put(text)
