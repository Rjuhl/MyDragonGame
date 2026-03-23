import pygame
from pygame.locals import K_z

from decorators import singleton
from utils.app_helpers import close_app
from system.global_vars import game_globals

from constants import DEBUG_ON

from enum import IntEnum

class GameEvent(IntEnum):
    PLAYER_DIED = pygame.event.custom_type()
    MOUSE_ONE_CLICKED = pygame.event.custom_type()


@singleton
class EventHandler:
    """
        Legacy event hub.

        Responsibilities (legacy split):
        - store_events(): pulls the pygame event queue once per frame and caches it
        - events(): returns the cached list so other systems can iterate it safely
        - event_tick(): applies global debug hotkeys and handles quit requests

        Notes
        - InputHandler is the authoritative source for high-level input state
        (quit_requested, was_key_pressed, etc.).
        - Many systems still iterate EventHandler().events() directly; this class
        exists to keep that pattern working.
    """

    def __init__(self):
        from system.input_handler import input_handler
        self.stored_events = []
        self.input_handler = input_handler

    def store_events(self):
        self.stored_events = pygame.event.get()
    
    def events(self):
        return self.stored_events

    def event_tick(self):
        if self.input_handler.quit_requested: close_app()

        if self._is_game_page():
            if self.input_handler.was_action_pressed("toggle_borders"):
                game_globals.chunk_borders_on = not game_globals.chunk_borders_on
                game_globals.optimize_render = not game_globals.chunk_borders_on
            
            if self.input_handler.was_action_pressed("toggle_hitboxes"):
                game_globals.show_hitboxes_on = not game_globals.show_hitboxes_on

            if self.input_handler.was_action_pressed("toggle_fps"):
                game_globals.fps_on = not game_globals.fps_on
            
            if self.input_handler.was_key_pressed(K_z) and DEBUG_ON:
                game_globals.render_debug = not game_globals.render_debug

    @staticmethod
    def _is_game_page():
        from system.pages.game_page import GamePage
        from system.page_manager import PageManager
        return isinstance(PageManager().current_page, GamePage)
