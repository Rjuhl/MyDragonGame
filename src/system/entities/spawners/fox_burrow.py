from utils.coords import Coord
from system.entities.entity_manager import EntityManager
from system.entities.sprites.fox import Fox
from system.entities.spawner import Spawner, SpawnerArgs
from decorators import register_entity

@register_entity
class FoxBurrow(Spawner):
    def __init__(self, location: Coord): # Remove entity manager from init and have enity manager bind to the entity
        size = Coord.math(2, 2, 1)
        render_offset = Coord.world(-1, 0)
        img_id = 5

        spawner_args = SpawnerArgs(
            4, 3e-4, 60 * 1000, 40, 
            Fox, lambda: Fox()
        )


        super().__init__(location, size, img_id, render_offset, spawner_args)

    @classmethod
    def load(cls, data):
        return FoxBurrow(Coord.load(data["location"]))

    