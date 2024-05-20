import logging
import threading

from src import rtask
from src.common import sim


class RManifestUnit:
    active: bool = False
    phoneme: bool = False,
    transcribe: bool = True,
    translated: bool = True,
    performance: bool = False,

    def set(
            self,
            active: bool = False,
            phoneme: bool = False,
            transcribe: bool = True,
            translated: bool = True,
            performance: bool = False
    ) -> 'RManifestUnit':
        self.active = active
        self.phoneme = phoneme
        self.transcribe = transcribe
        self.translated = translated
        self.performance = performance
        return self


class RManifest(threading.Thread):

    def __init__(
            self,
            task_ctrl: rtask.RTaskControl,
            index: int = 1,
    ):
        super().__init__()
        self.task_ctrl = task_ctrl
        self.index = index

        self.do_run = True
        self.logger = logging.getLogger(name='manifest')
        self.console = RManifestUnit()
        self.barrage = RManifestUnit()
        self.configure()

    def configure(self) -> 'RManifest':
        cfg = self.task_ctrl.cfg.get("manifest", {})
        cfg_console = sim.get(cfg, {}, "console")
        cfg_barrage = sim.get(cfg, {}, "barrage")
        self.console.set(**cfg_console)
        self.barrage.set(**cfg_barrage)
        return self

    def manifest_transcribe(self, task, timing, priority):

        text = task.text_transcribe

        if text is None or len(text) <= 0:
            return

        if self.console.active and self.console.transcribe:
            print(f"[s] {text}")

        if self.barrage.active and self.barrage.transcribe:
            self.task_ctrl.gui_root.add_barrage(
                text=text,
                font_color="#FFFFFF",
                font_size_delta=-2,
                timing=timing,
                priority=priority,
            )

    def manifest_phoneme(self, task, timing, priority):

        text = task.text_phoneme

        if text is None or len(text) <= 0:
            return

        if self.console.active and self.console.phoneme:
            print(f"[p] {task.text_transcribe}")

        if self.barrage.active and self.barrage.phoneme:
            self.task_ctrl.gui_root.add_barrage(
                text=text,
                font_color="#88CCEE",
                font_size_delta=-2,
                timing=timing,
                priority=priority,
            )

    def manifest_translate(self, task, timing, priority):
        text = task.text_translate
        if text is None or len(text) <= 0:
            return
        if self.console.active and self.console.translated:
            print(f"[d] {text}")

        if self.barrage.active and self.barrage.translated:
            self.task_ctrl.gui_root.add_barrage(
                text=text,
                timing=timing,
                priority=priority,
            )

    def manifest_performance(self, task, timing, priority):

        do_console = self.console.active and self.console.performance
        do_barrage = self.barrage.active and self.barrage.performance

        if not (do_console or do_barrage):
            return

        task.info.time_set("manifest")
        # task.info.time_set_as_str("manifest_str")
        task.info.time_diff("translate", "manifest", store="manifest")
        task.info.time_diff(head="create", tail="manifest", store="all")

        diff_slice = task.info.time_elapsed_get("slice")
        diff_transcribe = task.info.time_elapsed_get("transcribe")
        diff_translate = task.info.time_elapsed_get("translate")
        diff_manifest = task.info.time_elapsed_get("manifest")
        diff_all = diff_slice + diff_transcribe + diff_translate + diff_manifest

        pending_slice = self.task_ctrl.queue_slice.qsize()
        pending_transcribe = self.task_ctrl.queue_transcribe.qsize()
        perf = f"duration: {task.text_info.duration} | " \
               f"all: {diff_all} | slice: {diff_slice} | transcribe: {diff_transcribe} | " \
               f"translate: {diff_translate} | manifest: {diff_manifest} | " \
               f"slice_pending: {pending_slice} | transcribe_pending: {pending_transcribe} | "

        if do_console:
            print(perf)

        if do_barrage:
            self.task_ctrl.gui_root.add_barrage(
                text=perf,
                font_color="#FFFFFF",
                font_size_delta=-5,
                timing=timing,
                priority=priority,
            )

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

                lang_src = task.text_info.language
                lang_src_east_asian = lang_src == "zh" or lang_src == "ja" or lang_src == "ko"

                lang_des = task.param.lang_des
                lang_des_east_asian = lang_des == "zh" or lang_des == "ja" or lang_des == "ko"

                task.text_transcribe = sim.insert_newline_per(
                    text=task.text_transcribe.strip(),
                    max_len=16 if lang_src_east_asian else 10,
                )

                task.text_translate = sim.insert_newline_per(
                    text=task.text_translate.strip(),
                    max_len=16 if lang_des_east_asian else 10,
                )

                timing = task.info.time_get("slice", True)

                self.manifest_transcribe(task, timing, 1)
                self.manifest_phoneme(task, timing, 2)
                self.manifest_translate(task, timing, 3)
                self.manifest_performance(task, timing, 4)

            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1

        self.logger.info("end")
