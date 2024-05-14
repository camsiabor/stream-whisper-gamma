import threading
import traceback

import src.service.google.translator
from src import rtask


class RTranslator(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            lang_src: str = "en",
            lang_des: str = "en",
            agent_google_domain: str = "hk",
            timeout: int = 5,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.do_run = True
        self.lang_src = lang_src
        self.lang_des = lang_des
        self.agent_google = src.service.google.translator.GoogleTranslator(
            url_suffix=agent_google_domain,
            timeout=timeout,
        )

    def run(self):
        print("[translater] running")
        error_count = 0
        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_translate.get()
                if task.text_transcribe is None or len(task.text_transcribe) <= 0:
                    continue

                # task.text_translate = task.text_transcribe

                lang_ori = task.text_info.language

                if lang_ori == self.lang_des:
                    task.text_translate = task.text_transcribe
                else:
                    task.text_translate = self.agent_google.translate(
                        task.text_transcribe,
                        self.lang_des, lang_ori,
                    )

                self.task_ctrl.queue_manifest.put(task)
            except Exception:
                traceback.print_exc()
                if error_count > 100:
                    print("[translater] error_count > 3, breaking...")
                    break
                error_count += 1
        print("[translater] end")
