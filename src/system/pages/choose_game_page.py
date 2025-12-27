import pygame
from gui.page import Page
from gui.container import Container
from gui.text import PixelText
from gui.buttons.button import Button
from gui.types import ItemAlign, ItemAppend, ClickEvent
from gui.utils.callbacks import main_menu_callback, game_loop_callback
from system.page_context import PageContext
from system.game_clock import game_clock
from decorators import register_page
from pathlib import Path
from typing import List
from world.game import GameManager

GAMES_PER_PAGE = 3
DELETE_BUTTON_CYCLES = 192
DELETE_BAR_SPEED = 0.1

@register_page
class ChooseGamePage(Page):
    GAME_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'games'
    def __init__(self, pageContext):
        super().__init__(pageContext)

        self.current_page = 1
        self.total_games = self._get_total_games()
        self.max_pages = self._get_total_pages()
        self.context.state["paginate"] = self.current_page
        self.context.state["max_pages"] = self.max_pages

        self.delete_buttons = {}

        self.card_container = Container(
            "384", "32",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children = self._build_all_cards()
        )

        game_container = Container(
            "80%", "60%", 
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            gap=10,
            children=[
                self.card_container
            ]
        )
        

        self.paginate_buttons_container = Container(
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
                game_container,
                self.paginate_buttons_container,
                Button("80%", "20", "Main Menu", 18, main_menu_callback)
            ], gap=10
        )
        background = pygame.Surface((640, 360))
        background.fill((217, 202, 221, 255))
        base_container.background = background

        self.add_container(0, 0, base_container)

    def _get_total_games(self) -> int:
        return sum(1 for child in self.GAME_DIR.iterdir() if child.is_dir())


    def _get_total_pages(self) -> int:
        return 1 + max(self._get_total_games() - 1, 1) // GAMES_PER_PAGE
    
    def _get_game_names_on_page(self) -> List[str]:
        games = [child.name for child in self.GAME_DIR.iterdir() if child.is_dir()]
        return games[(self.current_page - 1) * GAMES_PER_PAGE: min(len(games), (self.current_page) * GAMES_PER_PAGE)]

    
    def _create_pagination_text(self):
        return PixelText(
            f"page {self.current_page} of {self._get_total_pages()}    ", 
            16, (255, 255, 255, 255), varient=1
        )
    
    def _build_game_card(self, game_name: str):
        delete_button = Button(
            "50%", "100%", "DELETE", 
            16, self._get_delete_button_callback(game_name),
            include_mouse_held=True, sound_instance=None
        )
        self.context.state[f"delete_{game_name}"] = 0
        self.delete_buttons[game_name] = delete_button
        return Container(
            "100%", "62", # y subject to change,
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children=[
                Container(
                    "384", "32",
                    ItemAlign.First, ItemAlign.Center, ItemAppend.Below,
                    children=[
                        PixelText(game_name, 20, (255, 255, 255, 255), outline=1)
                    ],
                    backgrounds=[self.GAME_DIR / game_name / 'banner.png'],
                    padding=(10, -5)
                ),
                Container(
                    "100%", "16", 
                    ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
                    children=[
                        Button("50%", "100%", "PLAY", 16, self._get_play_callback(game_name)),
                        delete_button,
                    ]
                )
            ],
        )
    
    def _build_all_cards(self):
        return [self._build_game_card(game) for game in self._get_game_names_on_page()]

    def update(self):
        if self.context.state["paginate"] != self.current_page or self.total_games != self._get_total_games():
            self.total_games = self._get_total_games()
            self.max_pages = self._get_total_pages()
            self.context.state["max_pages"] = self.max_pages

            self.current_page = self.context.state["paginate"]
            if self.current_page > self.max_pages:
                self.current_page -= 1
                self.context.state["paginate"] -= 1

            for key in self.delete_buttons: self.context.state[key] = 0
            self.delete_buttons = {}
            self.card_container.children = self._build_all_cards()
            
            self.paginate_buttons_container.children[0] = self._create_pagination_text()
        

        super().render()

        deleted_buttons = []
        for game_name, button in self.delete_buttons.items():
            # Handle delete
            if self.context.state[f"delete_{game_name}"] == DELETE_BUTTON_CYCLES:
                GameManager().delete_game(game_name)
                deleted_buttons.append(game_name)
                del self.context.state[f"delete_{game_name}"]
                continue
        
            self.context.state[f"delete_{game_name}"] = max(
                0, 
                self.context.state[f"delete_{game_name}"] - 1 * game_clock.dt * DELETE_BAR_SPEED
            )

            if self.context.state[f"delete_{game_name}"] > 0:
                _, h = button.get_size()
                delete_surface = pygame.Surface((int(round(self.context.state[f"delete_{game_name}"])), h), pygame.SRCALPHA)
                delete_surface.fill((238, 18, 66, 128))
                self.context.display.blit(delete_surface, (button.x, button.y))

        for button_name in deleted_buttons: del self.delete_buttons[button_name]

    
    @staticmethod
    def _prev_button_callback(context: PageContext) -> None:
        context["paginate"] = max(1, context["paginate"] - 1)

    @staticmethod
    def _next_button_callback(context: PageContext) -> None:
        context["paginate"] = min(context["max_pages"], context["paginate"] + 1)

    @staticmethod
    def _get_play_callback(game_name: str):

        def callback(context: PageContext) -> None:
            game = game_name
            GameManager().set_game(game)
            game_loop_callback(context)
        
        return callback
    
    @staticmethod
    def _get_delete_button_callback(game_name: str):

        def callback(context: PageContext) -> None:
            game = game_name
            context[f"delete_{game}"] = min(
                DELETE_BUTTON_CYCLES, 
                context[f"delete_{game}"] + 2 * game_clock.dt * DELETE_BAR_SPEED
            )
        
        return callback


        
