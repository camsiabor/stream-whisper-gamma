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

    def init(self, text):

        if self.me is not None:
            logging.warning("Barrage window already exists")
            return

        if text is None:
            text = self.text
        if text is None:
            text = ''

        screen_h = self.root.screen_h

        font = self.root.font
        text_w = font.measure(self.text)
        text_h_per = font.metrics("linespace")
        # me_h = screen_h - text_h_per

        self.me = tk.Toplevel(self.root.main)
        self.me.attributes("-topmost", True)  # Set the window to be always on top
        self.me.attributes("-transparentcolor", "#F0F0F0")
        self.me.attributes("-toolwindow", True)
        self.me.overrideredirect(True)  # Remove window decorations (title bar, borders, etc.)
        # self.me.geometry(f"+{0}+{0}")

        label = tk.Label(self.me, text=text, fg="orange", font=font)
        # label.pack(fill=tk.BOTH, expand=True)
        label.pack(fill=tk.BOTH, expand=True, )

        self.x = 10
        self.y = screen_h - text_h_per - 10
        self.width = text_w
        self.height = text_h_per + 1

        # Set window size and position
        # self.me.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        self.me.geometry(f"+{self.x}+{self.y}")

        label_w = label.winfo_width()
        label_h = label.winfo_height()

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
            self.main.after(0, unit.init, text)
            self.barrages.append(unit)
        finally:
            self.lock.release()

    # Function to add a new barrage message
    def add_barrage_message(self, text):
        try:
            self.lock.acquire()

            label_font = Font(family="Consolas", size=16)
            text_width = label_font.measure(text)
            text_height = label_font.metrics("linespace")

            if len(self.barrages) >= self.barrage_max:
                # Remove the oldest window if the limit is reached
                oldest_barrage = self.barrages.popleft()
                oldest_barrage.destroy()

                # Move existing windows up by 30 pixels
                for barrage in self.barrages:
                    x, y = barrage.winfo_x(), barrage.winfo_y() - 30
                    barrage.geometry(f"+{x}+{y}")

            x = 10
            # Adjust the vertical position of the new window
            y = self.main.winfo_screenheight() - (len(self.barrages) + 1) * 30
            sub = tk.Toplevel(self.main)
            sub.attributes("-topmost", True)  # Set the window to be always on top
            sub.attributes("-transparentcolor", "#F0F0F0")
            sub.attributes("-toolwindow", True)
            sub.overrideredirect(True)  # Remove window decorations (title bar, borders, etc.)
            sub.geometry(f"+{x}+{y}")  # Set window size and position

            label_font = tk.font.Font(family="Arial", size=20)
            label = tk.Label(sub, text=text, fg="orange", font=label_font)
            label.pack(fill=tk.BOTH, expand=True, )
            self.barrages.append(sub)
        finally:
            self.lock.release()

    def run(self):
        self.main.mainloop()
