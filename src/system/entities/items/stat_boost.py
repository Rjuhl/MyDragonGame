import random
from gui.text import PixelText
from system.entities.entity import Entity
from system.entities.sprites.player import Player
from system.entities.damage_text_entity import HoppingText
from system.entities.frame_incrementer import FrameIncrementer
from system.sound import SoundMixer, Sound, SoundRequest
from utils.coords import Coord
from utils.types.colors import RGBA
from typing import List, Tuple, Callable, Dict
from system.render_obj import RenderObj
from decorators import generate_shadow
from utils.trajectories import base_trajectory
from enum import Enum

CoinInfo = Tuple[int, RGBA, Callable[[Player], str]]

class CoinType(Enum):
    Fire = "fire"
    Energy = "energy"
    Defense = "defense"
    Gold = "gold"


# TODO: implement when items are needed
class Item:
    pass

@generate_shadow(0.5, 0.5, fade=0.85)
class StatBoost(Entity, Item):
    COIN_PROPS: Dict[CoinType, CoinInfo] = {}

    def __init__(
        self, 
        location: Coord,
        state_type: CoinType,
        size: Coord = Coord.math(0.25, 0.25, 0.25),
        lifespan: int = 1000 * 60 * 2
    ):
        super().__init__(location, size, -1, Coord(0))
        self.frame = 0
        self.type = state_type
        self.max_lifespan = lifespan

        self.img_id = self.COIN_PROPS[self.type][0]
        self.text_color = self.COIN_PROPS[self.type][1]
        self.collision_effect = self.COIN_PROPS[self.type][2]

        self.incrementer = FrameIncrementer(0, 167, lambda i: (i + 1) % 4)

        # prevents collosion checks with particles even though it is not particle itself
        self.is_particle = True
        self.send_death_event = False

    
    def shadow_location(self):
        location = self.location.copy()
        location.z = 0
        return location.as_view_coord()

    def update(self, dt, onscreen=True):
        super().update(dt, onscreen=onscreen)
        if self.lifespan > self.max_lifespan:
            self.kill()

        self.frame = self.incrementer.tick()

    
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)

        # Apply stat boost if collided with player
        if isinstance(other_entity, Player):
            text = self.collision_effect(other_entity)
            self.manager.queue_entity_addition(HoppingText(
                self.location,
                PixelText(text, 16, self.text_color, outline_color=(255, 255, 255, 255), outline=1),
                1000 * 2.5, base_trajectory, with_rng=False
            ))
            SoundMixer().add_sound_effect(SoundRequest(
                Sound.ITEM_PICKUP
            ))
            self.kill()


    def get_render_objs(self) -> List[RenderObj]:
        render_objs = super().get_render_objs()
        for obj in render_objs: obj.frame = self.frame
        return render_objs

    def jsonify(self):
        return None
    

    @classmethod
    def _apply_gold_coin_boost(cls, player: Player) -> str:
        if random.random() < 0.5: 
            player.vit += 1
            player.eff_vit = player.vit
            return cls._on_collect_text(["Vitality"], [1])
        
        player.max_health += 10
        player.eff_max_health = player.max_energy
        return cls._on_collect_text(["Max Health"], [10])
    
    @classmethod
    def _apply_defense_coin_boost(cls, player: Player) -> str:
        def_boost = random.randint(1, 3)
        player.deff += def_boost
        player.eff_deff = player.deff
        return cls._on_collect_text(["Defense"], [def_boost])
    
    @classmethod
    def _apply_energy_coin_boost(cls, player: Player) -> str:
        if random.random() < 0.5: 
            player.stam += 1
            player.eff_stam = player.stam
            return cls._on_collect_text(["Stamina"], [1])
            
        player.max_energy += 10
        player.eff_max_energy = player.max_energy
        return cls._on_collect_text(["Max Energy"], [10])
    
    @classmethod
    def _apply_fire_coin_boost(cls, player: Player) -> str:
        if random.random() < 0.5: 
            player.fire_charge_rate += 0.1
            return cls._on_collect_text(["Fire Charge Rate"], [0.1])
        
        player.max_fire_charge += 5
        return cls._on_collect_text(["Max Fire Charge"], [5])

    @staticmethod
    def _on_collect_text(stats: List[str], amounts: List[int]):
        text = ""
        for (stat, amount) in zip(stats, amounts):
            text += f"+{amount}  {stat}"
        return text


StatBoost.COIN_PROPS = {
    CoinType.Fire: (16, (186, 45, 95, 255), StatBoost._apply_fire_coin_boost),
    CoinType.Energy: (15, (67, 128, 109, 255), StatBoost._apply_energy_coin_boost),
    CoinType.Defense: (14, (49, 57, 73, 255), StatBoost._apply_defense_coin_boost),
    CoinType.Gold: (17, (201, 163, 72, 255), StatBoost._apply_gold_coin_boost),
}