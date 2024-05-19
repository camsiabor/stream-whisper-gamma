import logging
import threading
import tkinter as tk
from collections import deque
from tkinter.font import Font

from barrage import RBarrage


class RGuiRoot:

    def __init__(self, cfg: dict):
        self.logger = logging.getLogger('barrage')

        self.cfg = cfg
        self.main = tk.Tk()
        self.barrage_max = 10
        self.barrages = deque(maxlen=self.barrage_max)

        self.font = Font(family="Consolas", size=16)
        self.font_color = "#FFA500"
        self.font_background = "#000000"

        self.margin = {'x': 10, 'y': 10}

        self.lock = threading.Lock()

        self.screen_h = 0
        self.screen_w = 0

        # noinspection PyTypeChecker
        self.thread: threading.Thread = None

        self.configure()
        self.init()

    def configure(self) -> 'RGuiRoot':
        cfg_gui = self.cfg.get("gui", {})
        cfg_barrage = cfg_gui.get("barrage", {})
        self.configure_barrage(cfg_barrage)
        return self

    def configure_barrage(self, cfg_barrage):

        self.barrage_max = cfg_barrage.get("barrage_max", 10)
        self.barrages = deque(maxlen=self.barrage_max)

        font_cfg = cfg_barrage.get("font", {})
        font_name = font_cfg.get("family", "Consolas")
        font_size = font_cfg.get("size", 16)
        self.font = Font(family=font_name, size=font_size)
        self.font_color = cfg_barrage.get("font_color", "#FFA500")
        self.font_background = cfg_barrage.get("font_background", "#000000")

        margin_cfg = cfg_barrage.get("margin", {})
        self.margin = {
            'x': margin_cfg.get("x", 10),
            'y': margin_cfg.get("y", 10)
        }

    def init(self):

        self.screen_w = self.main.winfo_screenwidth()
        self.screen_h = self.main.winfo_screenheight()

        self.main.geometry(f"{self.screen_w}x{self.screen_h}+{0}+{0}")  # Set window size and position

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
            print("clearing")
            for unit in self.barrages:
                self.main.after(0, unit.destroy)
            self.barrages.clear()
        finally:
            self.lock.release()

    def add_barrage(self, text: str):
        try:
            self.lock.acquire()
            print("adding")
            unit = RBarrage(self, text)

            prev = self.barrages[-1] if len(self.barrages) > 0 else None
            if prev is not None:
                target_y = prev.y
                target_x = prev.x
            else:
                target_y = self.screen_h - self.margin.get('y', 10)
                target_x = self.margin.get('x', 10)

            self.main.after(0, unit.init, text)
            self.main.after(0, unit.move, target_x, target_y)

            self.barrages.append(unit)
        finally:
            self.lock.release()

    def run_mainloop(self):
        self.main.mainloop()
