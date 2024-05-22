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

    # noinspection PyTypeChecker
    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            index: int = 1,
    ):
        super().__init__()

        self.task_ctrl = task_ctrl
        self.index = index
        self.do_run = True

        self.agent_poe: poe_ctrl.PoeCtrl = None
        self.agent_ollama: ollama_ctrl.OllamaCtrl = None
        self.agent_google: google_trans.GoogleTransCtrl = None

        self.phoneme_ja: cutlet.Cutlet = None

        self.lang_des = "en"

        self.phoneme = {
            "convert": False,
            "translate": False,
        }

        self.cache_redis = {
            "fetch": 0,
            "persist": 0,
        }

        self.logger = logging.getLogger(f'translator-{self.index}')
        self.configure()
        pass

    def configure(self):
        cfg = self.task_ctrl.cfg

        trans_cfg = self.task_ctrl.cfg.get("translator", {})
        self.lang_des = trans_cfg.get('lang_des', 'en')

        self.configure_poe(cfg)
        self.configure_ollama(cfg)
        self.configure_google(cfg)

        self.configure_phoneme(cfg)
        self.configure_cache_redis(cfg)
        pass

    def configure_phoneme(self, cfg):
        phoneme_cfg = sim.getv(cfg, {}, "translator", "phoneme")
        convert = sim.getv(phoneme_cfg, False, "convert")
        self.phoneme = {
            "convert": convert,
            "translate": sim.getv(phoneme_cfg, False, "translate"),
        }
        if convert:
            self.phoneme_ja = cutlet.Cutlet()
        pass

    def configure_cache_redis(self, cfg):
        cache_redis_cfg = sim.getv(cfg, {}, "translator", "cache_redis")
        fetch = sim.getv(cache_redis_cfg, False, "fetch")
        persist = sim.getv(cache_redis_cfg, False, "persist")
        if (fetch <= 0) and (persist <= 0):
            return
        if self.task_ctrl.redis is None:
            self.logger.error("redis client is not available, cache_redis is disabled.")
            return
        self.cache_redis = {
            "fetch": fetch,
            "persist": persist,
        }
        pass

    def configure_google(self, cfg):
        active = sim.getv(cfg, False, "translator", "agent_google", "active")
        if not active:
            return
        self.agent_google = google_trans.GoogleTransCtrl(self.task_ctrl.cfg)
        self.agent_google.configure()

    def configure_poe(self, cfg):
        active = sim.getv(cfg, False, "translator", "agent_poe", "active")
        if not active:
            return
        self.agent_poe = poe_ctrl.PoeCtrl(self.task_ctrl.cfg)
        self.agent_poe.configure("translate")

    def configure_ollama(self, cfg):
        active = sim.getv(cfg, False, "translator", "agent_ollama", "active")
        if not active:
            return
        self.agent_ollama = ollama_ctrl.OllamaCtrl(self.task_ctrl.cfg)
        self.agent_ollama.configure("translate")

    # noinspection PyMethodMayBeStatic
    def phoneme_handle(self, task: rtask.RTask):
        if not self.phoneme.get("convert", False):
            return ""

        text = task.text_transcribe
        if text is None or len(text) <= 0:
            return ""

        lang_src = task.text_info.language.lower()
        if lang_src == "ja" and self.phoneme_ja is not None:
            task.text_phoneme = self.phoneme_ja.romaji(text)

        if task.text_phoneme is None or len(task.text_phoneme) <= 0:
            return task.text_phoneme

        if self.phoneme.get("translate", False):
            task.text_translate = task.text_translate + " | " + task.text_phoneme

        return task.text_phoneme

    async def translate(self, text, lang_src):
        if lang_src == self.lang_des:
            return text

        ret = ""

        if len(ret) <= 0 and self.agent_ollama is not None:
            try:
                ret = await self.agent_ollama.translate(text, lang_src, self.lang_des)
            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)

        if len(ret) <= 0 and self.agent_poe is not None:
            try:
                ret = self.agent_poe.translate(text, lang_src, self.lang_des)
            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)

        if len(ret) <= 0 and self.agent_google is not None:
            ret = self.agent_google.translate(text, lang_src, self.lang_des)

        return ret

    async def warmup(self):
        try:
            if self.agent_ollama is not None and self.agent_ollama.active:
                await self.agent_ollama.warmup("translate")
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)

        try:
            if self.agent_poe is not None and self.agent_poe.active:
                self.agent_poe.warmup("translate")
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)

    @staticmethod
    def result_adapt(result):
        if result is None:
            return None
        if isinstance(result, tuple) and len(result) > 0:
            result = result[0]
        if isinstance(result, str) and len(result) > 0:
            result = result.strip()
        return result

    def cache_fetch(self, task):
        translated = ""
        transcribe_len = len(task.text_transcribe)
        redis_fetch = self.cache_redis.get("fetch", 0)
        lang_key = f"{task.text_info.language}_{self.lang_des}"

        if redis_fetch > 0 and transcribe_len <= redis_fetch:
            redis_ret = self.task_ctrl.redis.hmget(lang_key, task.text_transcribe)
            if redis_ret is not None and len(redis_ret) > 0:
                byte_data = redis_ret[0]
                if byte_data is not None and len(byte_data) > 0:
                    translated = byte_data.decode("utf-8")

        cached = translated is not None and len(translated) > 0
        if cached:
            self.logger.info(f"cache_fetch {lang_key} | {task.text_transcribe} -> {translated}")

        return translated, cached

    def cache_persist(self, translated, task):

        if translated is None:
            return

        translated_len = len(translated)
        if translated_len <= 0:
            return

        if task.text_info.language == self.lang_des:
            return

        transcribe_len = len(task.text_transcribe)

        redis_persist = self.cache_redis.get("persist", 0)

        if redis_persist > 0 and transcribe_len <= redis_persist:
            lang_key = f"{task.text_info.language}_{self.lang_des}"
            self.task_ctrl.thread_pool.submit(
                self.task_ctrl.redis.hset,
                lang_key,
                task.text_transcribe,
                translated
            )
            # self.task_ctrl.redis.hset(lang_key, task.text_transcribe, translated)
            self.logger.info(f"cache_persist {lang_key} | {task.text_transcribe} -> {translated}")
            pass

        pass

    async def cycle(self):
        self.logger.info("running | destined language: %s" % self.lang_des)
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

                translated = None
                cached = False
                if task.text_info.language == self.lang_des:
                    translated = task.text_transcribe
                    cached = True

                self.phoneme_handle(task)

                if not cached:
                    translated, cached = self.cache_fetch(task)

                if not cached:
                    translated = await self.translate(
                        task.text_transcribe,
                        task.text_info.language,
                    )

                translated = self.result_adapt(translated)
                if translated is None:
                    continue

                if not cached:
                    self.cache_persist(translated, task)

                task.text_translate = translated
                task.info.time_set("translate")
                task.info.time_diff("transcribe", "translate", store="translate")
                task.param.lang_src = task.text_info.language
                task.param.lang_des = self.lang_des
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
