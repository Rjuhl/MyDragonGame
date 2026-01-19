import random
from utils.coords import Coord
from system.entities.npc import NPC
from system.entities.projectiles.magic_missle import MagicMissle
from system.entities.character import CharaterArgs
from system.entities.types.entity_types import NPCState
from system.entities.types.facing_types import Facing
from utils.cooldown import Cooldown
from system.entities.frame_incrementer import FrameIncrementer
from system.render_obj import RenderObj
from system.sound import SoundMixer, Sound, SoundRequest
from constants import WIZARD_AGGRESSION_RANGE
from decorators import register_entity, generate_shadow
from typing import Optional, List, Self

@register_entity
@generate_shadow(0.6, 0.6, fade=0.5)
class Wizard(NPC):
    def __init__(self, location: Coord, home: Optional[int], id: Optional[int] = None):
        entity_args = [
            location, Coord.math(0.25, 0.25, 1), 10, Coord.math(-2, -12, 0)
        ]
        
        character_args = CharaterArgs(
            10 + random.randint(0, 8), 0, + random.randint(0, 8), 
            10 + random.randint(0, 3), 15, 15, 10 + random.randint(0, 3), 10, 5,
            0.5, 0, 1.25
        )

        super().__init__(home, entity_args, character_args, id=id)


        self.rotated = False
        self.frame = 0
        self.current_step = 0
        self.facing = Facing.Idle
        self.state = NPCState.IDLE
        self.incrementer = FrameIncrementer(0, 167, lambda i: (i + 1) % 4)
        self.idle_time = FrameIncrementer(0, 1000 * 12, lambda i: i + 1)

        # Attack State Vars
        self.missle_count = 0
        self.launch_missles = False
        self.attack_frame = FrameIncrementer(0, 167, lambda i: (i + 1) % 4)
        self.magic_missle_cooldown = Cooldown(1000 * 3)
        self.missle_fire_rate = Cooldown(333)

    def _idle(self, dt: float) -> None:
        if self.state != NPCState.IDLE: return

        # Search for wandering path while idle so when wander is state is active there is a path calculated (Removing this helped with lag todo)
        # if self.destination is None:
        #     self._pick_and_set_destination()
        #     self.head_to_destination(0)
        # elif self.path is None:
        #     self.head_to_destination(0)

        self.facing = Facing.Idle
        if self.idle_time.tick():
            self.idle_time.reset()
            self.state = NPCState.WANDER
            

    def _wander(self, dt: float) -> None:
        if self.state != NPCState.WANDER: return
        
        self.current_step = self.incrementer.tick()

        if self.destination is None: 
            self._pick_and_set_destination()

        self.facing = self.head_to_destination(dt)

        if self.success_criteria():
            self.destination = None
            self.path = None
            self.state = NPCState.IDLE
            self.incrementer.reset()
            self.current_step = 0

    # TODO: Address attack lag spikes -- and general lag (something is off with these current changes)
    # I think the lag is coming from _attach changing the state machine which leaves some jobs never cleared
    # from the AstarManager leading to a build up 
    def _attack(self, dt: float) -> None:
        player_loc = self.manager.player.location
        self_loc = self.location

        # If we're not in range, immediately fall back to wandering
        if player_loc.manhattan_2D(self_loc) > WIZARD_AGGRESSION_RANGE:
            if self.state == NPCState.FIGHT:
                self._reset_attack()
            
            self.state = NPCState.WANDER if self.destination is not None else NPCState.IDLE
            return

        # If we are mid-attack (already firing missiles), keep going even though cooldown isn't ready.
        # If we are NOT mid-attack, only start an attack when the cooldown is ready.
        if self.missle_count == 0 and not self.magic_missle_cooldown.ready(reset=False):
            self.state = NPCState.WANDER
            self._reset_attack()
            return

        self.state = NPCState.FIGHT

        # Phase 1: windup animation until it completes one cycle
        if self.missle_count == 0:
            prev_step = self.current_step
            self.current_step = self.attack_frame.tick()

            # Detect "animation looped" (e.g., 3 -> 0 when modulo-4 animation wraps)
            if prev_step == 3 and self.current_step == 0:
                self.missle_count = 6
                self.missle_fire_rate.reset()
                
            return

        # Phase 2: firing missiles at a fixed rate
        if not self.missle_fire_rate.ready():
            return

        direction = player_loc - self_loc
        self.facing = self.get_4_facing_based_on_direction(direction)

        self.manager.queue_entity_addition(
            MagicMissle(self._get_attack_spawn_location(), direction)
        )

        self.missle_count -= 1
        if self.missle_count == 0:
            self._reset_attack()
            self.magic_missle_cooldown.reset()


    def _reset_attack(self):
        self.missle_count = 0
        self.attack_frame.reset()
        self.current_step = 0

    def _get_attack_spawn_location(self):
        return self.location + Coord.math(0, 0, 1)

    def _set_frame(self) -> None:
        if self.state == NPCState.FIGHT:
            if self.facing == Facing.Right: self.frame = 12 + self.current_step
            elif self.facing == Facing.Down: self.frame = 20 + self.current_step
            elif self.facing == Facing.Up: self.frame = 28 + self.current_step
            else: self.frame = self.frame = 4 + self.current_step
            return
        
        if self.facing == Facing.Left: self.frame = self.current_step
        elif self.facing == Facing.Right: self.frame = 8 + self.current_step
        elif self.facing == Facing.Down: self.frame = 16 + self.current_step
        elif self.facing == Facing.Up: self.frame = 24 + self.current_step
        else: self.frame = 0

    def _pick_and_set_destination(self) -> None:
        if (home := self.manager.entities.get(self.spawner)):
            axis, sign = random.randint(0, 1), 1 - (2 * random.randint(0, 1))
            dx, dy = axis * sign * 5, (1 - axis) * sign * 5
            self.set_destination(home.location + Coord.math(dx, dy, 0))
            self.set_success_criteria(None)

    def update(self, dt: float, onscreen: bool) -> None:
        super().update(dt, onscreen)
        self._wander(dt)
        self._idle(dt)
        self._attack(dt)
        self._set_frame()
        self.magic_missle_cooldown.tick()
        self.missle_fire_rate.tick()

    def get_render_objs(self) -> List[RenderObj]:
        render_objs = super().get_render_objs()
        for obj in render_objs: obj.frame = self.frame
        return render_objs

    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)
        self.move(self.prev_location, is_vector=False)

    def move(self, movement: Coord, with_listeners: bool = True, is_vector: bool = True) -> Self:
        SoundMixer().add_locational_sound_effect(SoundRequest(
            random.choice([Sound.GRASS_1, Sound.GRASS_2]),
            id=self.id,
            time_restricted=500,
            get_location=lambda: self.location,
        ))
        return super().move(movement, with_listeners=with_listeners, is_vector=is_vector)
    

    def _load_wizard(self, data):
        self.state = NPCState[data["state"]]

    def jsonify(self):
        data =  super().jsonify()
        data["state"] = self.state.name
        return data


    def close_to_player(self):
        return self.manager.player.location.euclidean(self.location) < 3

    @classmethod
    def load(cls, data):
        wizard = Wizard(Coord.load(data["location"]), data["spawner_id"], id=data["id"])
        wizard.load_npc(data)
        wizard._load_wizard(data)
        return wizard