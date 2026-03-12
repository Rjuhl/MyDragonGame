import math
import random
from system.entities.character import Character
from utils.coords import Coord
from typing import List, Optional, Callable
from system.entities.projectiles.projectile import Projectile
from enum import IntEnum
from dataclasses import dataclass
from decorators import register_entity, generate_shadow


class FireParticleHeat(IntEnum):
    RedHot = 0
    OrangeHot = 1
    WhiteHot = 2


@dataclass
class FireParticleArgs:
    location: Coord = Coord(0)
    direction: Coord = Coord(0)
    speed: float = 6
    lifespan: int = 1000
    heat: Callable[[int], FireParticleHeat] = lambda x: max(2 - x // 1000, 0)
    damage: Callable[[FireParticleHeat], float] = lambda x: (int(x) + 1) / 50
    id: Optional[int] = None
class FireParticle(Projectile):
    def __init__(self, args: FireParticleArgs):
        size = Coord.math(0.25, 0.25, 0.25)
        super().__init__(args.location, size, args.direction, args.speed, args.lifespan, 13, id=args.id)

        self.frame = args.heat(0)
        self.heat = args.heat
        self.damage = args.damage

    def update(self, dt, onscreen=True):
        super().update(dt, onscreen=onscreen)
        self.frame = self.heat(self.lifespan)
    
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)
        
        # Player is immune to fire and this is currently only spawned by the player
        from system.entities.npc import NPC
        from system.entities.sprites.player import Player
        if isinstance(other_entity, NPC):
            other_entity.take_damage(self.deal_damage)
        
        if not isinstance(other_entity, Player):
            self.kill()

    def deal_damage(self, e: Character) -> float:
        return self.damage(self.heat(self.lifespan))
    

    @classmethod
    def spawn_random_cone_embers(
        cls,
        max_x_angle: float,
        max_y_angle: float,
        parameters: FireParticleArgs,
        manager,
        count: int = 10,
    ) -> None:
        main_dir = parameters.direction
        max_cone_rad = math.radians(max_x_angle)

        for _ in range(count):
            ax = random.uniform(-max_x_angle, max_x_angle)
            ay = random.uniform(-max_y_angle, max_y_angle)

            # Rotate around Z (horizontal / left-right spread)
            cos_a, sin_a = math.cos(math.radians(ax)), math.sin(math.radians(ax))
            dx = main_dir.x * cos_a - main_dir.y * sin_a
            dy = main_dir.x * sin_a + main_dir.y * cos_a
            dz = main_dir.z

            # Tilt vertically in the plane containing the new XY direction and Z
            horiz = math.sqrt(dx**2 + dy**2)
            cos_b, sin_b = math.cos(math.radians(ay)), math.sin(math.radians(ay))
            new_horiz = horiz * cos_b - dz * sin_b
            new_dz    = horiz * sin_b + dz * cos_b
            if horiz > 0:
                dx *= new_horiz / horiz
                dy *= new_horiz / horiz
            dz = new_dz

            particle_dir = Coord.world(dx, dy, dz)

            # get_angle_2D (unsigned, radians) = XY-plane deviation from main_dir.
            # 0° (center) → WhiteHot (2);  max_x_angle (edge) → RedHot (0).
            angle_rad = main_dir.get_angle_2D(particle_dir, deg=False, signed=False)
            angle_fraction = min(angle_rad / max_cone_rad, 1.0) if max_cone_rad > 0 else 0.0
            initial_heat = round((1.0 - angle_fraction) * (len(FireParticleHeat) - 1))

            def make_heat(h):
                def heat_fn(lifespan):
                    return max(h - lifespan // 1000, 0)
                return heat_fn

            args = FireParticleArgs(
                location=parameters.location.copy(),
                direction=particle_dir,
                speed=parameters.speed,
                lifespan=parameters.lifespan,
                heat=make_heat(initial_heat),
                damage=parameters.damage,
            )
            manager.queue_entity_addition(cls(args))