from system.entities.entity import Entity
from system.game_clock import game_clock
from system.entities.entity_manager import EntityManagerSubscriber
from utils.coords import Coord
from world.tile import Tile
from typing import List, Dict, Callable, Any
from dataclasses import dataclass


@dataclass
class SpawnerArgs:
    spawn_limit: int
    recharge_time: float 
    vicinity_to_player: float
    
class Spawner(Entity, EntityManagerSubscriber):
    SIZE: Coord = Coord.math(0, 0, 0)
    SPAWN_PROBABLITY: float = 0
    CAN_SPAWN_SPAWNER: Callable[[Tile], None] = lambda _: False

    def __init__(self, location, size, img_id, render_offset, spawner_args, id=None):
        super().__init__(location, size, img_id, render_offset, id=id)
        self.spawn_limit = spawner_args.spawn_limit
        self.recharge_time = spawner_args.recharge_time
        self.vicinity_to_player = spawner_args.vicinity_to_player

        self.last_spawn_time = self.recharge_time
        self.entities: set[int] = set()

    def bind_to_manager(self, manager):
        super().bind_to_manager(manager)
        self.manager.add_kill_listener_subscriber(self)
    
    def update(self, dt, _):
        self.last_spawn_time += dt

        if self.within_player_spawn_distance() \
           and self.within_spawn_cooltime_period() \
           and self.within_spawn_limit(): self.spawn_entity()
    
    def spawn_entity(self):
        entity = self.create_entity()
        self.manager.queue_entity_addition(entity)
        self.entities.add(entity.id)
        self.last_spawn_time = 0

    def within_spawn_cooltime_period(self):
        return self.last_spawn_time > self.recharge_time

    def within_spawn_limit(self):
        return len(self.entities) < self.spawn_limit
    
    def within_player_spawn_distance(self):
        if self.manager.player is None: return False
        return self.location.euclidean_2D(self.manager.player.location) < self.vicinity_to_player

    def recieve_death_event(self, entity: Entity):
        if entity.id in self.entities: self.entities.remove(id)
    

    def jsonify(self):
        data = super().jsonify()
        data["bound_entitites"] = list(self.entities)
        data["last_spawn_time"] = self.last_spawn_time
        return data
    

    def set_spawner_data(self, data):
        self.entities = set(data["bound_entitites"])
        self.last_spawn_time = data["last_spawn_time"]         

    # ---------------------------------------------------- #
    # -----    Abstract Methods (Need Overwrite)    ------ #
    # ---------------------------------------------------- #
    def create_entity() -> Entity:
        pass

       