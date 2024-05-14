import threading
import traceback

import poe_api_wrapper

import src.service.google.translator
from src import rtask
from src.common import sim, lang


class RTranslator(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            lang_des: str = "en",
    ):
        super().__init__()

        cfg = task_ctrl.cfg
        cfg_trans = cfg["translator"]
        if cfg is None:
            cfg_trans = []

        self.task_ctrl = task_ctrl
        self.do_run = True
        self.lang_des = lang_des

        self.agent_google = None

        self.agent_poe = None
        self.agent_poe_map = {}

        self.configure_poe(cfg)
        self.configure_google(cfg)

    def configure_google(self, cfg):
        google_cfg = sim.get(cfg, None, "translator", "agent_google")
        if google_cfg is None:
            return
        if not sim.get(google_cfg, True, "active"):
            return
        domain = sim.get(google_cfg, "hk", "domain")
        timeout = sim.get(google_cfg, 5, "timeout")
        self.agent_google = src.service.google.translator.GoogleTranslator(
            url_suffix=domain,
            timeout=timeout,
        )

    def configure_poe(self, cfg):
        agent_cfg = sim.get(cfg, None, "translator", "agent_poe")
        if agent_cfg is None:
            return
        if not sim.get(agent_cfg, True, "active"):
            return

        poe_cfg = sim.get(cfg, None, "poe")
        token = sim.get(poe_cfg, None, "token")
        if token is None:
            print("[translator] poe token not found !")
            return

        self.agent_poe = poe_api_wrapper.PoeApi(
            cookie=token
        )

        bot_map = sim.get(poe_cfg, None, "translate")
        if bot_map is None:
            print("[translator] poe translate bot not found !")
            return
        self.agent_poe_map = bot_map

    def poe_get_bot_id(self, lang):
        bot_id = self.agent_poe_map.get(lang, None)
        if bot_id is not None:
            return bot_id
        return self.agent_poe_map.get("all")

    def translate_poe(self, text, lang_src):
        bot_id = self.poe_get_bot_id(lang_src)

        src_name = lang.LANGUAGES[lang_src]
        des_name = lang.LANGUAGES[self.lang_des]

        question = f"from {src_name} to {des_name}: {text}"
        res = self.agent_poe.send_message(
            bot_id, question
        )

        if res is None:
            raise Exception("[translator] poe response is None")

        chunk = None
        for chunk in res:
            pass
        return chunk["text"]

    def translate_google(self, text, lang_src):
        return self.agent_google.translate(
            text, self.lang_des, lang_src
        )

    def translate(self, text, lang_src, task):
        if lang_src == self.lang_des:
            return text

        ret = ""

        if len(ret) <= 0 and self.agent_poe is not None:
            try:
                ret = self.translate_poe(text, lang_src)
            except Exception:
                traceback.print_exc()

        if len(ret) <= 0 and self.agent_google is not None:
            ret = self.translate_google(text, lang_src)

        return ret

    def run(self):
        print("[translator] running")
        error_count = 0
        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_translate.get()
                if task.text_transcribe is None or len(task.text_transcribe) <= 0:
                    continue

                task.text_translate = self.translate(
                    task.text_transcribe,
                    task.text_info.language,
                    task,
                )

                self.task_ctrl.queue_manifest.put(task)
            except Exception:
                traceback.print_exc()
                if error_count > 100:
                    print("[translator] error_count > 3, breaking...")
                    break
                error_count += 1
        print("[translator] end")
