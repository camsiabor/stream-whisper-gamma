from tkinter.font import Font


class RFont:

    # noinspection PyUnresolvedReferences
    def __init__(
            self,
            family: str = "",
            size: int = 0,
            color: str = "",
            background: str = "",
            base: 'RFont' = None,
    ):
        self.family = family
        self.size = size
        self.color = color
        self.background = background

        if base is not None:
            if len(self.family) <= 0:
                self.family = base.family
            if self.size == 0:
                self.size = base.size
            if self.size < 0:
                self.size = base.size - self.size
            if len(self.color) <= 0:
                self.color = base.color
            if len(self.background) <= 0:
                self.background = base.background

        pass

    def apply(self, target):
        f = Font(family=self.family, size=self.size)
        target.config(
            font=f,
            color=self.color,
            background=self.background
        )
        return target
