import threading
import traceback

from src import rtask


class RTranslater(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.do_run = True

    def run(self):
        print("[translater] running")
        error_count = 0
        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_translate.get()
                if task.text_transcribe is None or len(task.text_transcribe) <= 0:
                    continue

                task.text_translate = task.text_transcribe
                self.task_ctrl.queue_render.put(task)

            except Exception:
                traceback.print_exc()
                if error_count > 3:
                    print("[translater] error_count > 3, breaking...")
                    break
                error_count += 1
        print("[translater] end")
