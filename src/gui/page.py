import pygame
from gui.container import Container
from pathlib import Path
from typing import Optional, List
from system.page_context import PageContext
from gui.types import ClickEvent
from constants import SCREEN_INIT_SIZE

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
        click_event = None
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_event = ClickEvent.Left
        mouse_pos = self.get_mouse_pos()
        for container in self.containers: 
            container.reposition_children()
            container.handle_mouse_actions(mouse_pos, click_event, self.context.state)
            container.render(self.surface)

    def update(self) -> None:
        self.render()
        self.context["next_page"] = self.__class__.__name__

    def get_mouse_pos(self):
        x, y = pygame.mouse.get_pos()
        s_x, s_y = self.context.display.get_size()
        d_x, d_y = SCREEN_INIT_SIZE # This can get updated so this will need changed later to be more resiliant

        return round(x * (s_x / d_x)), round(y * (s_y / d_y))
