from enum import Enum

class ItemAlign(Enum):
    First = "First"
    Last = "Last"
    Center = "Center"


class ItemAppend(Enum):
    Right = "Right"
    Below = "Below"


class SizeUnit(Enum):
    Absolute = "Absolute"
    Relative = "Relative"


class ClickEvent(Enum):
    Right = "Right"
    Left = "Left"
    Empty = "Empty"
