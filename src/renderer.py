import threading
import traceback

from src import rtask


class Renderer(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.do_run = True

    def run(self):
        error_count = 0
        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_render.get()
                text_target = None
                if task.text_translate is None:
                    text_target = task.text_transcribe

                if text_target is None or len(text_target) <= 0:
                    continue

                print(text_target)

            except Exception:
                traceback.print_exc()
                if error_count > 3:
                    print("[renderer] error_count > 3, breaking...")
                    break
                error_count += 1


        pass
