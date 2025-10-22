import pygame
from gui.types import ItemAlign, ItemAppend, ClickEvent
from gui.component import Component
from typing import Optional, List, Dict, Any
from pathlib import Path

class Container(Component):
    def __init__(
        self,
        w: str, h: str,
        alignment_x: ItemAlign,
        alignment_y: ItemAlign, 
        stack_direction: ItemAppend,
        *,
        children: List[Component] = [],
        backgrounds: Optional[List[Path]] = None,
        padding: int = 0,
        gap: int = 0
    ):
        # Let Component set x, y, w, h, size units, and background
        super().__init__(w=w, h=h, backgrounds=backgrounds)

        self.alignment_x = alignment_x
        self.alignment_y = alignment_y
        self.stack_direction = stack_direction
        self.padding = padding
        self.gap = gap
        self.children = children
    
    def add_child(self, child: Component):
        self.children.append(child)

    def handle_mouse_actions(self, mouse_pos: tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        for child in self.children: 
            child.handle_mouse_actions(mouse_pos, click_event, state_dict)

    def reposition_children(self) -> None:
        # Container pixel size (depends on container's parent size)
        c_w, c_h = self.get_size()
        inner_w = max(0, c_w - 2 * self.padding)
        inner_h = max(0, c_h - 2 * self.padding)

        #  Resolve each child's size relative to container
        children_sizes = []
        for child in self.children:
            child.parent_w = c_w
            child.parent_h = c_h
            children_sizes.append(child.get_size())

        # Horizontal stack (append Right)
        if self.stack_direction == ItemAppend.Right:
            total_w = sum(w for w, _ in children_sizes) + self.gap * max(0, len(self.children) - 1)

            # horizontal starting x based on alignment_x within inner width
            if self.alignment_x == ItemAlign.Center:
                start_x = self.x + self.padding + max(0, (inner_w - total_w) // 2)
            elif self.alignment_x == ItemAlign.Last:
                start_x = self.x + self.padding + max(0, inner_w - total_w)
            else:  
                start_x = self.x + self.padding

            x_cursor = start_x
            for child, (w, h) in zip(self.children, children_sizes):
                # vertical placement per child height and alignment_y
                if self.alignment_y == ItemAlign.Center:
                    y_pos = self.y + self.padding + max(0, (inner_h - h) // 2)
                elif self.alignment_y == ItemAlign.Last:
                    y_pos = self.y + self.padding + max(0, inner_h - h)
                else:  
                    y_pos = self.y + self.padding

                child.x = x_cursor
                child.y = y_pos
                x_cursor += w + self.gap

        # Vertical stack (append Below)
        else: 
            total_h = sum(h for _, h in children_sizes) + self.gap * max(0, len(self.children) - 1)

            # vertical starting y based on alignment_y within inner height
            if self.alignment_y == ItemAlign.Center:
                start_y = self.y + self.padding + max(0, (inner_h - total_h) // 2)
            elif self.alignment_y == ItemAlign.Last:
                start_y = self.y + self.padding + max(0, inner_h - total_h)
            else:  # First
                start_y = self.y + self.padding

            y_cursor = start_y
            for child, (w, h) in zip(self.children, children_sizes):
                # horizontal placement per child width and alignment_x
                if self.alignment_x == ItemAlign.Center:
                    x_pos = self.x + self.padding + max(0, (inner_w - w) // 2)
                elif self.alignment_x == ItemAlign.Last:
                    x_pos = self.x + self.padding + max(0, inner_w - w)
                else:  # First
                    x_pos = self.x + self.padding

                child.x = x_pos
                child.y = y_cursor
                y_cursor += h + self.gap
            
        for child in self.children: child.reposition_children() 


    def render(self, surface: pygame.Surface) -> None:
        if self.background: surface.blit(self.background, (self.x, self.y))
        for child in self.children: child.render(surface)