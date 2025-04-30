from settings import *


class ui():
    def __init__(self, ):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 30)
        self.left = 0 
        self.top = 0
        self.cols = 1
        self.route_name = None
        self.option_height = 25
        self.show_menu = False
        self.level_window_active = False
        self.string_level = ""
        self.update_level = False
        self.is_continue_descent = False
        self.active_aircraft_type = None # Guardar tipo de ruta (star/sid) para opciones de menú
        self.is_star = None 
        self.star_options =  ["Join Holding Pattern", "Finish Holding Pattern", "Stop descent at","Continue descent to", "disregard"]
        self.sid_options = ["Stop climb at", "continue climb to ", "disregard"]
        

        self.menu_options =  None
        self.rows = None

    # En ui.py, clase ui
    def process_menu_click(self, pos):
        """ Procesa un clic en el menú y devuelve la acción seleccionada, o None. """
        if not self.show_menu: #
            return None

        # Reconstruir el Rect del menú para verificar colisión
        menu_rect = pygame.Rect(self.left + 10, self.top + 10, self.cols * 400, self.rows * self.option_height) #
        if not menu_rect.collidepoint(pos):
            # Clic fuera del menú (Game lo cerrará)
            return "close_menu" # Identificador especial

        # Calcular en qué opción se hizo clic (lógica similar a draw)
        for col in range(self.cols): #
            for row in range(self.rows): #
                # Calcular centro de la opción
                x = menu_rect.left + menu_rect.width / (self.cols * 2) + (menu_rect.width / self.cols) * col
                y = menu_rect.top + menu_rect.height / (self.rows * 2) + (menu_rect.height / self.rows) * row
                i = row # Asumiendo una sola columna

                # Crear un Rect temporal para la opción de texto
                option_text_surf = self.font.render(self.menu_options[i], True, (0, 255, 0)) #
                option_text_rect = option_text_surf.get_rect(center=(x, y)) #

                if option_text_rect.collidepoint(pos):
                    selected_action = self.menu_options[i] #
                    print(f"UI: Acción seleccionada '{selected_action}'")

                    # Guardar si la acción implica continuar descenso/ascenso
                    self.is_continue_descent = "Continue" in selected_action or "continue" in selected_action #

                    return selected_action # Devolver la acción
        return None # No se hizo clic en ninguna opción
    
    def show_level(self):
        
        if self.level_window_active: 
            rect2 = pygame.Rect(0, 0 , 400,25)
            pygame.draw.rect(self.display_surface, (0, 0, 0),rect2, 0, 4) 
            pygame.draw.rect(self.display_surface, (0, 0,80),rect2, 4, 4)

            text_surf2 = self.font.render(f"level: {self.string_level}", True, (0, 255, 0))        
            text_rect2 = text_surf2.get_rect(center = (rect2.centerx,rect2.centery))
            self.display_surface.blit(text_surf2, text_rect2)
        
    
    def display_menu(self, position, aircraft_route_type):
        """ Muestra el menú en la posición dada, adaptado al tipo de ruta. """
        self.left, self.top = position #
        self.active_aircraft_type = aircraft_route_type # Guardar tipo

        # Determinar opciones según el tipo de ruta (STAR o SID)
        is_star = aircraft_route_type == "star"
        self.menu_options = self.star_options if is_star else self.sid_options #
        self.rows = len(self.menu_options) #
        self.show_menu = True #
        self.level_window_active = False # Asegurarse que la ventana de nivel esté cerrada

    def hide_menu(self):
        """ Oculta el menú. """
        self.show_menu = False #

    def display_level_input(self, position):
        """ Muestra la ventana de entrada de nivel. """
        self.string_level = "" # Resetear texto
        # Podrías usar la 'position' para colocar la ventana cerca del clic
        # O usar una posición fija (ej. centro pantalla o self.left/self.top)
        self.level_window_active = True #
        self.show_menu = False # Ocultar menú si estaba visible

    def hide_level_input(self):
        """ Oculta la ventana de entrada de nivel y devuelve el valor. """
        self.level_window_active = False #
        entered_level = self.string_level #
        self.string_level = "" # Limpiar para la próxima vez
        return entered_level # Devolver valor ingresado

    def handle_level_input_keypress(self, event):
        """ Procesa eventos de teclado para la entrada de nivel. Devuelve True si se presionó Enter. """
        if not self.level_window_active: #
            return False

        if event.key == pygame.K_RETURN: # (Originalmente en Game, ahora encapsulado aquí)
            print("UI: Enter presionado en Level Input")
            # Game llamará a hide_level_input para obtener el valor
            return True # Indica que se completó la entrada
        elif event.key == pygame.K_BACKSPACE: #
            self.string_level = self.string_level[:-1] #
        elif event.unicode.isdigit(): #
            self.string_level += event.unicode #
        return False # Entrada aún no completada

    
    def draw(self):
        if self.level_window_active: #
            self.show_level() #
        if not self.show_menu: #
            return
        
        if self.level_window_active:
            self.show_level()
        # bg
        if not self.show_menu:
            return
        # Dynamic placement (ensure label stays within the screen bounds)
                
        if self.left + 10 + self.cols * 400 > self.display_surface.get_width():
            self.left -= 10 + self.cols * 400
        if self.top + 10 + self.rows * self.option_height > self.display_surface.get_height():
            self.top -= 10 + self.rows * self.option_height
        rect = pygame.Rect(self.left + 10, self.top + 10 ,self.cols * 400, self.rows * self.option_height)
        pygame.draw.rect(self.display_surface, (0, 0, 0),rect, 0, 4)
        pygame.draw.rect(self.display_surface, (0, 80, 0),rect, 4, 4)
        # Draw menu options
        for col in range(self.cols):
            for row in range(self.rows):
                x = rect.left + rect.width / (self.cols * 2) + (rect.width / self.cols) * col
                y = rect.top + rect.height / (self.rows * 2) + (rect.height / self.rows) * row
                i = row
                # Asegúrate de que self.menu_options no sea None antes de acceder
                if self.menu_options and i < len(self.menu_options):
                    text_surf = self.font.render(self.menu_options[i], True, (0, 255, 0))
                    text_rect = text_surf.get_rect(center = (x,y))
                    self.display_surface.blit(text_surf, text_rect)
                    # self.get_input(text_rect,i) # <-- Mover el manejo de input a Game.run
        
        