import math
import numpy as np
from pathlib import Path
from typing import List, Tuple
from numpy.typing import NDArray

from utils.coords import Coord
from system.entities.entity import Entity
from utils.types.shade_levels import ShadeLevel
from system.entities.physics.shadows import Triangle, Receiver
from constants import DISPLAY_SIZE, PADDING, TILE_SIZE, WORLD_HEIGHT, TRACKING_BOX_SCALE

class Screen:
    """
        Camera / viewport manager.

        This class tracks a world-space 'top-left' screen coordinate (`self.coord`) that
        represents the camera position. It also maintains:
        - an 'anchor' entity (usually the player) that the camera tries to keep inside
        a tracking rectangle (the "tracking box") on the screen
        - a `cam_offset` in view/screen space used to shift rendering
    """

    PATH = Path(__file__).parent.parent.parent / 'data'

    def __init__(self):
        # Screen trackers
        self.coord = None
        self.tracking_box = Entity.dummy()
        self.anchor = Entity.dummy()

        # Initialize camera centered on anchor and build tracking box.
        self.center_anchor()
        self.init_tracking_box(TRACKING_BOX_SCALE)

        # Cached view/screen-space camera offset (used for rendering transforms).
        self.cam_offset = np.floor(Coord.BASIS @ self.location())[:-1]
    
    @classmethod
    def load(cls, id=""):
        return Screen()
    
    # -------------------------------------------------------------------------
    # Core state
    # -------------------------------------------------------------------------

    def location(self) -> NDArray: 
        return self.coord.location

    def update(self) -> None:
        """
        Update camera position for this tick.

        If the anchor (player) leaves the tracking box, move the camera by the
        anchor's view-space delta since the last frame. This keeps the anchor
        within the tracking box without "snapping" every frame.
        """

        if not self.anchor_in_tracking_box():
            delta = self.anchor.last_drawn_location - self.anchor.prev_drawn_location
            self.coord.update_as_view_coord(*delta) 
            self.cam_offset += delta

    # -------------------------------------------------------------------------
    # View bounds / collision helpers
    # -------------------------------------------------------------------------

    def get_corners(self) -> List[NDArray]:
        """ Return the four viewport corners in world coordinates """
        return [
            self.coord.as_world_coord(),
            self.coord.copy().update_as_view_coord(DISPLAY_SIZE[0], 0).as_world_coord(),
            self.coord.copy().update_as_view_coord(0, DISPLAY_SIZE[1]).as_world_coord(),
            self.coord.copy().update_as_view_coord(*DISPLAY_SIZE).as_world_coord(),
        ]
    
    def get_bounding_box(self, padding=PADDING):
        """ Return an axis-aligned world-space bounding box that fully contains the screen """
        corners = self.get_corners()
        min_x = math.floor(min(x for x, _, _ in corners)) - padding
        max_x = math.ceil(max(x for x, _, _ in corners)) + padding
        min_y = math.floor(min(y for _, y, _ in corners)) - padding
        max_y = math.ceil(max(y for _, y, _ in corners)) + padding

        return min_x, max_x, min_y, max_y
    
    def get_hitbox(self) -> Tuple[Coord, Coord]:
        """
        Return a 3D AABB representing the visible region in world space
        Used by collision/visibility systems to determine if an entity is 'on screen'
        """

        min_x, max_x, min_y, max_y = self.get_bounding_box()
        size = Coord(np.array([
            max_x - min_x,
            max_y - min_y,
            WORLD_HEIGHT
        ]))

        location = Coord(np.array([min_x, min_y, 0]))

        return location, size

    def in_bounding_box(self, point: Coord):
        """ True if a world-space point lies inside the screen bounding box """
        min_x, max_x, min_y, max_y = self.get_bounding_box()
        return min_x <= point.x <= max_x and min_y <= point.y <= max_y

    # -------------------------------------------------------------------------
    # Shadow receiver (screen ground plane)
    # -------------------------------------------------------------------------

    def get_screen_reciever(self) -> Receiver:
        """ Return a Receiver (for shadows) representing the screen's ground plane """
        base = self.coord.copy()
        base.z = -0.1  # slightly below zero to avoid z-fighting / sorting issues
        
        # Build a CCW base plane that covers screen
        poly = [
            base.copy(),
            base.copy().update_as_view_coord(0, DISPLAY_SIZE[1]),
            base.copy().update_as_view_coord(*DISPLAY_SIZE),
            base.copy().update_as_view_coord(DISPLAY_SIZE[0], 0)
        ]

        faces = [
            Triangle([poly[0].copy(), poly[1].copy(), poly[2].copy()]),
            Triangle([poly[0].copy(), poly[2].copy(), poly[3].copy()]),
        ]

        return Receiver(faces, poly, ShadeLevel.BASE_SHADOWS)

    # -------------------------------------------------------------------------
    # Camera centering / tracking box
    # -------------------------------------------------------------------------

    def get_screen_center(self) -> Coord:
        """ Return the world coord at the center of the screen """
        return self.coord.copy().update_as_view_coord(DISPLAY_SIZE[0] / 2, DISPLAY_SIZE[1] / 2) 
    
    def center_anchor(self):
        """ Re-center the camera so the anchor entity appears in the middle of the screen """
        self.coord = self.anchor.location.copy()

        # Center based on 2D location (looks better and prevent terrain loading bugs)
        self.coord.z = 0
        self.coord.update_as_view_coord(-DISPLAY_SIZE[0] / 2, -DISPLAY_SIZE[1] / 2)

        self.cam_offset = np.floor(Coord.BASIS @ self.location())[:-1]

    # Used to move screen with player
    def init_tracking_box(self, scale: float) -> None:
        """
        Initialize the tracking box entity.

        The tracking box is an inner rectangle (scale < 1) within the screen.
        As long as the anchor stays inside it, the camera does not move.
        """

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

    def get_tracking_box(self, screen_axis: bool = True) -> List[Coord | NDArray]:
        """
        Return the tracking box corners.

        If screen_axis=True:
            returns list of corners in view coords (int arrays) in order:
              [tl, tr, bl, br]
        else:
            returns (tl, tr, bl, br) as world Coord objects.
        """

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

    def anchor_in_tracking_box(self) -> bool:
        """ True if *any* corner of the anchor's AABB is inside the tracking box (in view coords) """
        screen_box = self.get_tracking_box()
        location, size = self.anchor.location.copy(), self.anchor.size.copy()
        return any([
            self.check_point_in_square(location.as_view_coord(), screen_box),
            self.check_point_in_square((location + Coord.math(size.x, 0, 0)).as_view_coord(), screen_box),
            self.check_point_in_square((location + Coord.math(0, size.y, 0)).as_view_coord(), screen_box),
            self.check_point_in_square((location + size).as_view_coord(), screen_box)
        ])
    
    # -------------------------------------------------------------------------
    # Geometry helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def check_point_in_square(point, square):
        """
        Check if a view-space point lies inside an axis-aligned square/rect
        `square` is expected to be [tl, tr, bl, br] in view coords
        """
        x, y = point
        tl, tr, bl, _ = square
        return tl[0] <= x <= tr[0] and bl[1] <= y <= tl[1]
