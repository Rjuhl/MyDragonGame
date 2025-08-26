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
            tuple([location.x // self.partition, location.y // self.partition]),
            tuple([(location.x + size.x) // self.partition, location.y // self.partition]),
            tuple([location.x // self.partition, (location.y + size.y) // self.partition]),
            tuple([(location.x + size.x) // self.partition, (location.y + size.y) // self.partition])
        ])

    # TODO: finish this method
    def get_possiable_onscreen_collisions(self, min_x, max_x, min_y, max_y):
        unique_collision_pairs = {}
        


    @staticmethod
    def generate_unique_enitity_pair_string(entity1, entity2):
        return str(entity1.id) + str(entity2.id) if entity1.id < entity2.id else str(entity2.id) + str(entity1.id)