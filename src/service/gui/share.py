from tkinter.font import Font


class RTextAttr:
    family = "Consolas"
    size = 16
    color = "#FFFFFF"
    background = "#000000"

    # noinspection PyUnresolvedReferences
    def __init__(
            self,
            base: 'RTextAttr' = None,
    ):
        self.base = base

    def init(
            self,
            family: str = "",
            size: int = 0,
            color: str = "",
            background: str = "",
            base: 'RTextAttr' = None,
    ) -> 'RTextAttr':
        if base is not None:
            self.base = base

        self.family = family
        self.size = size
        self.color = color
        self.background = background

        if self.base is not None:
            if len(self.family) <= 0:
                self.family = self.base.family
            if self.size <= 0:
                self.size = self.base.size + self.size
            if len(self.color) <= 0:
                self.color = self.base.color
            if len(self.background) <= 0:
                self.background = self.base.background

        return self

    def apply(self, target):
        f = Font(family=self.family, size=self.size)
        target.config(
            font=f,
            color=self.color,
            background=self.background
        )
        return target
