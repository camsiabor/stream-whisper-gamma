import logging
import threading
import tkinter as tk
from collections import deque
from tkinter.font import Font


class RBarrageUnit:

    def __init__(
            self,
            root: 'RBarrage',
            text: str = '',
    ):
        self.text = text
        self.me = None
        self.root = root
        self.label = None

        self.x = 10
        self.y = 0
        self.width = 0
        self.height = 0

    def init(self, text) -> 'RBarrageUnit':

        if self.me is not None:
            logging.warning("Barrage window already exists")
            return self

        if text is None:
            text = self.text
        if text is None:
            text = ''

        self.me = tk.Toplevel(self.root.main)
        self.me.attributes("-topmost", True)  # Set the window to be always on top
        self.me.attributes("-transparentcolor", "#F0F0F0")
        self.me.attributes("-toolwindow", True)
        self.me.overrideredirect(True)  # Remove window decorations (title bar, borders, etc.)
        # self.me.geometry(f"+{0}+{0}")

        font = self.root.font
        self.label = tk.Label(
            self.me,
            text=text,
            fg=self.root.font_color,

            font=font
        )
        if self.root.font_background is not None and len(self.root.font_background) > 0:
            self.label.configure(bg=self.root.font_background)
        self.label.pack(fill=tk.BOTH, expand=True, )

        lines = text.splitlines()
        num_lines = len(lines)

        screen_h = self.root.screen_h
        text_w = font.measure(self.text)
        text_h_per = font.metrics("linespace")
        text_h = text_h_per * num_lines

        self.x = 0
        self.y = screen_h - text_h
        self.width = text_w
        self.height = text_h

        return self

    def move(self, x: int, y: int, height_offset: int = None) -> 'RBarrageUnit':
        if height_offset is None:
            height_offset = self.height
        self.x = x
        self.y = y - height_offset
        self.me.geometry(f"+{self.x}+{self.y}")
        return self

    def destroy(self):
        if self.me is not None:
            self.me.destroy()
            self.me = None


class RBarrage:

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

        self.configure()
        self.init()

    def configure(self) -> 'RBarrage':
        cfg = self.cfg.get("barrage", {})
        self.barrage_max = cfg.get("barrage_max", 10)
        self.barrages = deque(maxlen=self.barrage_max)

        font_cfg = cfg.get("font", {})
        font_name = font_cfg.get("family", "Consolas")
        font_size = font_cfg.get("size", 16)
        self.font = Font(family=font_name, size=font_size)
        self.font_color = cfg.get("font_color", "#FFA500")
        self.font_background = cfg.get("font_background", "#000000")

        margin_cfg = cfg.get("margin", {})
        self.margin = {
            'x': margin_cfg.get("x", 10),
            'y': margin_cfg.get("y", 10)
        }

        self.screen_w = self.main.winfo_screenwidth()
        self.screen_h = self.main.winfo_screenheight()

        self.main.geometry(f"{self.screen_w}x{self.screen_h}+{0}+{0}")  # Set window size and position

        self.main.attributes("-topmost", True)  # Set the window to be always on top
        self.main.attributes("-transparentcolor", "#F0F0F0")
        self.main.attributes("-toolwindow", True)

        self.main.overrideredirect(True)
        return self

    def init(self):
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
            unit = RBarrageUnit(self, text)

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

    def run(self):
        self.main.mainloop()
