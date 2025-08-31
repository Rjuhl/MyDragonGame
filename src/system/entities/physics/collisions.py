from enum import Enum
from system.entities.entity import Entity
from utils.generate_unique_entity_pair_string import generate_unique_entity_pair_string
from system.entities.entity_types import EntityTypes
from typing import List, Dict
from constants import MAX_COLLISION_PASSES
from system.game_clock import game_clock

class CollisionTypes(Enum):
    STATIC = 1
    DYNAMIC = 2
    PASSTHROUGH = 3
    KILL = 4
    NONE = 5

def check_collision(
        e1_location: float, e1_size: float, 
        e2_location: float, e2_size: float
    ) -> bool:
    """AABB overlap test in 3D. """

    # Self box min/max on each axis
    ax1, ay1, az1 = e1_location.x, e1_location.y, e1_location.z
    ax2, ay2, az2 = ax1 + e1_size.x, ay1 + e1_size.y, az1 + e1_size.z

    # Other box min/max
    bx1, by1, bz1 = e2_location.x, e2_location.y, e2_location.z
    bx2, by2, bz2 = bx1 + e2_size.x, by1 + e2_size.y, bz1 + e2_size.z

    

    # Ensure correct ordering in case size components are negative
    ax1, ax2 = (ax1, ax2) if ax1 <= ax2 else (ax2, ax1)
    ay1, ay2 = (ay1, ay2) if ay1 <= ay2 else (ay2, ay1)
    az1, az2 = (az1, az2) if az1 <= az2 else (az2, az1)
    bx1, bx2 = (bx1, bx2) if bx1 <= bx2 else (bx2, bx1)
    by1, by2 = (by1, by2) if by1 <= by2 else (by2, by1)
    bz1, bz2 = (bz1, bz2) if bz1 <= bz2 else (bz2, bz1)


    overlap_x = (ax1 < bx2) and (bx1 < ax2)
    overlap_y = (ay1 < by2) and (by1 < ay2)
    overlap_z = (az1 < bz2) and (bz1 < az2)

    return overlap_x and overlap_y and overlap_z

def get_entity_velocities(unique_collision_pairs: Dict[str, List[Entity]]) -> Dict[Entity, float]:
    velocities = {}
    for e1, e2 in unique_collision_pairs.value():
        if e1 not in velocities:
            velocities[e1] = e1.location - e1.prev_location
        if e2 not in velocities:
            velocities[e2] = e2.location - e2.prev_location
    
    return velocities

def update_collision_entities(
        e1: Entity, e2: Entity, 
        velocities: Dict[Entity, float], 
        timestep: float
    ) -> None:
    
    pass

def resolve_collisions(unique_collision_pairs: Dict[str, List[Entity]]) -> None:
    timestep = game_clock.dt / MAX_COLLISION_PASSES
    velocities = get_entity_velocities(unique_collision_pairs)
    for _ in range(MAX_COLLISION_PASSES):
        stable = True

        for e1, e2 in unique_collision_pairs.value():
            if check_collision(e1.location, e1.size, e2.location, e2.size):
                update_collision_entities(e1, e2, velocities, timestep)
                stable = False
        
        if stable:
            break
    

                