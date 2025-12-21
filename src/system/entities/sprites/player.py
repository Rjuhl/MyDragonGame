import math
import pygame
import random
from pygame.locals import *
from system.entities.entity import Entity
from system.entities.character import Character, CharaterArgs
from typing import List, Dict
from utils.coords import Coord
from constants import TEMP_MOVEMENT_FACTOR, MOVEMENT_MAP, GRID_RATIO
from system.render_obj import RenderObj
from system.entities.physics.shadows import EllipseData
from utils.types.shade_levels import ShadeLevel
from system.input_handler import input_handler
from system.sound import SoundMixer, SoundInstance, Sound

# Update with character class
class Player(Character):
    def __init__(self, location: Coord, character_args=CharaterArgs()) -> None:
        is_human = True
        self.init_human(location, character_args) if is_human else self.init_dragon(location)

        self.last_drawn_location = self.location.as_view_coord()
        self.prev_drawn_location = self.location.as_view_coord()

    def update(self, dt, onscreen=True):
        super().update(dt, onscreen)
        movement = self.get_movement(dt)
        self.move(movement)
        self._play_sounds(movement)
        return self

    def init_human(self, location: Coord, character_args: CharaterArgs):
        size = Coord.math(.25, .25, 1.25)
        render_offset = Coord.math(0, -9, 0)
        img_id = 1
        entity_args = [location, size, img_id, render_offset]
        super().__init__(entity_args, character_args)

    def init_dragon(self, location: Coord) -> None:
        pass

    def smooth_movement(self):
        # Update draw location 
        self.prev_drawn_location = self.last_drawn_location
        dx, dy, dz = self.location.location - self.prev_location.location
        x, y = self.location.as_view_coord()
        if bool(dx) ^ bool(dy) and dz == 0:
            p1_x, p1_y = self.last_drawn_location
            ray_vector = math.copysign(GRID_RATIO[0], dy + dx), math.copysign(GRID_RATIO[1], -dy + dx)
            self.last_drawn_location = self.find_closest_point_on_discrete_ray((x, y), (p1_x, p1_y), ray_vector)
        else:
            self.last_drawn_location = self.location.as_view_coord()

    def shade_level(self):
        if self.location.z <= 1: return ShadeLevel.SPRITE
        elif self.location.z <= 3: return ShadeLevel.CANOPY
        return ShadeLevel.CANOPY_END
    
    def draw_location(self):
        return self.last_drawn_location + self.render_offset.location[:-1]
    
    def get_shadow(self) -> EllipseData:
        x, y = self.last_drawn_location
        return EllipseData(
            Coord.view(x, y, self.location.z),
            0.5, 0.5, 0
        )
    
    # TODO: Better collision handling (ie special handling for static opbjects and so on)
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        self.move(self_velocity * -timestep)

    # def jsonify(self):
    #     json = super().jsonify()
    #     json["last_drawn_location"] = self.last_drawn_location.tolist()
    #     json["prev_drawn_location"] = self.prev_drawn_location.tolist()
    #     return json
    
    def _play_sounds(self, movement: Coord):
        if not movement.is_null() and self.location.z == 0:
            SoundMixer().add_sound_effect(SoundInstance(
                random.choice([Sound.GRASS_1, Sound.GRASS_2]),
                id=self.id,
                time_restricted=500
            ))


    @staticmethod
    def load(data):
        player = Player(Coord.load(data["location"]), CharaterArgs())
        player.load_character_attrs(data)
        return player
    
    @staticmethod
    def get_movement(dt: float):
        movement = input_handler.get_player_movement()
        movement *= TEMP_MOVEMENT_FACTOR * (dt / 1000)
        return movement
    
