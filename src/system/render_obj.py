import pygame
import numpy as np
from numpy.typing import NDArray
from typing import Optional, Tuple

from dataclasses import dataclass

from utils.coords import Coord
from utils.types.colors import RGBA


@dataclass(slots=True)
class RenderObj:
    """
        Lightweight render command object.

        RenderObj is produced by entities/systems and consumed by the renderer. It contains
        just enough information to draw something on screen without the renderer needing
        to know about game/entity internals.

        How to render
        - If `img` is provided, the renderer should blit that surface directly.
        - Otherwise, the renderer should fetch the sprite image using `id` (+ optional `frame`)
        from the sprite sheet / asset system.

        Sorting
        - `render_order` is a tuple used as the sort key. This gives you flexible multi-key
        ordering (e.g., shade level, y-depth, z-height, tie-breakers).

        Debug / collision overlays
        - `location` and `size` are optional world-space values the renderer/debug tools
        can use to draw hitboxes or other overlays.
        - `isShadow` can be used to exclude shadows from debug overlays or special passes.

        Tinting
        - `mask` is an optional RGBA tint applied by the AssetDrawer before blitting.
    """

    # Sprite asset ID (index into sprite/tile sheet manager). May be None if `img` is used.
    id: Optional[int]

    # Where to draw on screen (view/screen coords). Typically a 2-element numpy array [x, y].
    draw_location: NDArray[np.float64]

    # Used for sorting draw calls front-to-back (or any custom order you want).
    render_order: Tuple[float, ...]

    # True if this render object represents a shadow (can be treated specially by debug/tools).
    isShadow: bool = False

    # Optional world-space hitbox info (for debug rendering).
    location: Optional[Coord] = None
    size: Optional[Coord] = None

    # Optional prebuilt image to blit directly (bypasses id/frame lookup).
    img: Optional[pygame.Surface] = None

    # Optional animation frame (used when fetching from a sheet).
    frame: Optional[int] = None

    # Optional RGBA tint mask.
    mask: Optional[RGBA] = None