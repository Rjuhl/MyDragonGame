import pygame
from gui.container import Container
from pathlib import Path
from typing import Optional, List
from system.page_context import PageContext
from gui.types import ClickEvent
from constants import SCREEN_INIT_SIZE
from system.input_handler import input_handler

# Might need to import all pages here to make sure they are regestered

class Page:
    def __init__(self, pageContext: Optional[PageContext]):
        if  pageContext:
            self.containers = []
            self.surface = pageContext.display
            self.w, self.h = self.surface.get_size()
            self.context = pageContext



    def add_container(self, x: int, y: int, container: Container) -> None:
        container.x, container.y = x, y
        container.parent_w, container.parent_h = self.w, self.h
        self.containers.append(container)


    def render(self) -> None:
        click_event = ClickEvent.Left if input_handler.was_mouse_button_pressed(1) else None
        mouse_pos = self.get_mouse_pos()
        for container in self.containers: 
            container.reposition_children()
            container.handle_mouse_actions(mouse_pos, click_event, self.context.state)
            container.render(self.surface)

    def update(self) -> None:
        self.render()
        self.context["next_page"] = self.__class__.__name__

    def get_mouse_pos(self):
        return input_handler.get_mouse_pos()
