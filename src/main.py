import pygame
import constants
from pathlib import Path
from utils.coords import Coord
from world.map import Map
from system.renderer import Renderer
from system.event_handler import EventHandler
from system.game_clock import game_clock
from system.input_handler import input_handler
from pygame.locals import *
from system.screen import Screen
from system.entities.sprites.player import Player
from system.page_manager import PageManager
from system.page_context import PageContext
from system.global_vars import set_base_globals
from system.sound import SoundMixer, Sound
from utils.close_app import close_app
from world.game import GameManager
from system.id_generator import id_generator


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

    game_manager = GameManager()
    game_manager.bind_screen(screen_entity)

    renderer = Renderer(display)
    event_handler = EventHandler()

    page_context = PageContext(
        display, event_handler, renderer, screen_entity
    )

    page_manager = PageManager(page_context)
    input_handler.bind_displays(screen, display)

    sound_mixer = SoundMixer()
    sound_mixer.play_music(Sound.MAIN_TRACK)

    while True:
        game_clock.tick()
        event_handler.store_events()
        input_handler.update()
        sound_mixer.update()

        display.fill((0,0,0))
        event_handler.event_tick()

        if not page_manager.show_page(): close_app()
        fps = game_clock.fps           
        fps_text = font.render(f"FPS: {fps:.1f}", True, (0, 0, 255))
        tiles_text = font.render(f"Tiles Rendered: {page_context.state["items_rendered"]}", True, (0, 0, 255))
        screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
        screen.blit(fps_text, (10, 10))
        screen.blit(tiles_text, (10, 26))
        pygame.display.flip()
            
