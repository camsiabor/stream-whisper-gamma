import logging
import threading

from src import rtask


class RManifest(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.do_run = True

        self.logger = logging.getLogger('manifest')

    def run(self):
        self.logger.info("running")
        error_count = 0
        while self.do_run:
            try:
                task: rtask.RTask = self.task_ctrl.queue_manifest.get()
                text_target = task.text_translate
                if text_target is None or len(text_target) <= 0:
                    text_target = task.text_transcribe

                if text_target is None or len(text_target) <= 0:
                    continue

                # stamp = "[%.2fs -> %.2fs]" % (task.text_start, task.text_end)

                self.logger.info(f"[{task.text_info.duration}] ------------------------------------------------")
                self.logger.info(f"[s] {task.text_transcribe}")
                self.logger.info(f"[d] {text_target}")

            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1

        self.logger.info("end")
