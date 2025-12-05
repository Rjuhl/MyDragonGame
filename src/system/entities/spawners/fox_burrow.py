from utils.coords import Coord
from system.entities.entity_manager import EntityManager
from system.entities.sprites.fox import Fox
from system.entities.spawner import Spawner, SpawnerArgs
from utils.types.shade_levels import ShadeLevel
from world.tile import Tile
from decorators import register_entity, spawn_with_chunk_creation
from constants import FOX_BURROW_WIEGHT

FOX_BURROW_SIZE = Coord.math(1, 1, 0)
def _fb_valid_spawner_location(tile: Tile) -> bool:
    return not tile.has_obsticle and not tile.is_water and tile.id != 12

@register_entity
@spawn_with_chunk_creation(
    FOX_BURROW_SIZE, 
    FOX_BURROW_WIEGHT,
    _fb_valid_spawner_location
)
class FoxBurrow(Spawner):
    def __init__(self, tile: Tile):
        
        render_offset = Coord.world(-1, 0)
        img_id = 7 + int(6 <= tile.id <= 11)
        spawner_args = SpawnerArgs(4, 60 * 1000, 40)
        super().__init__(tile.location, FOX_BURROW_SIZE, img_id, render_offset, spawner_args)

    def shade_level(self):
        return ShadeLevel.GROUND_MASK

    @classmethod
    def load(cls, data):
        tile = Tile(0, Coord.load(data["location"]))
        fox_burrow = FoxBurrow(tile)
        fox_burrow.img_id = data["img_id"]
        fox_burrow.set_spawner_data(data)
        return fox_burrow
    