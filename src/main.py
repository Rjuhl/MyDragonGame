import pygame
import constants
from utils.paths import assets_root
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
from utils.app_helpers import close_app
from system.settings import global_settings
from world.game import GameManager
from system.id_generator import id_generator


def runGame():
    # Load and set icon image
    icon_path = assets_root() / 'dragon_game_logo_scaled.png'
    pygame.init()
    icon_surface = pygame.image.load(icon_path)
    pygame.display.set_icon(icon_surface)

    set_base_globals()
    font = pygame.font.Font(None, 24) 
    pygame.display.set_caption(constants.GAME_NAME)
    display = pygame.Surface(constants.DISPLAY_SIZE)

    fullscreen = global_settings.get("fullscreen_on")
    screen = pygame.display.set_mode(constants.SCREEN_INIT_SIZE, pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1)
    if fullscreen: pygame.display.toggle_fullscreen()
    screen_entity = Screen.load()

    cursor_hotspot = (0, 0)
    cursor_path = assets_root() / 'mouse_claw.png'
    cursor_image = pygame.image.load(cursor_path).convert_alpha()
    pygame.mouse.set_cursor(cursor_hotspot, cursor_image)

    game_manager = GameManager()
    game_manager.bind_screen(screen_entity)

    renderer = Renderer(display)
    event_handler = EventHandler()

    page_context = PageContext(
        display, event_handler, renderer, screen_entity
    )

    page_manager = PageManager(page_context)

    sound_mixer = SoundMixer()
    sound_mixer.play_music(Sound.MAIN_TRACK)

    is_input_handler_bound = False

    while True:
        if not is_input_handler_bound:
            is_input_handler_bound = True
            input_handler.bind_displays(screen, display)

        if fullscreen != global_settings.get("fullscreen_on"):
            fullscreen = not fullscreen
            pygame.display.toggle_fullscreen()
            pygame.mouse.set_cursor(cursor_hotspot, cursor_image)
            pygame.event.pump()
            pygame.event.clear()

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

        if constants.DEBUG_ON:
            screen.blit(fps_text, (10, 10))
            screen.blit(tiles_text, (10, 26))

        pygame.display.flip()
            
