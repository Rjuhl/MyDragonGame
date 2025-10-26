from system.entities.entity import Entity
from system.game_clock import game_clock
from system.entities.entity_manager import EntityManagerSubscriber
from utils.math import distance_between_coords
from typing import List, Dict, Callable
from dataclasses import dataclass


@dataclass
class SpawnerArgs:
    spawn_limit: int
    probabilty: float
    recharge_time: float 
    vicinity_to_player: float
    entity_to_spawn: Entity
    spawn_entity: Callable[[], Entity]

    
class Spawner(Entity, EntityManagerSubscriber):
    def __init__(self, location, size, img_id, render_offset, spawner_args):
        super().__init__(location, size, img_id, render_offset)
        self.spawn_limit = spawner_args.spawn_limit
        self.probabilty = spawner_args.probabilty
        self.recharge_time = spawner_args.recharge_time
        self.vicinity_to_player = spawner_args.vicinity_to_player
        self.spawn_entity = spawner_args.spawn_entity

        self.last_spawn_time = float('inf')
        self.alive_entities_spawned = 0
    
    def update(self, dt, _):
        self.last_spawn_time += dt

        if self.within_player_spawn_distance() \
           and self.within_spawn_cooltime_period() \
           and self.within_spawn_limit(): self.spawn_entity()
    
    def spawn_entity(self):
        entity = self.spawn_entity()
        self.manager.add_entity(entity)
        self.manager.add_kill_listener_subscriber(self)

        self.last_spawn_time = 0
        self.alive_entities_spawned += 1

    def within_spawn_cooltime_period(self):
        return self.last_spawn_time < self.recharge_time

    def within_spawn_limit(self):
        return self.alive_entities_spawned < self.spawn_limit
    
    def within_player_spawn_distance(self):
        if self.manager.player is None: return False
        return distance_between_coords(self.location, self.manager.player) < self.vicinity_to_player

    def recieve_death_event(self):
        self.alive_entities_spawned -= 1
     
    # Need to work out loading and unloading and making sure we are still tracking the entities we spawned