from pygame.locals import K_ESCAPE
from decorators import register_page
from gui.page import Page
from system.pages.pause_page import PausePage
from system.input_handler import input_handler


@register_page#(default=True)
class GamePage(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)

    def update(self) -> None:
        self.context.map.update()
        items_rendered = self.context.renderer.draw(self.context.map, self.context.screen)
        self.context.state["items_rendered"] = items_rendered
        self.context.state["next_page"] = self.__class__.__name__
        if input_handler.was_key_pressed(K_ESCAPE):
            self.context.state["next_page"] = PausePage.__name__
