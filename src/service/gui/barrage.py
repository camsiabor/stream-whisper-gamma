import logging
import tkinter as tk
from collections import deque
from tkinter.font import Font


class RBarrage:

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.main = tk.Tk()
        self.logger = logging.getLogger('barrage')
        self.barrage_max = 10
        self.barrages = deque(maxlen=self.barrage_max)

        self.configure()

    def configure(self) -> 'RBarrage':
        cfg = self.cfg.get("barrage", {})
        self.barrage_max = cfg.get("barrage_max", 10)
        self.barrages = deque(maxlen=self.barrage_max)

        screen_w = self.main.winfo_screenwidth()
        screen_h = self.main.winfo_screenheight()

        self.main.geometry(f"{screen_w}x{screen_h}+{0}+{0}")  # Set window size and position

        self.main.attributes("-topmost", True)  # Set the window to be always on top
        self.main.attributes("-transparentcolor", "#F0F0F0")
        self.main.attributes("-toolwindow", True)

        self.main.overrideredirect(True)
        return self

    # Function to add a new barrage message
    def add_barrage_message(self, message):
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

        font = Font(family="Arial", size=20)
        label = tk.Label(sub, text=message, fg="orange", font=font)
        label.pack(fill=tk.BOTH, expand=True)
        self.barrages.append(sub)

    def run(self):
        self.main.mainloop()
