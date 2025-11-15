import pygame
from utils.coords import Coord


def generate_shadow_ellipse(length: float, width: float, fade: float, rotation: int | None = None) -> pygame.Surface:
    # Scale however you like; keeping your original idea:
    length_px = int(length * Coord.BASIS[0][0])
    width_px = int(width * Coord.BASIS[1][0])

    # Tune inner/outer alpha and number of steps
    shadow = make_gradient_ellipse(
        length_px=length_px,
        width_px=width_px,
        inner_alpha=160 if fade else 120,
        outer_alpha=0,
        steps=32,
        fade=fade,
        color=(0, 0, 0)
    )
    

    if rotation is not None and rotation % 360 != 0:
        shadow = pygame.transform.rotate(shadow, -rotation % 360)

    return shadow


def make_gradient_ellipse(
    length_px: int,
    width_px: int,
    color=(0, 0, 0),
    inner_alpha=160,
    outer_alpha=0,
    steps=64,
    fade=1.5
) -> pygame.Surface:
    """
    Create a transparent surface with a soft ellipse shadow where opacity
    increases toward the center.

    - inner_alpha: alpha at the core
    - outer_alpha: alpha at the very edge
    - steps: number of concentric fills (higher = smoother, slower)
    - fade: curve exponent; >1 steeper near center, <1 gentler
    """
    steps = max(1, min(steps, length_px, width_px))

    surf_w, surf_h = length_px * 2, width_px * 2
    surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, surf_w, surf_h)

    for i in range(steps, 0, -1):
        t = i / steps     
        a = outer_alpha + (inner_alpha - outer_alpha) * (1 - t) ** fade
        pygame.draw.ellipse(surf, (*color, int(a)), rect, 0)
        rect.inflate_ip(-2, -2)

    return surf
