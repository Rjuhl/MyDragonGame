from pygame.locals import K_ESCAPE
from decorators import register_page
from gui.page import Page
from system.pages.pause_page import PausePage
from system.pages.respawn_page import Respawn
from system.input_handler import input_handler
from world.game import GameManager
from gui.container import Container
from gui.types import ItemAlign, ItemAppend
from gui.atoms.percentage_icon import PercentageIcon
from system.global_vars import game_globals
from metrics.simple_metrics import timeit

@register_page
class GamePage(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)
    
        self.health_icon = PercentageIcon("health_icon.png")
        self.energy_icon = PercentageIcon("energy_icon.png")
        self.fire_icon = PercentageIcon("fire_icon.png")

        icon_container = Container(
            "98%", "36%",
            ItemAlign.Last, ItemAlign.Last, ItemAppend.Below,
            children=[
                self.health_icon,
                self.energy_icon,
                self.fire_icon,
            ],
            gap=10
        )

        base_container = Container(
            "100%", "98%", 
            ItemAlign.Center, ItemAlign.Last, ItemAppend.Below,
            children = [icon_container]
        )

        self.add_container(0, 0, base_container)

    def _update_icons(self):
        player = GameManager().game.player
        self.health_icon.set_percentage(player.current_health / player.max_health)
        self.energy_icon.set_percentage(player.current_energy / player.max_energy)
        self.fire_icon.set_percentage(player.fire_charge / player.max_fire_charge)

    def _render_ui_elements(self):
        self._update_icons()
        self.render()

    @timeit(base=True)
    def update(self) -> None:
        game_manager = GameManager()
        game_manager.game.map.update()
        items_rendered = self.context.renderer.draw(game_manager.game.map, game_manager.screen, optimize=game_globals.optimize_render)
        self._render_ui_elements()
        self.context.state["items_rendered"] = items_rendered
        self.context.state["next_page"] = self.__class__.__name__
        if input_handler.was_key_pressed(K_ESCAPE):
            self.context.state["next_page"] = PausePage.__name__
        if input_handler.is_player_dead():
            self.context.state["next_page"] = Respawn.__name__