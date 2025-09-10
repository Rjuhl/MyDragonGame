
import math
import pygame
import numpy as np
from pathlib import Path
from utils.coords import Coord
from constants import DISPLAY_SIZE, PADDING, TILE_SIZE, WORLD_HEIGHT, TRACKING_BOX_SCALE
from utils.coords import Coord
from system.entities.entity import Entity
from system.entities.physics.collisions import check_collision

class Screen:
    DELEMITER = ","
    PATH = Path(__file__).parent.parent.parent / 'data'
    def __init__(self):
        self.coord = None
        self.tracking_box = Entity.dummy()
        self.anchor = Entity.dummy()
        self.center_anchor()
        self.init_tracking_box(TRACKING_BOX_SCALE)

        self.cam_offset = np.floor(Coord.BASIS @ self.location())[:-1]
    
    @classmethod
    def load(cls, id=""):
        return Screen()

        path = cls.PATH / f"screen{id}"
        if path.exists():
            x, y = path.read_text(encoding='utf-8')
            return Screen(float(x), float(y))
        return Screen(0, 0)


    def location(self): return self.coord.location

    # def save(self, id=""):
    #     path = self.path / f"screen{id}"
    #     x, y = self.location()
    #     path.write_text(f"{x}{self.DELEMITER}{y}", encoding='utf-8')

    def update(self):
        if not self.anchor_in_tracking_box():
            delta = self.anchor.last_drawn_location - self.anchor.prev_drawn_location
            self.coord.update_as_view_coord(*delta) 
            self.cam_offset += delta
        
        
        

    def get_corners(self):
        return [
            self.coord.as_world_coord(),
            self.coord.copy().update_as_view_coord(DISPLAY_SIZE[0], 0).as_world_coord(),
            self.coord.copy().update_as_view_coord(0, DISPLAY_SIZE[1]).as_world_coord(),
            self.coord.copy().update_as_view_coord(*DISPLAY_SIZE).as_world_coord(),
        ]
    
    def get_bounding_box(self, padding=PADDING):
        corners = self.get_corners()
        min_x = math.floor(min(x for x, _, _ in corners)) - padding
        max_x = math.ceil(max(x for x, _, _ in corners)) + padding
        min_y = math.floor(min(y for _, y, _ in corners)) - padding
        max_y = math.ceil(max(y for _, y, _ in corners)) + padding

        return min_x, max_x, min_y, max_y
        
    def get_hitbox(self):
        min_x, max_x, min_y, max_y = self.get_bounding_box()
        size = Coord(np.array([
            max_x - min_x,
            max_y - min_y,
            WORLD_HEIGHT
        ]))

        location = Coord(np.array([min_x, min_y, 0]))

        return location, size
    
    # Used to move screen with player
    def init_tracking_box(self, scale):
        box_dims = Coord.math(
            (DISPLAY_SIZE[0] * scale) / TILE_SIZE,
            (DISPLAY_SIZE[1] * scale) / TILE_SIZE,
            WORLD_HEIGHT
        )
        
        box_loc = self.get_screen_center().update_as_view_coord(
            -(DISPLAY_SIZE[0] / 4),
            -(DISPLAY_SIZE[1] / 4),
        )
    
        self.tracking_box = Entity(box_loc, box_dims, None, Coord.math(0, 0, 0))

    

    def get_screen_center(self):
        return self.coord.copy().update_as_view_coord(DISPLAY_SIZE[0] / 2, DISPLAY_SIZE[1] / 2) 
    
    def center_anchor(self):
        self.coord = self.anchor.location.copy()
        self.coord.update_as_view_coord(-DISPLAY_SIZE[0] / 2, -DISPLAY_SIZE[1] / 2)

    def get_tracking_box(self, screen_axis=True):
        d1, d2 = DISPLAY_SIZE[0] * TRACKING_BOX_SCALE, DISPLAY_SIZE[1] * TRACKING_BOX_SCALE
        dx, dy = (1 - TRACKING_BOX_SCALE) * DISPLAY_SIZE[0] / 2, (1 - TRACKING_BOX_SCALE) * DISPLAY_SIZE[1] / 2
        
        bl = self.coord.copy().update_as_view_coord(dx, dy)
        br = bl.copy().update_as_view_coord(d1, 0)
        tl = bl.copy().update_as_view_coord(0, d2)
        tr = bl.copy().update_as_view_coord(d1, d2)

        if screen_axis:
            return [
                tl.as_view_coord(),
                tr.as_view_coord(),
                bl.as_view_coord(),
                br.as_view_coord(),
            ]

        return tl, tr, bl, br

    def anchor_in_tracking_box(self):
        screen_box = self.get_tracking_box()
        location, size = self.anchor.location.copy(), self.anchor.size.copy()
        return any([
            self.check_point_in_square(location.as_view_coord(), screen_box),
            self.check_point_in_square((location + Coord.math(size.x, 0, 0)).as_view_coord(), screen_box),
            self.check_point_in_square((location + Coord.math(0, size.y, 0)).as_view_coord(), screen_box),
            self.check_point_in_square((location + size).as_view_coord(), screen_box)
        ])

    @staticmethod
    def check_point_in_square(point, square):
        x, y = point
        tl, tr, bl, _ = square
        return tl[0] <= x <= tr[0] and bl[1] <= y <= tl[1]
