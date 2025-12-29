import pygame
import random
from utils.coords import Coord
from system.entities.npc import NPC
from system.entities.spawner import Spawner
from system.entities.character import CharaterArgs
from system.entities.types.entity_types import FoxStates
from system.entities.types.facing_types import Facing
from utils.types.shade_levels import ShadeLevel
from decorators import register_entity, generate_shadow
from typing import Optional, Self
from system.entities.frame_incrementer import FrameIncrementer
from system.sound import SoundMixer, Sound, SoundInstance


@register_entity
@generate_shadow(0.65, 0.5, fade=0.5)
class Fox(NPC):
    def __init__(self, location: Coord, home: Optional[int], id: Optional[int] = None):
        entity_args = [
            location, Coord.math(0.25, 0.25, 0.25), 6, Coord.math(0, -5, 0)
        ]

        character_args = CharaterArgs(
            10 + random.randint(0, 8), 0, + random.randint(0, 8), 
            10 + random.randint(0, 3), 15, 15, 10 + random.randint(0, 3), 10, 5,
            0.5, 0, 1.25
        )

        super().__init__(home, entity_args, character_args)

        self.rotated = False
        self.frame = 0
        self.current_step = 0
        self.facing = Facing.Idle
        self.state = FoxStates.WANDER
        self.incrementer = FrameIncrementer(0, 167, lambda i: (i + 1) % 4)
        self.idle_time = FrameIncrementer(0, 1000 * 12, lambda i: i + 1)
        


    def _set_frame(self) -> None:
        if self.facing == Facing.Right: self.frame = self.current_step
        elif self.facing == Facing.Left: self.frame = 4 + self.current_step
        elif self.facing == Facing.Down: self.frame = 8 + self.current_step
        elif self.facing == Facing.Up: self.frame = 12 + self.current_step
        else: self.frame = 0

        self.rotated = self.frame >= 8

    def _wander(self, dt: float) -> None:
        if self.state != FoxStates.WANDER: return
        if self.destination is None:
            new_destination = self.location.copy().update_as_world_coord(10 + random.randint(0, 10), 10 + random.randint(0, 10))
            new_destination.x *= -1 * random.randint(0, 1)
            new_destination.y *= -1 * random.randint(0, 1)
            self.set_destination(new_destination)
            self.set_success_criteria(None)
        if self.success_criteria():
            self.destination = None
            self.state = FoxStates.IDLE
            return
        
        self.facing = self.head_to_destination(dt)

    def move(self, movement: Coord, with_listeners: bool = True, is_vector: bool = True) -> Self:
        SoundMixer().add_locational_sound_effect(SoundInstance(
            random.choice([Sound.GRASS_1, Sound.GRASS_2]),
            id=self.id,
            time_restricted=500,
            get_location=lambda: self.location,
        ))
        return super().move(movement, with_listeners=with_listeners, is_vector=is_vector)

    def _idle(self) -> None:
        if self.state != FoxStates.IDLE: return
        self.facing = Facing.Idle
        if self.idle_time.tick():
            self.idle_time.reset()
            self.state = FoxStates.WANDER


    # def _return_home(self) -> None:
    #     if self.state != FoxStates.HOME: return
    #     if self.destination is None:

    def get_render_objs(self):
        render_objs = super().get_render_objs()
        for obj in render_objs: obj.frame = self.frame
        return render_objs
    
    def update(self, dt, onscreen):
        super().update(dt, onscreen)
        self._wander(dt)
        self._idle()
        self._set_frame()
        self.current_step = self.incrementer.tick()

    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)
        self.move(self.prev_location, is_vector=False)
        
    
    def jsonify(self):
        data = super().jsonify()
        data["state"] = self.state.name
        return data
    

    def _load_fox(self, data):
        self.state = FoxStates[data["state"]]

    @classmethod
    def load(cls, data):
        fox = Fox(Coord.load(data["location"]), data["spawner_id"], id=data["id"])
        fox.load_npc(data)
        fox._load_fox(data)
        return fox
    