from system.page_context import PageContext

def quit_game_callback(context: PageContext) -> None:
        from system.pages.null_page import NullPage  # Local import to avoid circular import
        context["next_page"] = NullPage.__name__ 

def game_loop_callback(context: PageContext) -> None:
        from system.pages.game_page import GamePage  # Local import to avoid circular import
        context["next_page"] = GamePage.__name__