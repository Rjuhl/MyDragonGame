from enum import Enum
from typing import List, Dict, Tuple

from utils.coords import Coord
from system.entities.entity import Entity

from system.game_clock import game_clock
from constants import MAX_COLLISION_PASSES


class CollisionTypes(Enum):
    STATIC = 1
    DYNAMIC = 2
    PASSTHROUGH = 3
    KILL = 4
    NONE = 5

def check_collision(
        e1_location: Coord, e1_size: Coord, 
        e2_location: Coord, e2_size: Coord
    ) -> bool:
    """
        Axis-Aligned Bounding Box (AABB) overlap test in 3D.

        Parameters
        ----------
        loc1, loc2:
            Expected to have `.x`, `.y`, `.z` (your Coord type).
            In this module, these are top-left/front-ish corners (see center_hit_box()).
        size1, size2:
            Expected to have `.x`, `.y`, `.z` representing box dimensions.

        Returns
        -------
        True if the boxes overlap with *strict* inequality (touching faces is not collision).
    """

    # Box 1 bounds
    ax1, ay1, az1 = e1_location.x, e1_location.y, e1_location.z
    ax2, ay2, az2 = ax1 + e1_size.x, ay1 + e1_size.y, az1 + e1_size.z

    # Box 1 bounds
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

def center_hit_box(location: Coord, size: Coord) -> Tuple[Coord, Coord]:
    """ Convert an entity center position into a top-left corner """
    top_left = location.copy()
    top_left.x = top_left.x - size.x / 2
    top_left.y = top_left.y - size.y / 2
    return top_left, size

def get_entity_velocities(unique_collision_pairs: Dict[str, List[Entity]]) -> Dict[Entity, float]:
    """
    Cache each entity's velocity once per resolve call.
    Velocity is computed from current - previous location.
    """
    velocities = {}
    for e1, e2 in unique_collision_pairs.values():
        if e1 not in velocities:
            velocities[e1] = e1.location - e1.prev_location
        if e2 not in velocities:
            velocities[e2] = e2.location - e2.prev_location
    
    return velocities


def resolve_collisions(unique_collision_pairs: Dict[str, List[Entity]]) -> None:
    """
        Resolve collisions between entity pairs.

        Algorithm:
        - Split the frame dt into MAX_COLLISION_PASSES substeps (timestep).
        - For each pass, test all pairs.
        - If any collisions occur, call handle_collision() on both entities.
        - If a pass finds no collisions, stop early (stable).
    """
    timestep = game_clock.dt / MAX_COLLISION_PASSES
    velocities = get_entity_velocities(unique_collision_pairs)
    for _ in range(MAX_COLLISION_PASSES):
        stable = True

        for e1, e2 in unique_collision_pairs.values():
            if check_collision(
                *center_hit_box(e1.location, e1.size), 
                *center_hit_box(e2.location, e2.size)
            ): 
                e1.handle_collision(velocities[e1], e2, velocities[e2], timestep)
                e2.handle_collision(velocities[e2], e1, velocities[e1], timestep)
                stable = False
        
        if stable:
            break
    
                