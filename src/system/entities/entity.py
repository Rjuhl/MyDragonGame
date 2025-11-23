from system.id_generator import id_generator
from utils.coords import Coord
from constants import GRID_RATIO, WORLD_HEIGHT, TILE_SIZE
import math
import numpy as np
from system.entities.base_entity import BaseEntity
from system.render_obj import RenderObj
from utils.types.shade_levels import ShadeLevel
from typing import List, Optional, Self, Tuple
from system.entities.physics.shadows import Receiver
from decorators import register_entity

@register_entity 
class Entity(BaseEntity):
    def __init__(self, location: Coord, size: Coord, img_id: int, render_offset: Coord, id: Optional[int] = None, solid: Optional[bool] = True): 
        super().__init__(location, size)
        self.id = id if id is not None else id_generator.get_id()
        self.prev_location = location.copy()
        self.img_id = img_id
        self.render_offset = render_offset # Determines where to render
        self.lifespan = 0

        self.movement_subscribers = []
        self.manager = None

        self.rotated = False
        self.solid = True

    
    @classmethod
    def dummy(cls):
        return Entity(
            Coord.math(0, 0, 0),
            Coord.math(0, 0, 0),
            0,
            Coord.math(0, 0, 0)
        )
    
    def serve_reciever(self) -> Optional[Receiver]:
        return None

    def serve_shadow(self): 
        return None

    def move(self, movement_vec: Coord, with_listeners: bool = True) -> Self:
        # Need to update prev location to use for collisions in the future
        self.prev_location = self.location.copy()
        self.location += movement_vec

        # Clamp z axis movement 
        self.location.z = np.clip(self.location.z, 0, WORLD_HEIGHT / TILE_SIZE)

        if with_listeners:
            for movement_subscriber in self.movement_subscribers:
                movement_subscriber.receive_movement_event(self)

        return self
    
    def bind_to_manager(self, manager):
        self.manager = manager

    def kill(self):
        if self.manager:
            self.manager.queue_entity_removal(self)
    
    def add_movement_subscriber(self, subscriber):
        self.movement_subscribers.append(subscriber)
        return self
    
    def remove_movement_subscriber(self, subscriber):
        self.movement_subscribers.remove(subscriber)
        return self
    
    def update(self, dt, onscreen=True):
        self.lifespan += dt
        return self

    def jsonify(self):
        return {
            "id": self.id,
            "img_id": self.img_id,
            "size": self.size.jsonify(),
            "location": self.location.jsonify(),
            "prev_location": self.prev_location.jsonify(),
            "render_offset": self.render_offset.jsonify(),
            "lifespan": self.lifespan
        }

    @staticmethod
    def load(data):
        entity = Entity(
            Coord.load(data["location"]),
            Coord.load(data["size"]),
            data["img_id"],
            Coord.load(data["render_offset"]),
            id=data["id"]
        )

        entity.prev_location = Coord.load(data["prev_location"])
        entity.lifespan = data["lifespan"]

        return entity

    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        pass

    def shade_level(self):
        return ShadeLevel.SPRITE

    def draw_location(self):
        return self.location.as_view_coord() + self.render_offset.location[:-1]

    def get_render_objs(self) -> List[RenderObj]:
        return [RenderObj(
            self.img_id,
            self.draw_location(),
            (self.shade_level(), self.location.x, self.location.y, self.location.z),
            location=self.location, size=self.size
        )]


    # move this methods elswhere (to a utlity or physics sections)
    @staticmethod
    def find_closest_point_on_discrete_ray(point, ray_start, ray_vector):
        x0, y0 = point
        dx, dy = ray_vector
        x1, y1 = ray_start
       
        m = dy / dx

        # Direction vector along the line and projection scalar
        t = ((x0 - x1) + m * (y0 - y1)) / (1.0 + m * m)

        qx = x1 + t
        qy = y1 + m * t

        x, y = (((qx - x1) // dx) * dx) + x1, (((qy - y1) // dy) * dy) + y1
        return np.array([x, y])


class EntitySubscriber:
    def receive_movement_event(entity: Entity):
        pass