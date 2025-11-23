import pygame
from gui.page import Page
from gui.container import Container
from gui.text import PixelText
from gui.buttons.button import Button
from gui.types import ItemAlign, ItemAppend, ClickEvent
from gui.utils.callbacks import main_menu_callback
from system.page_context import PageContext
from decorators import register_page
from pathlib import Path
from typing import List

GAMES_PER_PAGE = 5

@register_page(default=True)
class ChooseGamePage(Page):
    GAME_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'games'
    def __init__(self, pageContext):
        super().__init__(pageContext)

        self.current_page = 1
        self.context.state["paginate"] = self.current_page
        self.context.state["max_pages"] = self._get_total_pages()

        self.game_container = Container(
            "80%", "60%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            gap=10
        )

        paginate_buttons_container = Container(
           "80%", "20",
           ItemAlign.Last, ItemAlign.Center, ItemAppend.Right,
           children=[
               self._create_pagination_text(),
               Button("40", "20", "Prev", 16, self._prev_button_callback),
               Button("40", "20", "Next", 16, self._next_button_callback),
           ]
        )

        base_container = Container(
            "100%", "100%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children=[
                PixelText("Choose Game", 48, (255, 255, 255, 255), bold=True, outline=1),
                self.game_container,
                paginate_buttons_container,
                Button("80%", "20", "Main Menu", 18, main_menu_callback)
            ], gap=10
        )
        background = pygame.Surface((640, 360))
        background.fill((217, 202, 221, 255))
        base_container.background = background

        self.add_container(0, 0, base_container)

    
    def _get_total_pages(self) -> int:
        return sum(1 for child in self.GAME_DIR.iterdir() if child.is_dir())
    
    def _get_game_names_on_page(self) -> List[str]:
        games = [child.name for child in self.GAME_DIR.iterdir() if child.is_dir()]
        return games[self.current_page * GAMES_PER_PAGE: min(len(games), (self.current_page + 1) * GAMES_PER_PAGE)]

    
    def _create_pagination_text(self):
        return PixelText(
            f"page {self.current_page} of {self._get_total_pages()}    ", 
            16, (255, 255, 255, 255), varient=1
        )
    
    
    
    @staticmethod
    def _prev_button_callback(context: PageContext) -> None:
        context["paginate"] = max(0, context["paginate"] - 1)

    @staticmethod
    def _next_button_callback(context: PageContext) -> None:
        context["paginate"] = min(context["max_pages"], context["paginate"] + 1)


        
