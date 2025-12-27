from world.tile import Tile
from utils.coords import Coord
from system.render_obj import RenderObj
from utils.types.shade_levels import ShadeLevel
from system.entities.spawner import Spawner, SpawnerArgs
from system.entities.sprites.wizard import Wizard
from decorators import register_entity, spawn_with_chunk_creation
from constants import WORLD_HEIGHT, TILE_SIZE, OUTPOST_WEIGHT
from typing import List


OUTPOST_SIZE = Coord.math(2, 2, 1 + WORLD_HEIGHT // TILE_SIZE)
def _op_valid_spawner_location(tile: Tile) -> bool:
    return not tile.has_obsticle and not tile.is_water


@register_entity
@spawn_with_chunk_creation(
    OUTPOST_SIZE, 
    OUTPOST_WEIGHT,
    _op_valid_spawner_location
)
class Outpost(Spawner):
    IMG_ID = 9
    def __init__(self, tile: Tile):
        render_offset = Coord.math(0, -32, 0)
        spawner_args = SpawnerArgs(1, 30 * 1000, 160) # Change first arg to start spawning (prolly to ~6)
        super().__init__(tile.location, Coord.math(2.5,  2.5, 6), self.IMG_ID, render_offset, spawner_args)

    
    def create_entity(self):
        return Wizard(self.location + Coord.math(2, 0, 0), home=self.id)

    @classmethod
    def load(cls, data):
        tile = Tile(0, Coord.load(data["location"]))
        outpost = Outpost(tile)
        outpost.set_spawner_data(data)
        return outpost