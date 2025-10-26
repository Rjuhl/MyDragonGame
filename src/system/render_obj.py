import pygame
from typing import Optional
from utils.coords import Coord
import numpy as np
from numpy.typing import NDArray


class RenderObj:
    def __init__(
            self, 
            id: Optional[int], 
            draw_location: NDArray[np.float64], 
            render_order: tuple[float], 
            isShadow: bool = False, 
            location: Optional[Coord] = None, size: Optional[Coord] = None,
            img: Optional[pygame.Surface] = None,
            frame: Optional[int] = None
        ):
        self.id = id
        self.draw_location = draw_location
        self.render_order = render_order
        self.isShadow = isShadow
        self.location = location
        self.size = size
        self.img = img
        self.frame = frame
