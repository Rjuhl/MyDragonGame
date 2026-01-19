import pygame
from gui.page import Page
from gui.container import Container
from gui.types import ItemAlign, ItemAppend
from gui.text import PixelText
from gui.buttons.button import Button
from gui.utils.callbacks import game_loop_callback
from system.page_context import PageContext
from decorators import register_page
from world.game import GameManager


@register_page
class Respawn(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)

        text_container = Container(
            "100%", "70%", 
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Below,
            children=[
                PixelText(
                    "Your mortal body has perished", 
                    22, (255, 255, 255, 255), bold=True, outline=1, outline_color=(186, 45, 95, 255)
                ),
                PixelText(
                    "but your dragon flame lives on to rise again", 
                    22, (255, 255, 255, 255), bold=True, outline=1, outline_color=(186, 45, 95, 255)
                ),
            ]
        )

        respawn_button = Button(
            "70%", "10%", "Respawn", 28, self._respawn_player
        )

        base_container = Container(
            "100%", "100%", 
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Below,
            children = [
                text_container,
                respawn_button
            ]
        )

        background = pygame.Surface((640, 360), pygame.SRCALPHA)
        background.fill((218, 18, 66, 120))
        base_container.background = background
        self.add_container(0, 0, base_container)

    def update(self) -> None:
        game_manager = GameManager()
        self.context.renderer.draw(game_manager.game.map, game_manager.screen)
        self.render()

    @staticmethod
    def _respawn_player(context: PageContext):
        GameManager().game.bind_new_player()
        game_loop_callback(context)