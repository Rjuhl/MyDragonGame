import pygame
import numpy as np
from utils.coords import Coord


def generate_shadow_ellipse(length: float, width: float, fade:float, rotation: int = None) -> pygame.Surface:
    length *= Coord.BASIS[0][0]
    width *= Coord.BASIS[1][0]

    return make_ellipse_surface(length // 1, width // 1, (0, 0, 0, 120))


def make_ellipse_surface(length_px: int, width_px: int, color) -> pygame.Surface:
    """Return a transparent surface with an ellipse drawn inside a rect of size (length_px, width_px)."""
    surf = pygame.Surface((length_px * 2, width_px * 2), pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, length_px * 2, width_px * 2)
    
    pygame.draw.ellipse(surf, color, rect, 0)
    return surf




