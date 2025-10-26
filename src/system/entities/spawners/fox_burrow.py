from utils.coords import Coord
from system.entities.entity_manager import EntityManager
from system.entities.sprites.fox import Fox
from system.entities.spawner import Spawner, SpawnerArgs


class FoxBurrow(Spawner):
    def __init__(self, location: Coord, entity_manager: EntityManager):
        size = Coord.math(2, 2, 1)
        render_offset = Coord.world(-1, 0)
        img_id = 5

        spawner_args = SpawnerArgs(
            4, 3e-4, 60 * 1000, 40, 
            entity_manager, Fox,
            lambda: Fox()
        )


        super().__init__(location, size, img_id, render_offset, spawner_args)

        
    
    
    