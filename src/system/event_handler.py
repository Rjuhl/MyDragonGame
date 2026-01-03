import pygame
from pygame.locals import K_c, K_h, K_z

from decorators import singleton
from utils.close_app import close_app
from system.global_vars import game_globals


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

        if self.input_handler.was_key_pressed(K_c):
            game_globals.chunk_borders_on = not game_globals.chunk_borders_on
        
        if self.input_handler.was_key_pressed(K_h):
            game_globals.show_hitboxes_on = not game_globals.show_hitboxes_on
        
        if self.input_handler.was_key_pressed(K_z):
            game_globals.render_debug = not game_globals.render_debug
