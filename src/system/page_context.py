# --------------------------------------------------------------------------
# Will be resonsiable for keeping track saving/loading data need to load pages
# --------------------------------------------------------------------------


class PageContext:
    def __init__(self, display, player, map, event_handler, renderer, screen):
        self.state = {}
        self.display = display
        self.player = player
        self.map = map
        self.renderer = renderer
        self.event_handler = event_handler
        self.screen = screen
    
    def load(self):
        pass

    def save(self):
        pass