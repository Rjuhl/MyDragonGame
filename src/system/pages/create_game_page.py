import pygame
import random
from gui.page import Page
from gui.container import Container
from gui.types import ItemAlign, ItemAppend, ClickEvent
from gui.text import PixelText
from gui.atoms.text_input import TextInput
from gui.atoms.radio_input import RadioInput
from gui.buttons.button import Button
from gui.utils.callbacks import main_menu_callback, game_loop_callback
from system.page_context import PageContext
from world.game import GameManager
from decorators import register_page
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path


@register_page
class CreateGamePage(Page):
    GAME_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'games'
    def __init__(self, pageContext):
        super().__init__(pageContext)

        self.world_name_input = TextInput(
            "world_name", "40%", "20", 16, 
            variant=1,
            clear_on_click=True,
            default_text="ENTER WORLD NAME HERE"
        )

        world_name_container = Container(
            "80%", "20",
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
            children=[
                PixelText("World:", 18, (255, 255, 255, 255), varient=1),
                self.world_name_input
            ],
            gap=20
        )

        self._reroll_seed(self.context.state)
        self.seed_input = TextInput(
            "seed_value", "200", "20", 16, 
            variant=1, 
            verifier= lambda c: c.isdigit(), 
            char_limit=8, 
            outline_color=(79, 80, 112, 255), 
            default_text=self.context.state["seed_value"]
        )
        

        seed_name_container = Container(
            "80%", "20",
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
            children=[
                PixelText("Seed:", 18, (255, 255, 255, 255), varient=1),
                self.seed_input,
                Button("100", "20", "Reroll", 18, self._reroll_seed),
            ],
            gap=20, padding=(0, 10)
        )

        radio_container = Container(
            "100%", "100%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children=[
                self._create_radio_input_row("Climate:", ["cold", "normal", "hot"], field="climate"),
                self._create_radio_input_row("Forest Size:", ["small", "medium", "large"], field="forest_size"),
                self._create_radio_input_row("Water Level:", ["low", "normal", "high"], field="water_level"),
                self._create_radio_input_row("Game Difficulty:", ["low", "normal", "high"], field="difficulty"),
            ], gap=10, padding=(0, 20)
        )

        self.create_game_button = Button("40%", "100%", "Create Game", 18, self._create_game_callback)

        navigation_buttons_container = Container(
            "100%", "20", 
            ItemAlign.Center, ItemAlign.First, ItemAppend.Right,
            children=[
                Button("40%", "100%", "Main Menu", 18, main_menu_callback),
                self.create_game_button
            ], gap=10, padding=(0, 20)
        )

        self.empty_error_text = PixelText("", 14, (0, 0, 0, 0), varient=1)
        self.error_text = PixelText("World name already in use or is invalid", 16, (238, 18, 66, 255), varient=1)

        self.buttons_container = Container(
            "100%", "90%",
            ItemAlign.Center, ItemAlign.Last, ItemAppend.Below,
            children=[
                self.empty_error_text,
                navigation_buttons_container
            ], gap=0
        )

        base_container = Container(
            "100%", "100%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children=[
                PixelText("New Game", 48, (255, 255, 255, 255), bold=True, outline=1),
                world_name_container,
                seed_name_container,
                radio_container,
                navigation_buttons_container
            ]
        )
        background = pygame.Surface((640, 360))
        background.fill((217, 202, 221, 255))
        base_container.background = background

        self.add_container(0, 0, base_container)
        self.add_container(0, 0, self.buttons_container)

    def _create_radio_input_row(
        self, text: str, options: List[str],
        field: Optional[str] = None, default_selection: int = 1
    ):
        field = field if field else text
        return Container(
            "80%", "20",
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
            children=[
                Container(
                    "20%", "20",
                    ItemAlign.First, ItemAlign.Center, ItemAppend.Right,
                    children=[
                        PixelText(text, 14, (255, 255, 255, 255), varient=1),
                    ]
                ),
                Container(
                    "80%", "20",
                    ItemAlign.Last, ItemAlign.Center, ItemAppend.Right,
                    children=[
                        RadioInput(
                            field, "300", "20", 
                            14, options,  default_selection,
                        ),
                    ]
                )
            ],
        )
    

    def _world_name_is_valid(self) -> bool:
        return not (self.GAME_DIR / self.context.state["world_name"]).is_dir()
    
    def update(self):
        if self.context.state.get("reroll_called", False):
            self.seed_input.text = self.context.state["seed_value"]
            self.context.state["reroll_called"] = False

        super().render()

        self.buttons_container.children[0] = self.empty_error_text
        self.world_name_input.outline_color = (79, 80, 112, 255)
        if not self._world_name_is_valid():
            self.world_name_input.outline_color = (79, 80, 112, 255)
            self.buttons_container.children[0] = self.error_text

        if self._world_name_is_valid() and "create_game_clicked" in self.context.state and self.context.state["create_game_clicked"]:
            seed = self.context.state["seed_value"]
            seed = 0 if len(seed) == 0 else int(seed)
            GameManager().set_game(
                self.context.state["world_name"],
                seed=seed,
                water_level=int(self.context.state["water_level"]),
                forest_size=int(self.context.state["forest_size"]),
                temperature=int(self.context.state["climate"]),
            )
            GameManager().game.game_settings.set("difficulty", self.context.state["difficulty"])
            game_loop_callback(self.context.state)

        self.context.state["create_game_clicked"] = False
    

    @staticmethod
    def _create_game_callback(context: PageContext) -> None:
        context["create_game_clicked"] = True

    @staticmethod
    def _reroll_seed(context: PageContext) -> None:
        context["seed_value"] = str(random.randint(0, 99999999))
        context["reroll_called"] = True