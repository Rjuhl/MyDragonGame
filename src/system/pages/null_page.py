from decorators import register_page
from gui.page import Page 

@register_page
class NullPage(Page):
    def __init__(self, pageContext):
        super().__init__(None)