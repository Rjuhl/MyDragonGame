from decorators import register_page
from gui.page import Page
from system.pages.pause_page import PausePage


@register_page(default=True)
class GamePage(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)

    def update(self) -> None:
        self.context.map.update()
        items_rendered = self.context.renderer.draw(self.context.map, self.context.screen)
        self.context.state["items_rendered"] = items_rendered
        self.context.state["next_page"] = self.__class__.__name__
        if event := self.context.event_handler.event_tick():
            if event == "escape": self.context.state["next_page"] = PausePage.__name__
