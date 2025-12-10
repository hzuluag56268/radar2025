"""
Additional utility functions.

This module contains helper functions that are not currently used in the main
game flow but may be useful for future features or testing.

Currently contains:
- get_exercise_input(): Interactive exercise selection (blocking input loop)
"""

from settings import *


def get_exercise_input(screen, font):
    """
    Display an interactive input window for exercise selection.
    
    This function creates a blocking input loop that allows the user to
    type an exercise number (0-4) and press Enter to select it.
    
    Note: This function is currently not used in the main game flow.
    Exercise selection is done by modifying exercise_num_str in radar.py.
    
    Args:
        screen: Pygame surface for drawing
        font: Font for text rendering
        
    Returns:
        Selected exercise number (0-4) when user presses Enter
    """
    input_active = True
    user_text = ""
    input_rect = pygame.Rect(200, 300, 250, 50)
    color_active = (0, 255, 0)  # Green when active
    color_inactive = (255, 255, 255)  # White when inactive
    color = color_inactive

    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Toggle active state on click
                if input_rect.collidepoint(event.pos):
                    input_active = True
                    color = color_active
                else:
                    color = color_inactive
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # Enter key
                    try:
                        exercise_num = int(user_text)
                        if exercise_num in range(5):  # Valid range: 0-4
                            return exercise_num
                        else:
                            user_text = "Invalid! Enter 0-4."
                    except ValueError:
                        user_text = "Invalid! Enter 0-4."
                elif event.key == pygame.K_BACKSPACE:  # Backspace
                    user_text = user_text[:-1]
                elif event.unicode.isdigit():  # Digit key
                    user_text += event.unicode

        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw input box
        pygame.draw.rect(screen, color, input_rect, 2)

        # Display current input text
        text_surface = font.render(user_text, True, (255, 255, 255))
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))

        # Display prompt
        prompt_text = font.render("Enter exercise number (0-4):", True, (255, 255, 255))
        screen.blit(prompt_text, (200, 250))

        # Update display
        pygame.display.flip()
