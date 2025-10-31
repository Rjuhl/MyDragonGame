import math
import numpy as np
from typing import Callable, Self, Set, Tuple, List, Any
from utils.coords import Coord
from system.render_obj import RenderObj
from system.entities.entity import Entity
from world.generation.types import Terrain
from system.entities.damage_text_entity import DamageText
from decorators import register_entity


@register_entity
class Character(Entity):
    def __init__(
            self, entity_args: List[Any],
            health: int, mana: int, energy: int,
            stam: int, vit: int, wis: int, spd: int, att: int, deff: int,
            water_speed_mod: float, air_speed_mod: float, base_speed: float
        ):
        super().__init__(*entity_args)

        # ------ Base stats -------- #

        self.max_health = health
        self.max_mana = mana
        self.max_energy = energy

        self.stam = stam
        self.vit = vit
        self.wis = wis
        self.spd = spd
        self.att = att
        self.deff = deff

        self.base_speed = base_speed
        self.water_speed = water_speed_mod
        self.air_speed = air_speed_mod

        # ------ Modified stats -------- # 

        self.eff_max_health = self.max_health
        self.eff_max_mana = self.max_mana
        self.eff_max_energy = self.max_energy

        self.eff_stam = self.stam
        self.eff_vit = self.vit
        self.eff_wis = self.wis
        self.eff_spd = self.spd
        self.eff_att = self.att
        self.eff_deff = self.deff

        self.eff_base_speed = self.base_speed

        # ------ Other properties -------- # 

        self.current_health = self.eff_max_health
        self.current_mana = self.eff_max_mana
        self.current_energy = self.eff_max_energy
        self.effects: Set[Tuple[float, Callable[[Self], None]]] = set() # Need a way to save this 

        self.damage_mask = None
        self.damage_animation_frame = []
        self.animation_offset = 0

    def add_effect(self, effect: Callable[[Self], None], duration: float) -> None:
        self.effects.add((effect, duration))

    def take_damage(self, damage_func: Callable[[Self], float]) -> None:
        damage = damage_func(self)
        self.current_health -= damage
        self._apply_damage_animation()
        self._spawn_damage_number(damage // 1)

    def spend_energy(self, energy: float) -> bool:
        if energy <= self.current_energy: 
            self.current_energy -= energy
            return True
        return False

    def spend_mana(self, mana: float) -> bool:
        if mana <= self.current_mana:
            self.current_mana -= mana
            return True
        return False

    def get_damage(self, base: int) -> float:
        return base * self._stat_to_multiplier(self.eff_att)

    def get_speed(self, terrain: Terrain) -> float:
        return self.eff_base_speed * self._stat_to_multiplier(self.eff_spd) * self._terrain_spd_multiplier(terrain)

    # Maybe make regen field based purley off of stats and not need any inputs
    def regen_health(self, health: float, apply_stats: bool = True) -> None:
        health_gain_mod = self._stat_to_multiplier(self.vit) if apply_stats else 1
        self.current_health = min(self.eff_max_health, self.current_health + (health * health_gain_mod))

    def regen_mana(self, mana: float, apply_stats: bool) -> None:
        mana_gain_mod = self._stat_to_multiplier(self.wis) if apply_stats else 1
        self.current_mana = min(self.eff_max_mana, self.current_health + (mana * mana_gain_mod))

    def regen_energy(self, energy: float, apply_stats: bool) -> None:
        energy_gain_mod = self._stat_to_multiplier(self.stam) if apply_stats else 1
        self.current_energy = min(self.eff_max_energy, self.current_health + (energy * energy_gain_mod))

    # Helper to deal damage with respect to stats 
    def apply_damage(self, damage: float) -> None:
        damage = self._apply_def_reduction(damage)
        self.current_health -= damage
        self._apply_damage_animation()
        self._spawn_damage_number(damage // 1)

    
    def handle_character_updates(self, dt: float) -> bool:
        if self.current_health <= 0: 
            self.kill()
            return False

        self._apply_damage_animation()
        self.regen_mana(dt, True)
        self.regen_health(dt, True)
        self.regen_energy(dt, True)
        return True


    def _spawn_damage_number(self, num: int) -> None:
        text_entity = DamageText(num, 120, self._base_trajectory, with_rng=True)
        self.manager.add_entity(text_entity)

    def _start_damage_animation(self, amplitude=8, duration=30) -> None:
        self.damage_animation_frame = 0
        self.mask = (238, 18, 66, 100)

        period = duration // 2
        steps = np.linspace(0, period, duration)
        self.damage_animation_frames = amplitude * np.sin(2 * np.pi * steps / period)
        
    def _apply_damage_animation(self) -> None:
        self.animation_offset = 0
        if self.damage_animation_frame < len(self.damage_animation_frames):
            self.animation_offset = self.damage_animation_frames[self.damage_animation_frame]
            self.damage_animation_frame += 1
    

    def _terrain_spd_multiplier(self, terrain: Terrain):
        if terrain == Terrain.Air: return self.air_speed
        if terrain == Terrain.Water: return self.water_speed
        return 1
    
    def _apply_def_reduction(self, damage: float) -> float:
        return damage / self._stat_to_multiplier(self.eff_deff) 

    def apply_effects(self, dt: float):
        for item in self.effects:
            effect, lifetime = item
            effect(self)
            lifetime -= dt
            self.effects.remove(item)
            if lifetime > 0: self.effects.add((effect, lifetime))
    
    def jsonify(self):
        json = super().jsonify()
        json["max_health"] = self.max_health
        json["max_mana"] = self.max_mana
        json["max_energy"] = self.max_energy 
        json["stam"] = self.stam 
        json["vit"] = self.vit 
        json["wis"] = self.wis 
        json["spd"] = self.spd 
        json["att"] = self.att 
        json["deff"] = self.deff 
        json["base_speed"] = self.base_speed 
        json["water_speed"] = self.water_speed 
        json["air_speed"] = self.air_speed
        json["current_health"] = self.current_health
        json["current_mana"] = self.current_mana
        json["current_energy"] = self.current_energy
        # Save effects somehow
        return json
        

    def load_character_attrs(self, data) -> None:
        self.max_health = data["max_health"]
        self.max_mana = data["max_mana"]
        self.max_energy = data["max_energy"]
        self.stam = data["stam"]
        self.vit = data["vit"]
        self.wis = data["wis"] 
        self.spd = data["spd"]
        self.att = data["att"] 
        self.deff = data["deff"] 
        self.base_speed = data["base_speed"] 
        self.water_speed = data["water_speed"] 
        self.air_speed = data["air_speed"]
        self.current_health = data["current_health"]
        self.current_mana = data["current_mana"]
        self.current_energy = data["current_energy"]


    # Subject to change but this a decent base to start with
    @staticmethod
    def _stat_to_multiplier(stat: int) -> float:
        return 0.01 * stat + (math.sqrt(stat) / 10) + 1   
    
    @staticmethod
    def _base_trajectory(age: float) -> Coord:
        return 12 * (-(((age - 60) / 60) ** 2) + 1)
    

    # ----------------------------------------------------- #
    # ----------        Method overrides        ----------- #
    # ----------------------------------------------------- #

    def get_render_objs(self) -> List[RenderObj]:
        location = self.draw_location()
        location.x += self.animation_offset

        return [RenderObj(
            self.img_id,
            location,
            (self.shade_level(), self.location.x, self.location.y, self.location.z),
            location=self.location, size=self.size, mask=self.damage_mask
        )]

    

    
    
            


