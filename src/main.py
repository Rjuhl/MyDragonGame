import pygame
import constants
from pathlib import Path
from utils.coords import Coord
from world.map import Map
from system.renderer import Renderer
from system.event_handler import EventHandler
from system.game_clock import game_clock
from pygame.locals import *
from system.screen import Screen
from system.entities.sprites.player import Player
from system.global_vars import set_base_globals

def runGame(logger):
    # Load and set icon image 
    current_dir = Path(__file__).parent
    icon_path = current_dir.parent / 'assets' / 'dragon_game_logo_scaled.png'
    icon_surface = pygame.image.load(icon_path)
    pygame.init() 
    pygame.display.set_icon(icon_surface)

    set_base_globals()
    font = pygame.font.Font(None, 24) 
    pygame.display.set_caption(constants.GAME_NAME)
    display = pygame.Surface(constants.DISPLAY_SIZE)
    screen = pygame.display.set_mode(constants.SCREEN_INIT_SIZE, pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1)
    screen_entity = Screen.load()
    
    player = Player(Coord.world(0, 0))

    map = Map(screen_entity)
    renderer = Renderer(display)
    event_handler = EventHandler()

    map.bind_player(player)

    while True:
        game_clock.tick() 
        display.fill((0,0,0))

        map.update()
        items_rendered = renderer.draw(map, screen_entity)
        event_handler.event_tick()

        fps = game_clock.fps           
        fps_text = font.render(f"FPS: {fps:.1f}", True, (0, 0, 255))
        tiles_text = font.render(f"Tiles Rendered: {items_rendered}", True, (0, 0, 255))
        screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
        screen.blit(fps_text, (10, 10))
        screen.blit(tiles_text, (10, 26))
        pygame.display.flip()
