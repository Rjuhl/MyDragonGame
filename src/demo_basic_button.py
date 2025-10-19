import pygame
from gui.buttons.basic_button import BasicButton
from gui.types import ClickEvent

pygame.init()

SCREEN_SIZE = (400, 200)
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("BasicButton Demo")
clock = pygame.time.Clock()

# Callback for button click
def on_button_click(state):
    print("Button clicked!")

# Create BasicButton (absolute size for demo)
button = BasicButton("200", "60", "Click Me!", 24, on_button_click)
button.x = 100
button.y = 70
button.parent_w = SCREEN_SIZE[0]
button.parent_h = SCREEN_SIZE[1]
button.reposition_children()

running = True
while running:
    screen.fill((30, 30, 40))
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()
    click_event = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click_event = ClickEvent.Left

    
    button.reposition_children()
    is_above = button.mouse_over(mouse_pos)
    button.handle_mouse_actions(is_above, click_event, {})
    button.render(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
