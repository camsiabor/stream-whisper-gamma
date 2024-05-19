import logging
import threading

from src import rtask
from src.common import sim


class RManifest(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.do_run = True
        self.show_transcribe = True
        self.show_translated = True
        self.show_performance = False
        self.logger = logging.getLogger(name='manifest')
        self.console = True
        self.barrage = False
        self.configure()

    def configure(self) -> 'RManifest':
        cfg = self.task_ctrl.cfg.get("manifest", {})
        self.console = sim.get(cfg, True, "console")
        self.show_transcribe = sim.get(cfg, True, "show_transcribe")
        self.show_translated = sim.get(cfg, True, "show_translated")
        self.show_performance = sim.get(cfg, False, "show_performance")

        self.barrage = sim.get(cfg, True, "active")

        return self

    def manifest_transcribe(self, text_transcribe):
        if self.console:
            print(f"[s] {text_transcribe}")

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

                task.text_transcribe = task.text_transcribe.strip()

                text_target = sim.text_with_return(
                    text=task.text_translate.strip(),
                    splitter="" if task.param.lang_des == "zh" else " ",
                    max_len=10,
                )

                # print("[s] %s" % task.text_transcribe.encode('utf-8'))
                # print("[d] %s" % text_target.encode('utf-8'))

                if self.show_transcribe:
                    print(f"[s] {task.text_transcribe}")

                if self.show_translated:
                    print(f"[d] {text_target}")

                if self.barrage:
                    self.task_ctrl.gui_root.add_barrage(text_target)

                task.info.time_set("manifest")
                # task.info.time_set_as_str("manifest_str")
                task.info.time_diff("translate", "manifest", store="manifest")
                task.info.time_diff(head="create", tail="manifest", store="all")

                if self.show_performance:
                    diff_slice = task.info.time_elapsed_get("slice")
                    diff_transcribe = task.info.time_elapsed_get("transcribe")
                    diff_translate = task.info.time_elapsed_get("translate")
                    diff_manifest = task.info.time_elapsed_get("manifest")
                    diff_all = diff_slice + diff_transcribe + diff_translate + diff_manifest

                    pending_slice = self.task_ctrl.queue_slice.qsize()
                    pending_transcribe = self.task_ctrl.queue_transcribe.qsize()
                    print(
                        f"duration: {task.text_info.duration} | "
                        f"all: {diff_all} | slice: {diff_slice} | transcribe: {diff_transcribe} | "
                        f"translate: {diff_translate} | manifest: {diff_manifest} | "
                        f"slice_pending: {pending_slice} | transcribe_pending: {pending_transcribe} | "
                        "--- ")

            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1

        self.logger.info("end")
