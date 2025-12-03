import math
from collections import defaultdict
from itertools import combinations
from constants import SPATIAL_GRID_PARITION_SIZE
from utils.coords import Coord
from utils.generate_unique_entity_pair_string import generate_unique_entity_pair_string
from system.entities.sprites.player import Player
from system.entities.sprites.tree import Tree
from system.entities.entity import EntitySubscriber
from system.entities.physics.collisions import center_hit_box


class SpatialHashGrid(EntitySubscriber):
    def __init__(self, partition=SPATIAL_GRID_PARITION_SIZE):
        self.partition = partition
        self.location_to_entity_map = defaultdict(list)
    
    def add_entity(self, entity):
        entity.add_movement_subscriber(self)
        for location in self.convert_location_to_keys(entity.location, entity.size):
            self.location_to_entity_map[location].append(entity)
        return self

    def remove_entity(self, entity):
        location_keys = self.convert_location_to_keys(entity.location, entity.size)
        for location in location_keys:
            self.location_to_entity_map[location].remove(entity)
        self.clean_grid_location(location_keys)
        return self

    def receive_movement_event(self, entity):
        prev_location = self.convert_location_to_keys(entity.prev_location, entity.size)
        curr_location = self.convert_location_to_keys(entity.location, entity.size)
        if prev_location != curr_location:
            for location in prev_location:
                self.location_to_entity_map[location].remove(entity)
            for location in curr_location:
                self.location_to_entity_map[location].append(entity)
            self.clean_grid_location(prev_location)

    def clean_grid_location(self, location_keys):
        # Clean up Grid to keep mem footprint small and looping over it quicker
        for location in location_keys:
            if len(self.location_to_entity_map[location]) == 0:
                del self.location_to_entity_map[location]
    
    def convert_location_to_keys(self, location, size):
        # Not that entity location represent centers we first need to get top_left to get box 
        location, _ = center_hit_box(location, size)
        return {
            self.convert_to_key(location.x, location.y),
            self.convert_to_key(location.x + size.x, location.y),
            self.convert_to_key(location.x, location.y + size.y),
            self.convert_to_key(location.x + size.x, location.y + size.y),
        }


    def get_possible_onscreen_collisions(self, min_x, max_x, min_y, max_y):
        unique_collision_pairs = {}
        for x in range(min_x - self.partition, max_x + self.partition, self.partition):
            for y in range(min_y - self.partition, max_y + self.partition, self.partition):
                self.add_pairs_from_grid(x, y, unique_collision_pairs)
        return unique_collision_pairs

    def add_pairs_from_grid(self, x, y, unique_collision_pairs):
        key = self.convert_to_key(x, y)
        entities = self.location_to_entity_map[key]
        if len(entities) == 0: del self.location_to_entity_map[key]
        for e1, e2 in combinations(entities, 2):
            key = generate_unique_entity_pair_string(e1, e2)
            unique_collision_pairs[key] = [e1, e2]

    def convert_to_key(self, x, y):
        return tuple([x // self.partition, y // self.partition])
    
    def get_entities_in_range(self, x, y, dx, dy, exception=Player, strict=True, remove_entities=False):
        """ Getting all entities in range (x, y) to (x + dx, y - dy) """
        entities = set()
        for i in range(-self.partition, dx + self.partition, self.partition):
            for j in range(-self.partition, dy + self.partition, self.partition):
                keys = self.convert_location_to_keys(
                    Coord.math(x + i, y - j, 0), 
                    Coord.math(0, 0, 0)
                )

                # Note len(keys) == 1 should always be true
                first_key = next(iter(keys))
                for entity in self.location_to_entity_map[first_key]:

                    # If strict, count entity location as single location point instead of 
                    # the space it occupies and must be with in (x, y) to (x + dx, y - dy)
                    if strict:      
                        ex, ey, _ = entity.location.location

                        # Tree are placed offset from the gensis, so there is an exception for them
                        delta = 0.5 if isinstance(entity, Tree) else 0
                        if not (x - delta <= ex < x + dx - delta) or not (y - dy + delta < ey <= y + delta): 
                            continue

                    if not isinstance(entity, exception):
                        entities.add(entity)
        
        if remove_entities: 
            for entity in entities: self.remove_entity(entity)

        return entities
    