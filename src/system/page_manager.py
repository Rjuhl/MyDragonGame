from decorators import singleton
from system.pages.null_page import NullPage
from system.page_context import PageContext
from regestries import PAGE_REGISTRY

# import pages to make sure they are registerer
from system.pages import *


@singleton
class PageManager:
    def __init__(self, pageContext: PageContext):
        self.context = pageContext
        self.current_page = None
        self.prev_page = None
        self.pages = {}

        for page in PAGE_REGISTRY:
            self.pages[page.__name__] = page(pageContext)
            if PAGE_REGISTRY[page]: self.current_page = self.pages[page.__name__]


    
    def show_page(self) -> bool:
        self.current_page.update()
        if self.current_page != self.pages[self.context.state["next_page"]]:
            self.prev_page = self.current_page
            self.context.state["prev_page"] = self.prev_page.__class__.__name__
        self.current_page = self.pages[self.context.state["next_page"]]
        return not isinstance(self.current_page, NullPage)

