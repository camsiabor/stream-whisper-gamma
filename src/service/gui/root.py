import logging
import threading
import tkinter as tk
from collections import deque
from tkinter.font import Font

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
        self.barrage_max = cfg_barrage.get("max", 10)
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
            text="ADD",
            bg="black", fg="white",
            command=self.click_add,
        )
        button_test.pack(side="right", padx=3, pady=0)

        button_clear = tk.Button(
            self.main,
            text="CLEAR",
            bg="black", fg="white",
            command=self.click_clear
        )
        button_clear.pack(side="right", padx=3, pady=0)

        button_hide = tk.Button(
            self.main,
            text="HIDE",
            bg="black", fg="white",
            command=self.click_hide
        )
        button_hide.pack(side="right", padx=3, pady=0)

        button_show = tk.Button(
            self.main,
            text="SHOW",
            bg="black", fg="white",
            command=self.click_show
        )
        button_show.pack(side="right", padx=3, pady=0)

    def click_add(self):
        timing = sim.datetime_str()
        self.add_barrage(f"New Barrage Message | {timing}")

    def click_clear(self):
        try:
            self.lock.acquire()
            self.logger.debug("clearing barrages")
            for unit in self.barrages:
                self.main.after(0, unit.destroy)
            self.barrages.clear()
        finally:
            self.lock.release()

    def click_hide(self):
        try:
            self.lock.acquire()
            self.logger.debug("hiding barrages")
            for unit in self.barrages:
                self.main.after(0, unit.me.withdraw)
        finally:
            self.lock.release()

    def click_show(self):
        try:
            self.lock.acquire()
            self.logger.debug("showing barrages")
            for unit in self.barrages:
                self.main.after(0, unit.me.deiconify)
        finally:
            self.lock.release()

    def add_barrage(
            self,
            text: str,
            font: Font = None,
            font_color: str = '',
            font_background: str = '',
    ):

        if text is None or len(text) <= 0:
            return

        cfg_barrage = sim.get(self.cfg, {}, "gui", "barrage")
        self.logger.debug(f"adding barrage: {text}")

        nova = RBarrage(
            root=self,
            text=text,
            cfg=cfg_barrage
        )

        if font is not None:
            nova.font = font

        if font_color is not None and len(font_color) > 0:
            nova.font_color = font_color

        if font_background is not None and len(font_background) > 0:
            nova.font_background = font_background

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
