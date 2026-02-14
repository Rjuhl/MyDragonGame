from pygame.locals import K_ESCAPE
from decorators import register_page
from gui.page import Page
from system.pages.pause_page import PausePage
from system.pages.respawn_page import Respawn
from system.input_handler import input_handler
from world.game import GameManager
from system.global_vars import game_globals
from metrics.simple_metrics import timeit

@register_page
class GamePage(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)

    @timeit(base=True)
    def update(self) -> None:
        game_manager = GameManager()
        game_manager.game.map.update()
        items_rendered = self.context.renderer.draw(game_manager.game.map, game_manager.screen, optimize=game_globals.optimize_render)
        self.context.state["items_rendered"] = items_rendered
        self.context.state["next_page"] = self.__class__.__name__
        if input_handler.was_key_pressed(K_ESCAPE):
            self.context.state["next_page"] = PausePage.__name__
        if input_handler.is_player_dead():
            self.context.state["next_page"] = Respawn.__name__