from utils.coords import Coord

class RenderObj:
    def __init__(self, id: int, draw_location: Coord, render_order: tuple[float], isShadow=False, location=None, size=None):
        self.id = id
        self.draw_location = draw_location
        self.render_order = render_order
        self.isShadow = isShadow
        self.location = location
        self.size = size
