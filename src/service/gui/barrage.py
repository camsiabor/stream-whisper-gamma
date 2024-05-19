import logging
import threading
import tkinter as tk
from collections import deque
from tkinter.font import Font


class RBarrageUnit:

    def __init__(
            self,
            root: 'RBarrage',
            text: str
    ):
        self.text = text
        self.root = root
        self.label = None

    def destroy(self):
        if self.label is not None:
            self.label.destroy()


class RBarrage:

    def __init__(self, cfg: dict):
        self.logger = logging.getLogger('barrage')

        self.cfg = cfg
        self.main = tk.Tk()
        self.barrage_max = 10
        self.barrages = deque(maxlen=self.barrage_max)

        self.font = Font(family="Consolas", size=16)

        self.lock = threading.Lock()

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


        screen_w = self.main.winfo_screenwidth()
        screen_h = self.main.winfo_screenheight()

        self.main.geometry(f"{screen_w}x{screen_h}+{0}+{0}")  # Set window size and position

        self.main.attributes("-topmost", True)  # Set the window to be always on top
        self.main.attributes("-transparentcolor", "#F0F0F0")
        self.main.attributes("-toolwindow", True)

        self.main.overrideredirect(True)
        return self

    def init(self):
        button_test = tk.Button(
            self.main,
            text="Test",
            bg="black", fg="white",
            command=self.click_test,
        )
        button_test.pack(side="right", padx=10, pady=10)

        button_clear = tk.Button(
            self.main,
            text="Clear Barrages",
            bg="black", fg="white",
            command=self.click_clear
        )
        button_clear.pack(side="right", padx=10, pady=10)

    def click_test(self):
        self.add_barrage_message("New Barrage Message")

    def click_clear(self):
        try:
            self.lock.acquire()
            for barrage in self.barrages:
                barrage.destroy()
            self.barrages.clear()
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
