from system.page_context import PageContext
from system.pages.null_page import NullPage

def quit_game_callback(context: PageContext) -> None:
        context["next_page"] = NullPage.__name__