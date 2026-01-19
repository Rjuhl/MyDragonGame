from collections import defaultdict
from itertools import combinations
from typing import Tuple, Self, Set, Dict

from utils.coords import Coord
from system.entities.sprites.tree import Tree
from system.entities.sprites.player import Player
from system.entities.entity import Entity, EntitySubscriber

from constants import SPATIAL_GRID_PARITION_SIZE
from system.entities.physics.collisions import center_hit_box
from utils.generate_unique_entity_pair_string import generate_unique_entity_pair_string


# Grid key type: (cell_x, cell_y)
GridKey = Tuple[int, int]

# Dict containing possiable collisions between entities  
CollisionPairs = Dict[str, Tuple[Entity]]


class SpatialHashGrid(EntitySubscriber):
    """
        Spatial hash grid for broad-phase collision / proximity queries.

        Entities are bucketed into square cells of size `partition` (world units).
        For each entity we insert up to 4 keys corresponding to the corners of its hitbox.
        This is a fast broad-phase filter; exact collision should be checked elsewhere.
    """

    def __init__(self, partition=SPATIAL_GRID_PARITION_SIZE):
        self.partition = partition

        # Map grid cell -> list of entities whose hitbox overlaps that cell.
        self.location_to_entity_map = defaultdict(list)
    
    # -------------------------------------------------------------------------
    # Entity lifecycle
    # -------------------------------------------------------------------------

    def add_entity(self, entity: Entity) -> Self:
        """ Add entity to all relevant grid cells and subscribe to movement updates """
        entity.add_movement_subscriber(self)
        for location in self.convert_location_to_keys(entity.location, entity.size):
            self.location_to_entity_map[location].append(entity)
        return self

    def remove_entity(self, entity: Entity) -> Self:
        """ Remove entity from all relevant grid cells """
        location_keys = self.convert_location_to_keys(entity.location, entity.size)
        for location in location_keys:
            self.location_to_entity_map[location].remove(entity)
        self.clean_grid_location(location_keys)
        return self

    def receive_movement_event(self, entity: Entity) -> None:
        """
        Movement subscriber hook. Updates which grid cells the entity occupies.
        Only updates when the set of keys changes to avoid unnecessary churn.
        """
        prev_location = self.convert_location_to_keys(entity.prev_location, entity.size)
        curr_location = self.convert_location_to_keys(entity.location, entity.size)
        if prev_location != curr_location:
            for location in prev_location:
                self.location_to_entity_map[location].remove(entity)
            for location in curr_location:
                self.location_to_entity_map[location].append(entity)
            self.clean_grid_location(prev_location)

    # -------------------------------------------------------------------------
    # Broad-phase collision pairing
    # -------------------------------------------------------------------------

    def get_possible_onscreen_collisions(self, min_x: int, max_x: int, min_y: int, max_y: int) -> CollisionPairs:
        """
        Return a dict of unique entity pairs that *might* collide on screen

        We iterate over cells in and around the viewport and create all pairs
        within each cell. Dedup is done via generate_unique_entity_pair_string()
        """
        unique_collision_pairs = {}
        for x in range(min_x - self.partition, max_x + self.partition, self.partition):
            for y in range(min_y - self.partition, max_y + self.partition, self.partition):
                self.add_pairs_from_grid(x, y, unique_collision_pairs)
        return unique_collision_pairs
    
    def add_pairs_from_grid(self, x: int, y: int, unique_collision_pairs: CollisionPairs) -> None:
        """ Add all unique pairs from the single grid cell containing (x, y) """
        key = self.convert_to_key(x, y)
        entities = self.location_to_entity_map[key]
        if len(entities) == 0: del self.location_to_entity_map[key]
        for e1, e2 in combinations(entities, 2):
            key = generate_unique_entity_pair_string(e1, e2)
            unique_collision_pairs[key] = [e1, e2]

    # -------------------------------------------------------------------------
    # Range query
    # -------------------------------------------------------------------------

    def get_entities_in_range(
        self, 
        x: int, y: int, 
        dx: int, dy: int, 
        exception: type = Player, 
        strict: bool = True, 
        remove_entities: bool = False
    ) -> Set[Entity]:
        """
            Return entities in the axis-aligned query rectangle.

            Rectangle is defined as:
                left   = x
                right  = x + dx
                top    = y
                bottom = y - dy

            Parameters
            ----------
            exception:
                Entities of this type are excluded from results (defaults to Player).
            strict:
                If True, entities are filtered by their *center location* being within the rectangle,
                rather than by whether their occupied grid cells overlap it.
            remove_entities:
                If True, all returned entities are removed from the grid.
        """
        entities = set()

        # Iterate candidate cells overlapping the rectangle, padded by 1 cell.
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
    
    # -------------------------------------------------------------------------
    # Keying helpers
    # -------------------------------------------------------------------------

    def clean_grid_location(self, location_keys: Set[GridKey]) -> None:
        """ Remove any empty cell lists to keep memory footprint small """
        for location in location_keys:
            if len(self.location_to_entity_map[location]) == 0:
                del self.location_to_entity_map[location]
    
    def convert_location_to_keys(self, location: Coord, size: Coord) -> Set[GridKey]:
        """ Convert an entity's center location + size into the set of occupied grid cell keys """
        location, _ = center_hit_box(location, size)
        return {
            self.convert_to_key(location.x, location.y),
            self.convert_to_key(location.x + size.x, location.y),
            self.convert_to_key(location.x, location.y + size.y),
            self.convert_to_key(location.x + size.x, location.y + size.y),
        }

    def convert_to_key(self, x: float, y: float) -> GridKey:
        """ Convert world coordinates to grid cell coordinate """
        return tuple([x // self.partition, y // self.partition])
    