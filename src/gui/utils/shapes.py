import pygame

def draw_rect_surface(fill_color, outline_color, thickness, w, h, corner_radius=0):
    """
    Creates a Pygame surface with a filled rectangle and an outline.

    Args:
        fill_color (tuple): RGB fill color.
        outline_color (tuple): RGB outline color.
        thickness (int): Border thickness.
        w (int): Width of the rectangle surface.
        h (int): Height of the rectangle surface.
        corner_radius (int): Rounded corner radius.

    Returns:
        pygame.Surface: A surface containing the drawn rectangle.
    """

    # Create the surface with per-pixel alpha so rounded edges look clean
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    rect = pygame.Rect(0, 0, w, h)

    # Draw filled part
    pygame.draw.rect(
        surf,
        fill_color,
        rect,
        border_radius=corner_radius
    )

    # Draw outline (if thickness > 0)
    if thickness > 0:
        pygame.draw.rect(
            surf,
            outline_color,
            rect,
            width=thickness,
            border_radius=corner_radius
        )

    return surf
