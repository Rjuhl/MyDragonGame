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
            p2_x, p2_y = p1_x + math.copysign(GRID_RATIO[0], dy + dx), p1_y + math.copysign(GRID_RATIO[1], -dy + dx)

            # TODO: Fix this
            #This can cause visaul glitches because the entity could be moving to fast
            if self.norm_1_distance(x, y, p2_x, p2_y) < self.norm_1_distance(x, y, p1_x, p1_y):
                self.last_drawn_location = np.array([p2_x, p2_y])
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
    def norm_1_distance(p1_x, p1_y, p2_x, p2_y):
        return abs(p2_x - p1_x) + abs(p2_y - p1_y)