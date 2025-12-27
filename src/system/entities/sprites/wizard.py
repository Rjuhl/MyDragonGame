import random
from utils.coords import Coord
from system.entities.npc import NPC
from system.entities.character import CharaterArgs
from system.entities.types.entity_types import NPCState
from system.entities.types.facing_types import Facing
from system.entities.frame_incrementer import FrameIncrementer
from system.render_obj import RenderObj
from decorators import register_entity, generate_shadow
from typing import Optional, List


@register_entity
@generate_shadow(0.75, 0.75, fade=0.5)
class Wizard(NPC):
    def __init__(self, location: Coord, home: Optional[int]):
        entity_args = [
            location, Coord.math(0.25, 0.25, 1), 10, Coord.math(-2, -12, 0)
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
        self.state = NPCState.IDLE
        self.incrementer = FrameIncrementer(0, 167, lambda i: (i + 1) % 4)
        self.idle_time = FrameIncrementer(0, 1000 * 12, lambda i: i + 1)


    def _idle(self, dt: float) -> None:
        if self.state != NPCState.IDLE: return

        # Search for wandering path while idle so when wander is state is active there is a path calculated
        if self.destination is None:
            self._pick_and_set_destination()
            self.head_to_destination(0)
        elif self.path is None:
            self.head_to_destination(0)

        self.facing = Facing.Idle
        if self.idle_time.tick():
            self.idle_time.reset()
            self.state = NPCState.WANDER
            

    def _wander(self, dt: float) -> None:
        if self.state != NPCState.WANDER: return

        if self.destination is None: 
            self._pick_and_set_destination()
        
        if self.success_criteria():
            self.destination = None
            self.path = None
            self.state = NPCState.IDLE

        self.facing = self.head_to_destination(dt)


    def _attack(self, dt: float) -> None:
        pass

    def _set_frame(self) -> None:
        if self.facing == Facing.Left: self.frame = self.current_step
        elif self.facing == Facing.Right: self.frame = 8 + self.current_step
        elif self.facing == Facing.Down: self.frame = 16 + self.current_step
        elif self.facing == Facing.Up: self.frame = 24 + self.current_step
        else: self.frame = 0

    def _pick_and_set_destination(self) -> None:
        if (home := self.manager.entities.get(self.spawner)):
            dx, dy = 5 * (-1 * random.randint(0, 1)), 5 * (-1 * random.randint(0, 1))
            self.set_destination(home.location + Coord.world(dx, dy))
            self.set_success_criteria(None)

    def update(self, dt: float, onscreen: bool) -> None:
        super().update(dt, onscreen)
        self._wander(dt)
        self._idle(dt)
        self._set_frame()
        self.current_step = self.incrementer.tick()

    def get_render_objs(self) -> List[RenderObj]:
        render_objs = super().get_render_objs()
        for obj in render_objs: obj.frame = self.frame
        return render_objs

    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)
        self.move(self.prev_location, is_vector=False)