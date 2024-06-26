import logging
import tkinter as tk
from tkinter.font import Font


class RBarrage:

    def __init__(
            self,
            root,
            text: str = '',
            cfg: dict = None,
            timing: int = 0,
            priority: int = 0,
    ):
        self.root = root
        self.text = text
        self.cfg = cfg

        self.timing = timing
        self.priority = priority

        self.me = None
        self.label = None

        self.x = 0
        self.y = 0

        self.x_geo = 0
        self.y_geo = 0

        self.width = 0
        self.height = 0

        self.font = Font(family="Consolas", size=16)
        self.font_color = "#FFA500"
        self.font_background = "#000000"
        self.margin = {'x': 0, 'y': 3}
        self.offset = {'x': 10, 'y': 30}

        self.configure(self.cfg)

    def configure(self, cfg: dict) -> 'RBarrage':
        if cfg is None:
            cfg = self.cfg
        font_cfg = cfg.get("font", {})
        font_name = font_cfg.get("family", "Consolas")
        font_size = font_cfg.get("size", 16)
        self.font = Font(family=font_name, size=font_size)
        self.font_color = font_cfg.get("color", "#FFA500")
        self.font_background = font_cfg.get("background", "#000000")

        margin_cfg = cfg.get("margin", {})
        self.margin = {
            'x': margin_cfg.get("x", 0),
            'y': margin_cfg.get("y", 3)
        }
        offset_cfg = cfg.get("offset", {})
        self.offset = {
            'x': offset_cfg.get("x", 10),
            'y': offset_cfg.get("y", 30)
        }
        return self

    def init(self, text: str = None) -> 'RBarrage':

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

        self.label = tk.Label(
            self.me,
            text=text,
            fg=self.font_color,
            font=self.font,
            anchor="w"
        )
        if self.font_background is not None and len(self.font_background) > 0:
            self.label.configure(bg=self.font_background)
        self.label.pack(fill=tk.BOTH, expand=True, )

        lines = text.splitlines()
        num_lines = len(lines)

        text_w = self.font.measure(self.text)
        text_h_per = self.font.metrics("linespace")
        text_h = text_h_per * num_lines

        self.width = text_w + self.margin.get('x', 0)
        self.height = text_h + self.margin.get('y', 0)

        return self

    def pos_geo(self, x, y):
        x_geo = x + self.margin.get('x', 0)
        y_geo = y - self.height - self.margin.get('y', 0)
        return x_geo, y_geo

    def move(
            self,
            x: int, y: int,
            roof: int = 0,
    ) -> bool:

        self.x = x
        self.y = y

        self.x_geo, self.y_geo = self.pos_geo(x, y)

        if self.y_geo >= roof and self.me is not None:
            self.me.geometry(f"+{self.x_geo}+{self.y_geo}")
            return True

        self.destroy()
        return False

    def destroy(self):
        if self.me is not None:
            self.me.destroy()
            self.me = None
