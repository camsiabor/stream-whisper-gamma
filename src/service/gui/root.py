import logging
import random
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
        self.barrage_roof = 0
        self.barrages = deque(maxlen=self.barrage_max)

        self.lock = threading.Lock()

        self.width = 0
        self.height = 0

        self.width_ratio = 1
        self.height_ratio = 1

        self.screen_h = 0
        self.screen_w = 0

        self.click_add_index = 1

        self.show = True

        # noinspection PyTypeChecker
        self.thread: threading.Thread = None

        self.configure()

    def configure(self) -> 'RGuiRoot':
        cfg_gui = self.cfg.get("gui", {})
        self.width = cfg_gui.get("width", 0)
        self.height = cfg_gui.get("height", 0)
        self.width_ratio = cfg_gui.get("width_ratio", 1)
        self.height_ratio = cfg_gui.get("height_ratio", 1)

        cfg_barrage = cfg_gui.get("barrage", {})
        self.configure_barrage(cfg_barrage)
        return self

    def configure_barrage(self, cfg_barrage):
        self.barrage_max = cfg_barrage.get("max", 10)
        self.barrage_roof = cfg_barrage.get("roof", 0)
        self.barrages = deque(maxlen=self.barrage_max)

    def init(self):

        self.screen_w = self.main.winfo_screenwidth()
        self.screen_h = self.main.winfo_screenheight()

        if self.width <= 0:
            self.width = self.screen_w

        if self.height <= 0:
            self.height = self.screen_h

        self.width = round(self.width * self.width_ratio)
        self.height = round(self.height * self.height_ratio)

        # Set window size and position
        self.main.geometry(f"{self.width}x{self.height}+{0}+{0}")

        self.main.attributes("-topmost", True)  # Set the window to be always on top
        self.main.attributes("-transparentcolor", "#F0F0F0")
        self.main.attributes("-toolwindow", True)

        self.main.overrideredirect(True)

        button_exit = tk.Button(
            self.main,
            text="EXIT",
            bg="black", fg="white",
            command=lambda: self.main.destroy(),
        )
        button_exit.pack(side="right", padx=3, pady=0)

        button_add = tk.Button(
            self.main,
            text="ADD",
            bg="black", fg="white",
            command=self.click_add,
        )
        button_add.pack(side="right", padx=3, pady=0)

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
        try:
            timing = random.randint(1, 1024)
            self.add_barrage(
                text=f"T {timing} I {self.click_add_index}",
                timing=timing,
            )
        finally:
            self.click_add_index += 1

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
            self.show = False
            self.logger.debug("hiding barrages")
            for unit in self.barrages:
                self.main.after(0, unit.me.withdraw)
        finally:
            self.lock.release()

    def click_show(self):
        try:
            self.lock.acquire()
            self.show = True
            self.logger.debug("showing barrages")
            for unit in self.barrages:
                self.main.after(0, unit.me.deiconify)
        finally:
            self.lock.release()

    def add_barrage(
            self,
            text: str,
            font: Font = None,
            font_size_delta: int = 0,
            font_family='',
            font_color: str = '',
            font_background: str = '',
            timing: int = 0,
            priority: int = 0,
    ):

        if text is None or len(text) <= 0:
            return

        cfg_barrage = sim.get(self.cfg, {}, "gui", "barrage")
        self.logger.debug(f"adding barrage: {text}")

        nova = RBarrage(
            root=self,
            text=text,
            cfg=cfg_barrage,
            timing=timing,
            priority=priority,
        )

        if font is not None:
            nova.font = font

        if font_size_delta != 0:
            font_size = nova.font.cget("size")
            nova.font.config(size=font_size + font_size_delta)

        if font_family is not None and len(font_family) > 0:
            nova.font.config(family=font_family)

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

            sim.insort_ex(
                container=self.barrages,
                unit=nova,
                right=True,
                key=lambda x: x.timing + x.priority
            )

            self.main.after(0, self.update_barrage, nova, legacy)
        finally:
            self.lock.release()

    def update_barrage(self, nova: RBarrage, legacy: RBarrage):
        try:
            if legacy is not None:
                legacy.destroy()

            nova.init()

            y_item = 0
            h_item = 0

            index_destroy = -1
            index_last = len(self.barrages) - 1
            for i in range(index_last, -1, -1):
                unit = self.barrages[i]

                x_item = nova.offset.get('x', 10)
                if index_last == i:
                    y_item = self.screen_h - nova.offset.get('y', 10)
                else:
                    y_item = y_item - h_item
                h_item = unit.height + unit.margin.get('y', 0)

                # print(f"[{i}] B x_item: {x_item}, y_item: {y_item}, h_item: {h_item}")

                success = unit.move(
                    x=x_item, y=y_item,
                    roof=self.barrage_roof,
                )

                if not self.show:
                    unit.me.withdraw()

                if not success:
                    index_destroy = i
                    break

            if index_destroy >= 0:
                for i in range(index_destroy + 1):
                    self.barrages.popleft()

        except Exception as ex:
            self.logger.error(ex, exc_info=True, stack_info=True)

    def run_mainloop(self):
        self.main.mainloop()
