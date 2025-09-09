from system.id_generator import id_generator
from utils.coords import Coord
from constants import GRID_RATIO
import math
import numpy as np

class Entity:
    def __init__(self, location, size, img_id, render_offset): # Use pygame rects
        self.id = id_generator.get_id()
        self.location = location
        self.size = size # Determines hitbox
        self.prev_location = location.copy()
        self.img_id = img_id
        self.render_offset = render_offset # Determines where to render
        self.lifespan = 0

        self.movement_subscribers = []
        self.mananger = None

        self.last_drawn_location = self.location.as_view_coord()
        self.prev_drawn_location = self.location.as_view_coord()
    
    @classmethod
    def dummy(cls):
        return Entity(
            Coord.math(0, 0, 0),
            Coord.math(0, 0, 0),
            0,
            Coord.math(0, 0, 0)
        )
    
    def move(self, movement_vec, with_listeners=True):
        # Need to update prev location to use for collisions in the future
        self.prev_location = self.location.copy()
        self.location += movement_vec

        if with_listeners:
            for movement_subscriber in self.movement_subscribers:
                movement_subscriber.receive_movement_event(self)

        return self
    
    def bind_to_manager(self, manager):
        self.mananger = manager

    def kill(self):
        if self.mananger:
            self.mananger.remove_entity(self)
    
    def add_movement_subscriber(self, subscriber):
        self.movement_subscribers.append(subscriber)
        return self
    
    def remove_movement_subscriber(self, subscriber):
        self.movement_subscribers.remove(subscriber)
        return self
    
    def update(self, dt, onscreen=True):
        self.lifespan += dt

        # Update draw location 
        self.prev_drawn_location = self.last_drawn_location
        dx, dy, _ = self.location.location - self.prev_location.location
        x, y = self.location.as_view_coord()
        if bool(dx) ^ bool(dy):
            p1_x, p1_y = self.last_drawn_location
            ray_vector = math.copysign(GRID_RATIO[0], dy + dx), math.copysign(GRID_RATIO[1], -dy + dx)
            self.last_drawn_location = self.find_closest_point_on_discrete_ray((x, y), (p1_x, p1_y), ray_vector, )
        else:
            self.last_drawn_location = self.location.as_view_coord()

        return self

    def save(self):
        pass

    def load(self, data):
        pass

    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        pass

    def draw(self):
        return self.last_drawn_location + self.render_offset.location[:-1]

    # move this methods elswhere (to a utlity or physics sections)
    @staticmethod
    def find_closest_point_on_discrete_ray(point, ray_start, ray_vector):
        x0, y0 = point
        dx, dy = ray_vector
        x1, y1 = ray_start
       
        m = dy / dx

        # Direction vector along the line and projection scalar
        # d = (1, m)
        # t = ((P - A) · d) / (d · d)
        t = ((x0 - x1) + m * (y0 - y1)) / (1.0 + m * m)

        qx = x1 + t
        qy = y1 + m * t

        x, y = (((qx - x1) // dx) * dx) + x1, (((qy - y1) // dy) * dy) + y1
        return np.array([x, y])
