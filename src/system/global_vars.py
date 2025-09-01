from decorators import singleton

@singleton
class Globals:
    def __init__(self):
        self._data = {}

    def __getattr__(self, name):
        # Called when attribute isn't found normally
        return self._data.get(name)

    def __setattr__(self, name, value):
        if name == '_data':  # allow regular setting for internal storage
            super().__setattr__(name, value)
        else:
            self._data[name] = value

game_globals = Globals()


def set_base_globals():
    game_globals.chunk_borders_on = False