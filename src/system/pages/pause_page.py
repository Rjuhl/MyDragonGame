from decorators import register_page
from gui.page import Page
from gui.container import Container
from gui.types import ItemAlign, ItemAppend
from gui.buttons.basic_button import BasicButton
from system.page_context import PageContext
from system.pages.main_menu import MainMenu
from gui.utils.callbacks import settings_callback, main_menu_callback, game_loop_callback
from world.game import GameManager

@register_page
class PausePage(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)
        return_button = BasicButton(
            "100%", "30", 
            "Continue", 24,
            game_loop_callback
        )

        settings_button = BasicButton(
            "100%", "30", 
            "Settings", 24,
            settings_callback
        )

        exit_button = BasicButton(
            "100%", "30", 
            "Exit to main menu", 24,
            main_menu_callback
        )


        button_container = Container(
            "40%", "80%",
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Below,
            children=[
                return_button,
                settings_button,
                exit_button
            ],
            gap=20
        )

        base_container = Container(
            "100%", "100%", 
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
            children = [
                button_container
            ]
        )

        self.add_container(0, 0, base_container)


    def update(self) -> None:
        game_manager = GameManager()
        self.context.renderer.draw(game_manager.game.map, game_manager.screen)
        self.render()




