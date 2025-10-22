import math
import pygame
from gui.types import SizeUnit, ClickEvent
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path


class Component:
    def __init__(
        self,
        w: str, h: str,
        backgrounds: Optional[List[Path]] | None = None
    ):
        # width & height parsing
        self.w = int(w[:-1]) if w[-1] == "%" else int(w)
        self.h = int(h[:-1]) if h[-1] == "%" else int(h)
        self._size_unit_w = SizeUnit.Relative if w[-1] == "%" else SizeUnit.Absolute
        self._size_unit_h = SizeUnit.Relative if h[-1] == "%" else SizeUnit.Absolute

        # internal attributes (use private fields for property control)
        self._x = None
        self._y = None
        self._parent_w = None
        self._parent_h = None

        # optional background image
        self.background = None
        self.backgrounds = backgrounds
        if self.backgrounds:
            self.backgrounds = [self._load_background(file) for file in self.backgrounds]
            self.background = self.backgrounds[0]

    # --------------------------------------------------------------------------
    #                              PROPERTIES
    # --------------------------------------------------------------------------
    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int):
        if not isinstance(value, int):
            raise TypeError("x must be an int")
        self._x = int(value)

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int):
        if not isinstance(value, int):
            raise TypeError("y must be an int")
        self._y = int(value)

    @property
    def parent_w(self) -> int:
        if self._parent_w is None:
            raise ValueError("parent_w is not set for this component.")
        return self._parent_w

    @parent_w.setter
    def parent_w(self, value: int):
        if not isinstance(value, int):
            raise TypeError("parent_w must be an int")
        self._parent_w = int(value)

    @property
    def parent_h(self) -> int:
        if self._parent_h is None:
            raise ValueError("parent_h is not set for this component.")
        return self._parent_h

    @parent_h.setter
    def parent_h(self, value: int):
        if not isinstance(value, int):
            raise TypeError("parent_h must be an int")
        self._parent_h = int(value)

    # --------------------------------------------------------------------------
    #                              METHODS
    # --------------------------------------------------------------------------

    def get_size(self) -> Tuple[int, int]:
        """Returns component size based on parent's size."""
        width = self.w if self._size_unit_w == SizeUnit.Absolute else math.floor(self.parent_w * (self.w / 100))
        height = self.h if self._size_unit_h == SizeUnit.Absolute else math.floor(self.parent_h * (self.h / 100))
        self._set_size((width, height))
        return width, height

    def mouse_over(self, mouse_pos: Tuple[int, int]) -> bool:
        """Checks if mouse overlaps with the component."""
        mx, my = mouse_pos
        dx, dy = self.get_size()

        # Scale background if needed
        if self.background:
            background_mask = pygame.mask.from_surface(self.background)

            # Convert global mouse pos to local (relative to surface top-left)
            rel_x = mx - self.x
            rel_y = my - self.y

            # Check bounds first
            if 0 <= rel_x < dx and 0 <= rel_y < dy:
                if background_mask.get_at((rel_x, rel_y)):
                    return True
            return False

        # Fallback: bounding box
        return (self.x <= mx <= self.x + dx and self.y <= my <= self.y + dy)

    def _set_size(self, size: Tuple[int, int]) -> None:
        """Updates background to correct size."""
        if self.backgrounds and self.background.get_size() != size:
            self.backgrounds = [pygame.transform.scale(background, size) for background in self.backgrounds]

    @staticmethod
    def _load_background(file):
        """Loads a pygame image as the background from asset file."""
        # Accept full Path objects
        return pygame.image.load(file.resolve()).convert_alpha()

    # --------------------------------------------------------------------------
    #                              ABSTRACT-LIKE METHODS
    # --------------------------------------------------------------------------

    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        """Executes actions based on mouse position and click."""
        pass

    def reposition_children(self) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass
