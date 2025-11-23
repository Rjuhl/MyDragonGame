import math
import json
import shutil
import pygame
from pathlib import Path
from system.entities.sprites.player import Player
from world.map import Map
from world.generation.terrain_generator import TerrainGenerator
from utils.coords import Coord
from typing import Dict, Any, Optional
from decorators import singleton
from system.id_generator import id_generator
from system.game_settings import GameSettings
from system.asset_drawer import AssetDrawer
from constants import BANNER_SIZE


class Game:
    PATH = Path(__file__).parent.parent.parent / 'data' / 'games'
    def __init__(
        self, name: str, 
        screen: pygame.Surface,
        seed: Optional[int] = None, 
        water_level: Optional[int] = None, 
        forest_size: Optional[int] = None, 
        temperature: Optional[int] = None,
        defer_load: bool = False,
        drawer: Optional[AssetDrawer] = None,
    ):
        self.name = name
        self.screen = screen
        self.drawer = drawer
        self.game_settings = GameSettings.load(self.name)

        self.terrain_generator = None
        self.player = None
        self.map = None

        if not defer_load:
            self.terrain_generator = TerrainGenerator(
                seed, water_level, forest_size, temperature
            )

            self.player = Player(self._find_load_spot())
            self.map = Map(self.name, self.screen, self.player, self.terrain_generator)
            self._create_banner()
    
    def _create_banner(self):
        if self.drawer:
            banner_surface = pygame.Surface((384, 32), pygame.SRCALPHA)
            self.drawer.display = banner_surface
            corners = [
                self.player.location.as_world_coord(),
                self.player.location.copy().update_as_view_coord(BANNER_SIZE[0], 0).as_world_coord(),
                self.player.location.copy().update_as_view_coord(0, BANNER_SIZE[1]).as_world_coord(),
                self.player.location.copy().update_as_view_coord(*BANNER_SIZE).as_world_coord(),
            ]
            min_x = math.floor(min(x for x, _, _ in corners)) - 1
            max_x = math.ceil(max(x for x, _, _ in corners)) + 1
            min_y = math.floor(min(y for _, y, _ in corners)) - 1
            max_y = math.ceil(max(y for _, y, _ in corners)) + 1
            
            cam_offset = self.player.location.location[:-1]
            for tile in self.map.get_tiles_to_render(min_x, max_x, min_y, max_y):
                self.drawer.draw_tile(tile, cam_offset, None)
            
            self.map.update()
            for entity in self.map.get_entities_to_render():
                self.drawer.draw_sprite(entity, cam_offset)
   
            pygame.image.save(banner_surface, str((self.PATH / self.name / 'banner.png')))

    def _check_spot(self, location: Coord) -> bool:
        adj = [
            Coord.world(-1, 1), Coord.world(-1, 0), Coord.world(-1, 1),
            Coord.world(0, 1), Coord.world(0, 0), Coord.world(0, 1),
            Coord.world(1, 1), Coord.world(1, 0), Coord.world(1, 1),
        ]

        for c in adj:
            loc = c + location
            tile, _ = self.terrain_generator.generate_tile(loc.x, loc.y, False)
            if tile.has_obsticle or tile.is_water: return False
        
        return True
    
    def _find_load_spot(self):
        location = Coord.world(0, 0)
        while True:
            if self._check_spot(location): return location
            location += Coord.world(1, 1)

    def _save_player(self):
        path = self.PATH / self.name / 'player'
        path.write_text(json.dumps(self.player.jsonify(), ensure_ascii=False, indent=2), encoding='utf-8')

    @classmethod
    def _load_player(cls, name: str) -> Player:
        path = cls.PATH / name / 'player'
        data = json.loads(path.read_text(encoding="utf-8"))
        return Player.load(data)

    @staticmethod
    def load(name: str, screen: pygame.Surface):
        terrain_generator = TerrainGenerator.load(name)
        player = Game._load_player(name)
        map = Map(name, screen, player, terrain_generator)
        game = Game(name, screen, defer_load=True)
        game.map = map
        game.player = player
        game.terrain_generator = terrain_generator
        return game



    def save(self):
        self.terrain_generator.save(self.name)
        self.map.save()
        self.game_settings.save()
        self._save_player()



@singleton
class GameManager:
    PATH = Path(__file__).parent.parent.parent / 'data' / 'games'
    def __init__(self) -> None:
        self.screen: pygame.Surface = None
        self.game: Game = None
        self.drawer = AssetDrawer(pygame.Surface((1, 1), pygame.SRCALPHA))
    
    def save_game(self):
        if self.game: self.game.save()

    def bind_screen(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def set_game(
        self, name: str,
        seed: Optional[int] = None, 
        water_level: Optional[int] = None, 
        forest_size: Optional[int] = None, 
        temperature: Optional[int] = None,
    ):
        self.save_game()
        id_generator.save()
        id_generator.load_game(name)

        if (self.PATH / name).is_dir():
            self.game = Game.load(name, self.screen)
        else:
            self.game = Game(
                name, self.screen,
                seed=seed,
                water_level=water_level,
                forest_size=forest_size,
                temperature=temperature,
                drawer=self.drawer
            )


    @classmethod
    def delete_game(cls, game_name: str):
        path = cls.PATH / game_name
        if path.is_dir(): shutil.rmtree(path)
