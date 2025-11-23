import json
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

class Game:
    PATH = Path(__file__).parent.parent.parent / 'data' / 'games'
    def __init__(
        self, name: str, 
        screen: pygame.Surface,
        seed: Optional[int] = None, 
        water_level: Optional[int] = None, 
        forest_size: Optional[int] = None, 
        temperature: Optional[int] = None,
        defer_load: bool = False
    ):
        self.name = name
        self.screen = screen
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
        print(path)
        with path.open("r", encoding="utf-8") as f:
            data = json.loads(f)
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
                temperature=temperature
            )


    @classmethod
    def delete_game(cls, game_name: str):
        pass

game_manager = GameManager()
