import pygame
from world.tile import Tile
from utils.coords import Coord
from system.entities.physics.collisions import check_collision
from typing import List, Optional, Tuple
from constants import TILE_GROUP_DRAW_SIZE, TILE_SIZE, TILE_ASSET_SHOWN_SIZE

class TileGroup:
    def __init__(self, tile_imgs: List[pygame.Surface]):
        self._tile_imgs = tile_imgs
        self._has_tiled_changed = False
        self._tiles: List[Tile] = []
        self.tile_group_surface: Optional[pygame.Surface] = None
        self._tile_group_top_left: Tuple[int, int] = (0, 0)


    def add_tile(self, tile: Tile):
        self._has_tiled_changed = True
        self._tiles.append(tile)
        tile.subscribe(self)
    
    def tile_upate(self, tile: Tile):
        self._has_tiled_changed = True
    
    def _build_tile_group_surface(self):
        min_x, min_y, w, h = self._get_bounding_box()
        tile_group = pygame.Surface((w, h), flags=pygame.SRCALPHA).convert_alpha()

        self._tile_group_top_left = (min_x, min_y)

        for tile in self._tiles:
            tile_img = self._tile_imgs[tile.id]
            center_view = tile.location.as_view_coord()
            rect_view = tile_img.get_rect(center=center_view)

            # shift so that view(min_x, min_y) maps to chunk(0,0)
            rect = rect_view.move(-min_x, -min_y)
            tile_group.blit(tile_img, rect)

        self.tile_group_surface = tile_group
        self._has_tiled_changed = False


    def get_surface(self, region: Tuple[Coord, Coord]) -> Optional[Tuple[pygame.Surface, Tuple[int, int]]]:
        if self.tile_group_surface is None or self._has_tiled_changed == True:
            self._build_tile_group_surface()

        return (self.tile_group_surface, self._tile_group_top_left) if self._is_overlaping(region) else None

    def _is_overlaping(self, region: Tuple[Coord, Coord]):
        region_location, region_size = region
        tile_group_location = Coord.world(self._tiles[0].location.x, self._tiles[-1].location.y)
        tile_group_size = Coord.world(TILE_GROUP_DRAW_SIZE, TILE_GROUP_DRAW_SIZE, 1)
        return check_collision(
            tile_group_location, tile_group_size,
            region_location, region_size
        )

    def _get_bounding_box(self) -> Tuple[int, int, int, int]:
        """
            Returns (min_x, min_y, width, height) in VIEW coords.

            Uses the assumption:
            - tiles[0] is one corner
            - tiles[-1] is the opposite corner
        """

        # Get the tl and br in world coords
        top_left, bottom_right = self._tiles[0].location, self._tiles[-1].location

        # Create tr and bl from what we know about tl and br
        top_right = Coord.world(bottom_right.x, top_left.y)
        bottom_left = Coord.world(top_left.x, bottom_right.y)

        # Convert to view corrd
        top_left = top_left.as_view_coord()
        bottom_right = bottom_right.as_view_coord()
        top_right = top_right.as_view_coord()
        bottom_left = bottom_left.as_view_coord()

        # Note location measure top left position so some positions  
        # need adjusting by tile size to get the proper bounding box
        max_x = top_right[0] + TILE_ASSET_SHOWN_SIZE[0]
        min_x = bottom_left[0]
        min_y = top_left[1]
        max_y = bottom_right[1] + TILE_ASSET_SHOWN_SIZE[0]

        return min_x - TILE_ASSET_SHOWN_SIZE[1], min_y - TILE_ASSET_SHOWN_SIZE[1], max_x - min_x, max_y - min_y

