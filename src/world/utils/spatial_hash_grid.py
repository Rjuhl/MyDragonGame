from collections import defaultdict
from constants import SPATIAL_GRID_PARITION_SIZE


class SpatialHashGrid:
    def __init__(self, partition=SPATIAL_GRID_PARITION_SIZE):
        self.partition = partition
        self.location_to_entity_map = defaultdict(list)
    
    def add_enitity(self, entity):
        entity.add_movement_subscriber(self)
        location_keys = self.convert_location_to_key(entity.location, entity.size)
        for location in location_keys:
            self.location_to_entity_map[location].append(entity)
        return self
    
    def remove_entity(self, entity):
        location = self.convert_location_to_keys(entity.location, entity.size)
        self.location_to_entity_map[location].remove(entity)
        self.clean_grid_location(location)
        return self

    def recieve_movement_event(self, entity):
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
        return set([
            self.convert_to_key(location.x, location.y),
            self.convert_to_key(location.x + size.x, location.y),
            self.convert_to_key(location.x, location.y + size.y),
            self.convert_to_key(location.x + size.x, location.y + size.y)
        ])


    # TODO: finish this method
    def get_possiable_onscreen_collisions(self, min_x, max_x, min_y, max_y):
        unique_collision_pairs = {}
        for x in range(min_x // self.partition, (max_x // self.partition) + 1):
            for y in range(min_x // self.partition, (max_x // self.partition) + 1):
                self.add_pairs_from_grid(x, y, unique_collision_pairs)
        
        return unique_collision_pairs

    def add_pairs_from_grid(self, x, y, unique_collision_pairs):
        entities = self.location_to_entity_map[self.convert_to_key(x, y)]
        for i in range(len(entities) - 1):
            for j in range(i + 1, len(entities)):
                entity_string = self.generate_unique_enitity_pair_string(entities[i], entities[j])
                unique_collision_pairs[entity_string] = [entities[i], entities[j]]

    def convert_to_key(self, x, y):
        return tuple([x // self.partition, y // self.partition])

    @staticmethod
    def generate_unique_enitity_pair_string(entity1, entity2):
        return str(entity1.id) + str(entity2.id) if entity1.id < entity2.id else str(entity2.id) + str(entity1.id)