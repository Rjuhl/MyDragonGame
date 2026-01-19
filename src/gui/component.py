import math
import pygame
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional

from gui.types import SizeUnit, ClickEvent

from system.global_vars import game_globals
from gui.utils.shapes import draw_rect_surface


class Component:
    """
        Base class for GUI components.

        Sizing model
        - Width/height are provided as strings:
            * "120"  -> absolute pixels
            * "50%"  -> percentage of parent width/height
        - `bind_parent(parent)` must be called before `get_size()` if you use "%".

        Position model
        - `x` and `y` are integer pixel coordinates in the render surface.
        - No layout is performed here; containers should set child positions.

        Background model
        - Optional list of background images (e.g., for hover/pressed states).
        - Backgrounds are scaled to the component size on demand.
        - If a background exists, `mouse_over()` can do pixel-perfect hit-testing using a mask.
        Otherwise it falls back to an AABB (rect) test.

        Extension points
        - handle_mouse_actions(...) : react to mouse events and update state
        - reposition_children()     : recompute child positions when layout changes
        - render(surface)           : draw yourself 
    """

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
        self.background: Optional[pygame.Surface] = None
        self.backgrounds: Optional[List[pygame.Surface]] = backgrounds
        if self.backgrounds:
            self.backgrounds = [self._load_background(file) for file in self.backgrounds]
            self.background = self.backgrounds[0]
        
        # Cache the last computed pixel size to avoid unnecessary rescaling.
        self._cached_size: Optional[Tuple[int, int]] = None

    # -------------------------------------------------------------------------
    # Properties: x/y and parent size
    # -------------------------------------------------------------------------

    @property
    def x(self) -> int:
        if self._x is None:
            raise ValueError("Component.x was accessed before being set.")
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("x must be an int")
        self._x = value

    @property
    def y(self) -> int:
        if self._y is None:
            raise ValueError("Component.y was accessed before being set.")
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("y must be an int")
        self._y = value

    @property
    def parent_w(self) -> int:
        if self._parent_w is None:
            raise ValueError("parent_w is not set for this component.")
        return self._parent_w

    @parent_w.setter
    def parent_w(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("parent_w must be an int")
        self._parent_w = value

    @property
    def parent_h(self) -> int:
        if self._parent_h is None:
            raise ValueError("parent_h is not set for this component.")
        return self._parent_h

    @parent_h.setter
    def parent_h(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("parent_h must be an int")
        self._parent_h = value

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def bind_parent(self, parent: Any) -> None:
        """
        Bind this component to its parent so % sizing can be computed.
        Parent must expose:
            parent.w, parent.h  (in pixels)
        """

        self.parent_w = int(parent.w)
        self.parent_h = int(parent.h)

    def unbind(self) -> None:
        """Hook for cleanup; containers can override."""
        # If components subscribe to events, timers, etc., clear them here.
        pass

    # -------------------------------------------------------------------------
    # Size / layout
    # -------------------------------------------------------------------------

    def get_size(self) -> Tuple[int, int]:
        """
        Compute the current pixel size.

        For absolute sizes, returns (self.w, self.h).
        For relative sizes (percent), uses parent's pixel size.

        Also scales backgrounds to the computed size (only when size changes).
        """
        
        width = self.w if self._size_unit_w == SizeUnit.Absolute else math.floor(self.parent_w * (self.w / 100))
        height = self.h if self._size_unit_h == SizeUnit.Absolute else math.floor(self.parent_h * (self.h / 100))
        
        size = (width, height)

        # Only rescale backgrounds when size changes.
        if size != self._cached_size:
            self._cached_size = size
            self._set_size(size)

        return size

    # -------------------------------------------------------------------------
    # Hit testing
    # -------------------------------------------------------------------------

    def mouse_over(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Return True if the mouse is over this component.

        If a background is set, this uses pixel-perfect hit testing via a mask:
        - only non-transparent pixels count as "inside"
        Otherwise, it falls back to an axis-aligned bounding box test.
        """
        
        mx, my = mouse_pos
        dx, dy = self.get_size()

        # Scale background if needed
        if self.background:
            background_mask = pygame.mask.from_surface(self.background)
            mask_w, mask_h = background_mask.get_size()

            # Convert global mouse pos to local (relative to surface top-left)
            rel_x = mx - self.x
            rel_y = my - self.y

            # Check bounds first
            if 0 <= rel_x < mask_w and 0 <= rel_y < mask_h:
                if background_mask.get_at((rel_x, rel_y)):
                    return True
            return False
        
        

        # Fallback: bounding box
        return (self.x <= mx <= self.x + dx and self.y <= my <= self.y + dy)
    
    # -------------------------------------------------------------------------
    # Background handling
    # -------------------------------------------------------------------------

    def _set_size(self, size: Tuple[int, int]) -> None:
        """ Resize background surfaces to match the component size """
        if self.backgrounds and self.background.get_size() != size:
            self.backgrounds = [pygame.transform.scale(background, size) for background in self.backgrounds]

    @staticmethod
    def _load_background(file):
        """ Loads a pygame image as the background from asset file """
        # Accept full Path objects
        return pygame.image.load(file.resolve()).convert_alpha()

    # --------------------------------------------------------------------------
    # Abstract like methods
    # --------------------------------------------------------------------------

    def handle_mouse_actions(
        self,
        mouse_pos: Tuple[int, int],
        click_event: ClickEvent,
        state_dict: Dict[Any, Any],
    ) -> None:
        """
        Handle mouse input for this component.

        Args:
            mouse_pos: Mouse position in screen pixels.
            click_event: High-level click state (from your GUI system).
            state_dict: Shared mutable state across GUI elements (if used).
        """
        pass

    def reposition_children(self) -> None:
        """
        Layout hook for container components.
        Leaf components typically do nothing.
        """
        pass

    def render(self, surface: pygame.Surface) -> None:
        """
        Render this component.
        Base implementation only draws optional debug hitboxes. Subclasses should
        draw
        """

        # For debugging 
        if game_globals.show_hitboxes_on:
            w, h = self.get_size()
            color = (0, 0, 0, 255)
            surface.blit(draw_rect_surface((0, 0, 0, 0), color, 1, w, h), (self.x, self.y))

