import asyncio
import logging
import threading
import traceback

import cutlet

from src import rtask
from src.common import sim
from src.service import poe_ctrl, ollama_ctrl
from src.service.google import google_trans


class RTranslator(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            lang_des: str = "en",
    ):
        super().__init__()

        self.cfg = cfg = task_ctrl.cfg

        self.task_ctrl = task_ctrl
        self.do_run = True
        self.lang_des = lang_des

        self.agent_google = None

        self.phoneme_convert = False

        self.agent_poe = poe_ctrl.PoeCtrl(cfg)
        self.agent_ollama = ollama_ctrl.OllamaCtrl(cfg)
        self.agent_google = google_trans.GoogleTransCtrl(cfg)
        self.logger = logging.getLogger('translator')

        self.configure()

    def configure(self):
        trans_cfg = self.task_ctrl.cfg.get("translator", {})
        phoneme_cfg = trans_cfg.get("phoneme", {})
        self.phoneme_convert = sim.get(phoneme_cfg, False, "convert")

        self.configure_poe(self.cfg)
        self.configure_ollama(self.cfg)
        self.configure_google(self.cfg)

    def configure_google(self, cfg):
        active = sim.get(cfg, False, "translator", "agent_google", "active")
        if not active:
            return
        self.agent_google.configure()

    def configure_poe(self, cfg):
        active = sim.get(cfg, False, "translator", "agent_poe", "active")
        if not active:
            return
        self.agent_poe.configure("translate")

    def configure_ollama(self, cfg):
        active = sim.get(cfg, False, "translator", "agent_ollama", "active")
        if not active:
            return
        self.agent_ollama.configure("translate")

    # noinspection PyMethodMayBeStatic
    def phoneme(self, task: rtask.RTask):
        text = task.text_transcribe
        if text is None or len(text) <= 0:
            return text
        lang_src = task.text_info.language.lower()
        if lang_src == "ja":
            katsu = cutlet.Cutlet()
            task.text_phoneme = katsu.romaji(text)

        return text

    async def translate(self, text, lang_src, task):
        if lang_src == self.lang_des:
            return text

        ret = ""

        if len(ret) <= 0 and self.agent_ollama.active:
            try:
                ret = await self.agent_ollama.translate(text, lang_src, self.lang_des)
            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)

        if len(ret) <= 0 and self.agent_poe.active:
            try:
                ret = self.agent_poe.translate(text, lang_src, self.lang_des)
            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)

        if len(ret) <= 0 and self.agent_google is not None:
            ret = self.agent_google.translate(text, lang_src, self.lang_des)

        return ret

    async def warmup(self):
        try:
            if self.agent_ollama.active:
                await self.agent_ollama.warmup("translate")
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)

        try:
            if self.agent_poe.active:
                self.agent_poe.warmup("translate")
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)

    @staticmethod
    def result_handle(result):
        if result is None:
            return None
        if isinstance(result, tuple) and len(result) > 0:
            result = result[0]
        if isinstance(result, str) and len(result) > 0:
            result = result.strip()
        return result

    async def cycle(self):
        self.logger.info("running")
        error_count = 0

        try:
            await self.warmup()
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)

        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_translate.get()
                if task.text_transcribe is None or len(task.text_transcribe) <= 0:
                    continue

                task.param.lang_des = self.lang_des

                if self.phoneme_convert is True:
                    self.phoneme(task)

                result = await self.translate(
                    task.text_transcribe,
                    task.text_info.language,
                    task,
                )

                result = self.result_handle(result)
                if result is None:
                    continue
                task.text_translate = result
                task.info.time_set("translate")
                task.info.time_diff("transcribe", "translate", store="translate")
                self.task_ctrl.queue_manifest.put(task)
            except Exception:
                traceback.print_exc()
                if error_count > 100:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1
        self.logger.info("end")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.cycle())
        loop.close()
