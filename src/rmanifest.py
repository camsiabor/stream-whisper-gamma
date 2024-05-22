import logging
import threading

from src import rtask
from src.common import sim
from src.rtask import RManifestUnit
from src.service.gui.share import RTextAttr
from src.service.persist.filer import RPersistToFile


class RManifest(threading.Thread):

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
        self.logger = logging.getLogger(name='manifest')
        self.console = RManifestUnit()
        self.barrage = RManifestUnit()
        self.file = RManifestUnit()
        self.file_persister: RPersistToFile = None
        self.configure()

    def configure(self) -> 'RManifest':
        cfg_manifest = self.task_ctrl.cfg.get("manifest", {})
        cfg_console = sim.getv(cfg_manifest, {}, "console")
        cfg_barrage = sim.getv(cfg_manifest, {}, "barrage")
        cfg_file = sim.getv(cfg_manifest, {}, "file")
        self.console.init(**cfg_console)
        self.barrage.init(**cfg_barrage)
        self.file.init(**cfg_file)

        textattr_default = None
        for manifest_type in ["default", "transcribe", "phoneme", "translated", "performance"]:
            setting = self.barrage.text.get(manifest_type, None)
            if setting is None:
                continue
            # noinspection PyArgumentList
            textattr = RTextAttr(textattr_default).init(**setting)
            if manifest_type == "default":
                textattr_default = textattr
            self.barrage.textattrs[manifest_type] = textattr

        if textattr_default is None:
            self.barrage.textattrs["default"] = RTextAttr()

        return self

    def show_barrage(self, manifest_type: str, task: rtask.RTask, text: str, priority: int):
        if not self.barrage.active:
            return
        textattr = self.barrage.textattrs.get(manifest_type, None)
        if textattr is None:
            textattr = self.barrage.textattrs.get("default", None)
        self.task_ctrl.gui_root.add_barrage(
            text=text,
            font_family=textattr.family,
            font_color=textattr.color,
            font_size=textattr.size,
            timing=task.info.sequence,
            priority=priority,
        )

    def manifest_transcribe(self, task, priority):

        text = task.text_transcribe

        if text is None or len(text) <= 0:
            return

        if self.console.active and self.console.transcribe:
            print(f"[s] {text}")

        if self.barrage.transcribe:
            self.show_barrage("transcribe", task, text, priority)

    def manifest_phoneme(self, task, priority):

        text = task.text_phoneme

        if text is None or len(text) <= 0:
            return

        if self.console.active and self.console.phoneme:
            print(f"[p] {text}")

        if self.barrage.phoneme:
            self.show_barrage("phoneme", task, text, priority)

    def manifest_translated(self, task, priority):
        text = task.text_translate
        if text is None or len(text) <= 0:
            return
        if self.console.active and self.console.translated:
            print(f"[d] {text}")

        if self.barrage.translated:
            self.show_barrage("translated", task, text, priority)

    def manifest_performance(self, task, priority):

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
            self.show_barrage("performance", task, perf, priority)

    def persist_init(self):
        try:
            if self.file.active:
                self.file_persister = RPersistToFile(
                    name="manifest",
                    filename=self.file.path,
                )
                self.file_persister.init()
                self.file_persister.start()
            return True
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)
            return False

    def persist(self, task: rtask.RTask):
        if self.file_persister is not None:
            task.param.manifest = self.file
            self.file_persister.push(task)
        pass

    def run(self):
        self.logger.info("running")
        error_count = 0

        if not self.persist_init():
            return

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

                task.text_transcribe = sim.Text.insert_newline_per(
                    text=task.text_transcribe.strip(),
                    max_len=16 if lang_src_east_asian else 10,
                )

                task.text_translate = sim.Text.insert_newline_per(
                    text=task.text_translate.strip(),
                    max_len=16 if lang_des_east_asian else 10,
                )

                self.manifest_transcribe(task, 1)
                self.manifest_phoneme(task, 2)
                self.manifest_translated(task, 3)
                self.manifest_performance(task, 4)

                self.persist(task)

            except Exception as ex:
                self.logger.error(ex, exc_info=True, stack_info=True)
                if error_count > 3:
                    self.logger.warning("error_count > 3, breaking...")
                    break
                error_count += 1

        if self.file_persister is not None:
            self.file_persister.close()

        self.logger.info("end")
