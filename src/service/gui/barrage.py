import logging
import tkinter as tk

from root import RGuiRoot


class RBarrage:

    def __init__(
            self,
            root: 'RGuiRoot',
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

    def init(self, text) -> 'RBarrage':

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

    def move(self, x: int, y: int, height_offset: int = None) -> 'RBarrage':
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




