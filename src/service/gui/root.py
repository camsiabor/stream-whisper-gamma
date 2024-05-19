import logging
import threading
import tkinter as tk
from collections import deque

from src.common import sim
from src.service.gui.barrage import RBarrage


class RGuiRoot:

    def __init__(self, cfg: dict):
        self.logger = logging.getLogger('gui_root')

        self.cfg = cfg
        self.main = tk.Tk()
        self.barrage_max = 10
        self.barrages = deque(maxlen=self.barrage_max)

        self.lock = threading.Lock()

        self.screen_h = 0
        self.screen_w = 0

        # noinspection PyTypeChecker
        self.thread: threading.Thread = None

        self.configure()

    def configure(self) -> 'RGuiRoot':
        cfg_gui = self.cfg.get("gui", {})
        cfg_barrage = cfg_gui.get("barrage", {})
        self.configure_barrage(cfg_barrage)
        return self

    def configure_barrage(self, cfg_barrage):
        self.barrage_max = cfg_barrage.get("barrage_max", 10)
        self.barrages = deque(maxlen=self.barrage_max)

    def init(self):

        self.screen_w = self.main.winfo_screenwidth()
        self.screen_h = self.main.winfo_screenheight()

        # Set window size and position
        self.main.geometry(f"{self.screen_w}x{self.screen_h}+{0}+{0}")

        self.main.attributes("-topmost", True)  # Set the window to be always on top
        self.main.attributes("-transparentcolor", "#F0F0F0")
        self.main.attributes("-toolwindow", True)

        self.main.overrideredirect(True)

        button_test = tk.Button(
            self.main,
            text="TEST_ADD)",
            bg="black", fg="white",
            command=self.click_test,
        )
        button_test.pack(side="right", padx=10, pady=10)

        button_clear = tk.Button(
            self.main,
            text="TEST_CLEAR",
            bg="black", fg="white",
            command=self.click_clear
        )
        button_clear.pack(side="right", padx=10, pady=10)

    def click_test(self):
        count = len(self.barrages)
        self.add_barrage(f"New Barrage Message | {count}")

    def click_clear(self):
        try:
            self.lock.acquire()
            self.logger.debug("clearing barrages")
            for unit in self.barrages:
                self.main.after(0, unit.destroy)
            self.barrages.clear()
        finally:
            self.lock.release()

    def add_barrage(self, text: str):
        cfg_barrage = sim.get(self.cfg, {}, "gui", "barrage")
        self.logger.debug(f"adding barrage: {text}")

        nova = RBarrage(
            root=self,
            text=text,
            cfg=cfg_barrage
        )

        try:
            self.lock.acquire()

            barrage_count = len(self.barrages)

            legacy = None
            if barrage_count >= self.barrage_max:
                legacy = self.barrages.popleft()
                self.main.after(0, legacy.destroy)

            nova.x = nova.offset.get('x', 10)
            nova.y = self.screen_h - nova.offset.get('y', 10)

            self.main.after(0, self.update_barrage, nova, legacy)
        finally:
            self.lock.release()

    def update_barrage(self, nova: RBarrage, legacy: RBarrage):
        try:
            if legacy is not None:
                legacy.destroy()

            nova.init()
            nova.move(nova.x, nova.y)

            # print(f"barrages len: {len(self.barrages)}")
            # print(f"nova.x: {nova.x}, nova.y: {nova.y}, nova.height: {nova.height}")
            # print("---------------------------")

            for i in range(len(self.barrages) - 1, -1, -1):
                unit = self.barrages[i]
                # print(f"[{i}] A unit.x: {unit.x}, unit.y: {unit.y}, unit.height: {unit.height}")
                unit.move(unit.x, unit.y + unit.height - nova.height)
                # print(f"[{i}] Z unit.x: {unit.x}, unit.y: {unit.y}, unit.height: {unit.height}")
                # print("---------------------------")

            self.barrages.append(nova)
        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)

    def run_mainloop(self):
        self.main.mainloop()
