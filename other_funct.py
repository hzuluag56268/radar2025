from settings import *


def get_exercise_input(screen, font):
    input_active = True
    user_text = ""
    input_rect = pygame.Rect(200, 300, 250, 50)
    color_active = (0, 255, 0)
    color_inactive = (255, 255, 255)
    color = color_inactive

    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    input_active = True
                    color = color_active
                else:
                    color = color_inactive
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try:
                        exercise_num = int(user_text)
                        if exercise_num in range(5):
                            return exercise_num
                        else:
                            user_text = "Invalid! Enter 0-4."
                    except ValueError:
                        user_text = "Invalid! Enter 0-4."
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                elif event.unicode.isdigit():
                    user_text += event.unicode

        screen.fill((0, 0, 0))  # Clear screen
        pygame.draw.rect(screen, color, input_rect, 2)  # Draw input box

        text_surface = font.render(user_text, True, (255, 255, 255))
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))  # Display text in the box

        prompt_text = font.render("Enter exercise number (0-4):", True, (255, 255, 255))
        screen.blit(prompt_text, (200, 250))  # Display prompt text

        pygame.display.flip()  # Update the display

