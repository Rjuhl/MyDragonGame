from decorators import register_page
from gui.page import Page
from gui.container import Container
from gui.types import ItemAlign, ItemAppend
from gui.buttons.basic_button import BasicButton
from system.page_context import PageContext
from system.pages.main_menu import MainMenu


@register_page
class PausePage(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)
        return_button = BasicButton(
            "100%", "30", 
            "Continue", 24,
            self.return_callback
        )

        settings_button = BasicButton(
            "100%", "30", 
            "Settings", 24,
            lambda x: x
        )

        exit_button = BasicButton(
            "100%", "30", 
            "Exit to main menu", 24,
            self.exit_callback
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
        self.context.renderer.draw(self.context.map, self.context.screen)
        self.render()

    @staticmethod
    def return_callback(context: PageContext) -> None:
        from system.pages.game_page import GamePage  # Local import to avoid circular import
        context["next_page"] = GamePage.__name__

    @staticmethod
    def exit_callback(context: PageContext) -> None:
        context["next_page"] = MainMenu.__name__



