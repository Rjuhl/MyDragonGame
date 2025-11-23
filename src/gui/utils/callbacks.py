from system.page_context import PageContext

def quit_game_callback(context: PageContext) -> None:
    from system.pages.null_page import NullPage  # Local import to avoid circular import
    context["next_page"] = NullPage.__name__

def game_loop_callback(context: PageContext) -> None:
    from system.pages.game_page import GamePage  # Local import to avoid circular import
    context["next_page"] = GamePage.__name__

def settings_callback(context: PageContext) -> None:
    from system.pages.settings_page import SettingsPage  # Local import to avoid circular import
    context["next_page"] = SettingsPage.__name__

def main_menu_callback(context: PageContext) -> None:
    from system.pages.main_menu import MainMenu  # Local import to avoid circular import
    context["next_page"] = MainMenu.__name__

def create_game_callback(context: PageContext) -> None:
    from system.pages.create_game_page import CreateGamePage  # Local import to avoid circular import
    context["next_page"] = CreateGamePage.__name__

def choose_game_callback(context: PageContext) -> None:
    from system.pages.choose_game_page import ChooseGamePage  # Local import to avoid circular import
    context["next_page"] = ChooseGamePage.__name__

def previous_page_callback(context: PageContext) -> None:
    if "prev_page" in context:
        context["next_page"] = context["prev_page"]