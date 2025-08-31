import numpy as np
from typing import List, Dict
from system.game_clock import game_clock
from system.entities.physics.collisions import check_collision, resolve_collisions
from system.entities.physics.spatial_hash_grid import SpatialHashGrid
from system.screen import Screen
from system.entities.entity import Entity
from system.entities.physics.vec3 import Vec3
from constants import TILE_SIZE, DISPLAY_SIZE, WORLD_HEIGHT


class EntityManager:
    def __init__(self, screen: Screen):
        self.screen = screen
        self.spatial_hash_grid = SpatialHashGrid()
        self.entities = set()
    
    def add_entity(self, entity: Entity) => None:
        entity.bind_to_manager(self)
        self.entities.add(entity)
        self.spatial_hash_grid.add_entity(entity)

    # Updates all entities and returns a list of them to render
    def update_entities(self) -> List[Entity]:
        dt = game_clock.dt
        screen_size, screen_location = self.screen.git_hitbox()

        entities_on_screen = []
        for entity in self.entities:
            onscreen = check_collision(entity.location, entity.size, screen_location, screen_size)
            entity.update(dt, onscreen)
            if onscreen: entities_on_screen.append(entity)
        
        resolve_collisions(self.spatial_hash_grid.get_possible_onscreen_collisions(*self.screen.get_bounding_box()))

        entities_on_screen.sort(key = lambda e: (e.location.z, e.location.x, e.location.y))

        return entities_on_screen

    
