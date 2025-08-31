from typing import List, Dict
from system.entities.entity import Entity


class Tree(Entity):
    IMG_ID = None
    def __init__(self, location, size, render_size):
        super().__init__(location, size, self.IMG_ID, render_size)