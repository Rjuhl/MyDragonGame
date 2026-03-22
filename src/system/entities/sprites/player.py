import math
import pygame
import random
from pygame.locals import *
from system.entities.character import Character, CharaterArgs
from typing import List, Callable, Self
from utils.coords import Coord
from constants import TEMP_MOVEMENT_FACTOR, MOVEMENT_MAP, GRID_RATIO, Y_MOUSE_FIRE_RANGE
from system.render_obj import RenderObj
from system.entities.physics.shadows import EllipseData
from utils.types.shade_levels import ShadeLevel
from system.input_handler import input_handler
from system.sound import SoundMixer, SoundRequest, Sound, DRAGON_WING_FLAPS, DRAGON_HURT_SOUNDS
from system.event_handler import GameEvent
from system.entities.types.facing_types import Facing
from system.entities.frame_incrementer import FrameIncrementer
from system.entities.projectiles.fire_particle import FireParticle, FireParticleArgs
from world.generation.types import Terrain
from system.entities.projectiles.projectile import Projectile
from utils.cooldown import Cooldown

# Update with character class
class Player(Character):
    def __init__(self, location: Coord, character_args=CharaterArgs()) -> None:
        size = Coord.math(0.65, 0.65, 0.5)
        render_offset = Coord.math(0, -3, 0)
        img_id = 12
        entity_args = [location, size, img_id, render_offset]
        character_args.air_speed_mod = 1.6
        character_args.base_speed = TEMP_MOVEMENT_FACTOR * 0.75
        character_args.deff = 15
        super().__init__(entity_args, character_args)


        self.last_drawn_location = self.location.as_view_coord()
        self.prev_drawn_location = self.location.as_view_coord()

        # Animation
        self.facing = Facing.Right
        self.incrementer = FrameIncrementer(0, 120, lambda i: (i + 1) % 10)
        self.current_step = 0
        self.current_wing_flap = 0
        self.is_moving = False
        self.frame = 0 if self.location.z == 0 else 160

        self.can_spawn_fire_particles = Cooldown(33)
        self.mouse_pos_on_fire_start = None
        self._fire_state = 'idle'  # 'idle' | 'starting' | 'firing' | 'ending'
        self.sound_ready = False

        self.max_fire_charge = 100
        self.fire_charge = self.max_fire_charge
        self.fire_charge_rate = 1
        self.fire_exhuastion_rate = -2 
        self.has_energy = self.current_energy > 0

    def regen_energy(self):
        if not self.has_energy and self.location.z > 0: return
        super().regen_energy()

    def _handle_player_updates(self, dt: float) -> bool:
        if self.apply_effects_interval.ready(reset=False):
            # Spend energy if flying
            self.has_energy = self.spend_energy(2) if self.location.z > 0 else self.spend_energy(0)
        
            # Spend/gain fire energy 
            self.fire_charge += self.fire_exhuastion_rate if self._is_breathing_fire() else self.fire_charge_rate
            self.fire_charge = min(max(0, self.fire_charge), self.max_fire_charge)

        return self.handle_character_updates(dt)

    def update(self, dt, onscreen=True):
        super().update(dt, onscreen)
        if not self._handle_player_updates(dt): self.kill()
        movement = self.get_movement(dt)
        self._set_facing(movement)
        self._set_frame()
        self.move(movement)
        self._play_sounds(movement)
        self._spawn_fire()
        self.can_spawn_fire_particles.tick()
        return self

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

        # Circle returned
        if (
            not self.is_moving and
            self.location.z > 0
        ): return EllipseData(
            Coord.view(x, y, self.location.z),
            0.65, 0.65, 0
        )

        # Ellipse rot: 0 (screen coords) returned
        if (
            (
                self.facing == Facing.Left or
                self.facing == Facing.Right
            ) and 
            (
                self.is_moving or
                self.location.z == 0
            )
        ): return EllipseData(
            Coord.view(x, y, self.location.z),
            0.65, 1, -math.pi / 4
        )

        # Ellipse rot: 45 (screen coords) returned
        if (
            (
                self.facing == Facing.UpperRight or
                self.facing == Facing.LowerLeft
            ) and 
            (
                self.is_moving or
                self.location.z == 0
            )
        ): return EllipseData(
            Coord.view(x, y, self.location.z),
            0.65, 1, 0
        )

        # Ellipse rot: 90 (screen coords) returned
        if (
            (
                self.facing == Facing.Up or
                self.facing == Facing.Down
            ) and 
            (
                self.is_moving or
                self.location.z == 0
            )
        ): return EllipseData(
            Coord.view(x, y, self.location.z),
            0.65, 1, math.pi / 4
        )

        # Ellipse rot: 135 (screen coords) returned
        return EllipseData(
            Coord.view(x, y, self.location.z),
            0.65, 1.2, math.pi / 2
        )
    
    # TODO: Better collision handling (ie special handling for static objects and so on)
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        if not isinstance(other_entity, Projectile):
            self.move(self_velocity * -timestep)

    def jsonify(self):
        json = super().jsonify()
        # json["last_drawn_location"] = self.last_drawn_location.tolist()
        # json["prev_drawn_location"] = self.prev_drawn_location.tolist()
        json["fire_charge"] = self.fire_charge
        json["max_fire_charge"] = self.max_fire_charge
        json["fire_charge_rate"] = self.fire_charge_rate
        return json

    def _is_breathing_fire(self) -> bool:
        return input_handler.is_mouse_button_held(1) and self.fire_charge > 0
    
    def _play_sounds(self, movement: Coord):
        if not movement.is_null() and self.location.z == 0:
            SoundMixer().add_locational_sound_effect(SoundRequest(
                random.choice([Sound.GRASS_1, Sound.GRASS_2]),
                id=self.id,
                time_restricted=500,
                get_location=lambda: self.get_location()
            ))

        if self.location.z > 0 and self.current_step == 0:
            SoundMixer().add_locational_sound_effect(SoundRequest(
                DRAGON_WING_FLAPS[self.current_wing_flap % len(DRAGON_WING_FLAPS)],
                id=self.id,
                get_location=lambda: self.get_location()
            ))
            self.current_wing_flap += 1
        
        if self._is_breathing_fire() and self._fire_state == 'idle':
            # First click in game will be from "choosing game" so ignore it
            if not self.sound_ready:
                self.sound_ready = True
                return
            
            self._fire_state = 'starting'
            SoundMixer().add_locational_sound_effect(SoundRequest(
                Sound.DRAGON_FIRE_START,
                get_location=lambda: self.get_location(),
                keep_playing=lambda: self._is_breathing_fire(),
                finished_callback=self._on_fire_start_done,
            ))

    def _on_fire_start_done(self):
        if not self._is_breathing_fire():
            self._fire_state = 'idle'
            return
        self._fire_state = 'firing'
        SoundMixer().add_locational_sound_effect(SoundRequest(
            Sound.DRAGON_FIRE,
            repeats=-1,
            get_location=lambda: self.get_location(),
            keep_playing=lambda: self._is_breathing_fire(),
            finished_callback=self._on_fire_done,
        ))

    def _on_fire_done(self):
        self._fire_state = 'ending'
        SoundMixer().add_locational_sound_effect(SoundRequest(
            Sound.DRAGON_FIRE_END,
            get_location=lambda: self.get_location(),
            finished_callback=self._on_fire_end_done,
        ))

    def _on_fire_end_done(self):
        self._fire_state = 'idle'


    def _set_facing(self, movement: Coord) -> None:
        dx, dy, _ = movement.location
        if dx < 0 and dy > 0: self.facing = Facing.Up
        elif dx > 0 and dy < 0: self.facing = Facing.Down
        elif dx < 0 and dy < 0: self.facing = Facing.Left
        elif dx > 0 and dy > 0: self.facing = Facing.Right
        elif dx == 0 and dy > 0: self.facing = Facing.UpperRight
        elif dx == 0 and dy < 0: self.facing = Facing.LowerLeft
        elif dx > 0 and dy == 0: self.facing = Facing.LowerRight
        elif dx < 0 and dy == 0: self.facing = Facing.UpperLeft

        self.is_moving = dx != 0 or dy != 0
        # Don't change facing if no movement was made
        

    def _set_frame(self):
        is_flying = self.location.z > 0
        if is_flying or self.is_moving: self.current_step = self.incrementer.tick()
        
        frame = self.current_step  + (is_flying * 80) + ((is_flying and not self.is_moving) * 80)
        if self.facing == Facing.Left: frame += 10
        if self.facing == Facing.Up: frame += 20
        if self.facing == Facing.Down: frame += 30
        if self.facing == Facing.UpperRight: frame += 40
        if self.facing == Facing.UpperLeft: frame += 50
        if self.facing == Facing.LowerRight: frame += 60
        if self.facing == Facing.LowerLeft: frame += 70

        self.frame = frame

    def take_damage(self, damage_func: Callable[[Self], float]) -> None:
        super().take_damage(damage_func)
        SoundMixer().add_locational_sound_effect(
            SoundRequest(
                random.choice(DRAGON_HURT_SOUNDS),
                get_location=lambda: self.get_location(),
                time_restricted=333,
            )
        )

    def kill(self):
        super().kill()
        pygame.event.post(
            pygame.event.Event(
                GameEvent.PLAYER_DIED,
            )
        )

    def get_render_objs(self) -> List[RenderObj]:
        render_objs = super().get_render_objs()
        for obj in render_objs: obj.frame = self.frame
        return render_objs
    

    def _get_fire_location_and_direction(self):
        fire_start = fire_direction = None
        z_offset = self.mouse_pos_on_fire_start - input_handler.get_mouse_pos()[-1]
        z_offset = max(min(z_offset, Y_MOUSE_FIRE_RANGE), -Y_MOUSE_FIRE_RANGE) / Y_MOUSE_FIRE_RANGE
        match self.facing:
            case Facing.Right:
                fire_start = self.location + Coord.math(0.55, 0.55, 0.5)
                fire_direction = Coord.math(1, 1, z_offset)
            case Facing.Left:
                fire_start = self.location + Coord.math(-0.5, -0.5, 0.5)
                fire_direction = Coord.math(-1, -1, z_offset)
            case Facing.Down:
                fire_start = self.location + Coord.math(1.25, -1.25, 0.5)
                fire_direction = Coord.math(1, -1, z_offset)
            case Facing.Up:
                fire_start = self.location + Coord.math(-0.75, 0.75, 0.5)
                fire_direction = Coord.math(-1, 1, z_offset)
            case Facing.UpperRight:
                fire_start = self.location + Coord.math(0, 0.85, 0.5)
                fire_direction = Coord.math(0, 1, z_offset)
            case Facing.UpperLeft:
                fire_start = self.location + Coord.math(-0.85, 0, 0.5)
                fire_direction = Coord.math(-1, 0, z_offset)
            case Facing.LowerRight:
                fire_start = self.location + Coord.math(0.85, 0, 0)
                fire_direction = Coord.math(1, 0, z_offset)
            case Facing.LowerLeft:
                fire_start = self.location + Coord.math(0, -0.85, 0)
                fire_direction = Coord.math(0, -1, z_offset)
        return fire_start, fire_direction
        

    def _spawn_fire(self):
        if not self._is_breathing_fire(): 
            self.mouse_pos_on_fire_start = None
            return
        if self.can_spawn_fire_particles.ready():
                if self.mouse_pos_on_fire_start is None:
                    self.mouse_pos_on_fire_start = input_handler.get_mouse_pos()[-1]

                location, direction = self._get_fire_location_and_direction()
                parameters = FireParticleArgs(location, direction)
                FireParticle.spawn_random_cone_embers(
                    10, 10, parameters, self.manager, count=10
                )
        
    def get_movement(self, dt: float) -> Coord:
        movement = input_handler.get_player_movement()
        movement *= self.get_speed(Terrain.Ground if self.location.z == 0 else Terrain.Air) * (dt / 1000)

        if not self.has_energy:
            movement.z = -0.05

        return movement
    

    def get_location(self):
        return self.location

    @staticmethod
    def load(data):
        player = Player(Coord.load(data["location"]), CharaterArgs())
        player.load_character_attrs(data)
        player.fire_charge = data["fire_charge"]
        player.max_fire_charge = data["max_fire_charge"]
        player.fire_charge_rate = data["fire_charge_rate"]
        return player

    
