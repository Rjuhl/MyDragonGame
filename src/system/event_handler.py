import pygame, sys
from pygame.locals import *
from system.global_vars import game_globals
from utils.close_app import close_app
from decorators import singleton


@singleton
class EventHandler:
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
