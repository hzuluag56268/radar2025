
from settings import *
from util_funct import *
from aircraft import *
from ui import *
from other_funct import *
from views import AircraftLabelView # <<<--- Importar la nueva clase
# Pygame initialization

pygame.init()


class Game:
    def __init__(self):
        print('ejercicio 0')
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Radar Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)  # Added font for aircraft labels
        self.running = True
        
        self.elapsed_time = 0
        self.all_sprites = pygame.sprite.Group()
        
        self.ui = ui()
        self.level_str = ""
        self.exercise_num = 1
        #self.Aircraft = Aircraft
        #self.exercise_num = input("Enter the exercise number: ")
        #print(f"Exercise number: {self.exercise_num}")
        self.aircraft_timers = self.load_exercise_data('data/exercises_config.json') # <<<--- Cargar aquí
        self.selected_aircraft = None # Para guardar la A/C seleccionada
        self.label_views = []

    def load_exercise_data(self, file_path): # <<<--- Nueva función para cargar
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            # JSON guarda las claves numéricas como strings, convertirlas si es necesario
            # o acceder a ellas como strings. En tu caso, `self.aircraft_timers[str(self.exercise_num)]`
            # si las claves en JSON son "0", "1", etc.
            # Si quieres claves enteras en el dict:
            # return {int(k): v for k, v in data.items()}
            return data # Dejarlas como strings por ahora es más simple
        except FileNotFoundError:
            print(f"Error: El archivo de configuración de ejercicios '{file_path}' no fue encontrado.")
            return {} # Retornar un diccionario vacío para evitar errores
        except json.JSONDecodeError:
            print(f"Error: El archivo '{file_path}' contiene JSON inválido.")
            return {}


    def display_time(self):
    # Calculate elapsed time in minutes and seconds
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        # Render the time
        time_text = self.font.render(f"Time  00 : {minutes} : {seconds:02d} ", True, (0, 255, 0))
        
        # Position the text on the screen
        self.screen.blit(time_text, (10, 10))  # Adjust position as needed
    
    # En radar.py, clase Game, método run
    def run(self): #
        start_time = time.time() #
        while self.running: #
            dt = self.clock.tick(60) / 1000.0 #
            self.elapsed_time = time.time() - start_time #
            self.label_views = [lv for lv in self.label_views if lv.aircraft.alive()]
            # mouse_pos = pygame.mouse.get_pos() # Obtener si es necesario
            
            for event in pygame.event.get(): #
                if event.type == pygame.QUIT: #
                    self.running = False #

                # --- Manejo de Input de Teclado (Pasar a UI si es necesario) ---
                if event.type == pygame.KEYDOWN: #
                    if self.ui.level_window_active: # Verificar si la ventana de nivel está activa
                        enter_pressed = self.ui.handle_level_input_keypress(event) # Pasar evento a UI
                        if enter_pressed: # Si UI indica que se presionó Enter
                            entered_level = self.ui.hide_level_input() # Ocultar y obtener valor
                            if self.selected_aircraft: # Aplicar al seleccionado
                                # Pasar la bandera de continuación desde UI a Aircraft
                                self.selected_aircraft.set_continue_descent_climb_flag(
                                    self.ui.is_continue_descent
                                )
                                self.selected_aircraft.set_desired_altitude(entered_level)
                            # Deseleccionar después de la acción de nivel
                            self.selected_aircraft = None

                # --- Manejo de Clics del Mouse ---
                if event.type == pygame.MOUSEBUTTONDOWN: #
                    # --- Clic Derecho: Seleccionar Aeronave / Mostrar Menú ---
                    if event.button == 3: # Botón derecho
                        # Primero, ocultar cualquier menú/ventana existente y deseleccionar
                        self.ui.hide_menu()
                        self.ui.hide_level_input()
                        currently_selected = None # Temporal para guardar la nueva selección
                        
                        for label_view in self.label_views:
                            if label_view.is_clicked(event.pos): # Preguntar a la vista
                                currently_selected = label_view.aircraft # Obtener la aeronave asociada
                                break

                        self.selected_aircraft = currently_selected # Actualizar selección
                        if self.selected_aircraft:
                            if self.selected_aircraft.alive():
                                print(f"Game: Aeronave seleccionada {self.selected_aircraft.label}")
                                route_type = self.selected_aircraft.route_type
                                self.ui.display_menu(event.pos, route_type)
                            else:
                                 # La aeronave fue eliminada justo antes del clic?
                                 self.selected_aircraft = None
                                 print("Game: Clicked on label of killed aircraft?")
                        else:
                            # Si no se hizo clic en ninguna etiqueta, no hacer nada o deseleccionar (ya hecho)
                            print("Game: Clic derecho en espacio vacío.")


                    # --- Clic Izquierdo: Procesar Menú ---
                    elif event.button == 1: # Botón izquierdo
                        if self.ui.show_menu: # Solo si el menú está visible
                            action = self.ui.process_menu_click(event.pos) # Preguntar a UI qué acción es
                            if action: # Si se hizo clic en una opción o fuera
                                self.ui.hide_menu() # Ocultar menú después del clic
                                if action == "close_menu":
                                    self.selected_aircraft = None # Deseleccionar si se hizo clic fuera
                                elif self.selected_aircraft: # Si había una A/C seleccionada
                                    # --- Ejecutar Acciones ---
                                    print(f"Game: Ejecutando acción '{action}' para {self.selected_aircraft.label}")
                                    if action == "Join Holding Pattern":
                                        self.selected_aircraft.set_pending_holding(True)
                                    elif action == "Finish Holding Pattern":
                                        self.selected_aircraft.set_finish_holding(True)
                                    elif action == "Stop descent at" or action == "Stop climb at":
                                        # Decirle a UI que muestre la ventana de nivel
                                        self.ui.display_level_input(event.pos)
                                        # No deseleccionar aún, esperar input de nivel
                                    elif action == "Continue descent to" or action == "continue climb to ":
                                        # Decirle a UI que muestre la ventana de nivel
                                        self.ui.display_level_input(event.pos)
                                        # No deseleccionar aún
                                    elif action == "disregard":
                                        print("Game: Acción 'disregard' seleccionada.")
                                        self.selected_aircraft = None # Deseleccionar

                                    # Deseleccionar si la acción no requiere input de nivel posterior
                                    if action not in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to "]:
                                        self.selected_aircraft = None
                                else:
                                    # Caso raro: clic en menú sin aeronave seleccionada
                                    self.selected_aircraft = None

                        # Podrías añadir lógica aquí para otros clics izquierdos (ej. arrastrar etiqueta si se movió esa lógica a Game)


            # --- Fin del bucle de eventos ---

            # --- Lógica de Actualización ---
            # Acceder a los datos del ejercicio usando la clave como string
            current_exercise_key = str(self.exercise_num) # <<<--- Clave como string
            if current_exercise_key in self.aircraft_timers:
                for acft_data in self.aircraft_timers[current_exercise_key][:]:
                    if self.elapsed_time >= acft_data['time']:
                        # Usar ROUTES de settings (o util_funct si se movió allí)
                        new_aircraft = Aircraft(self.all_sprites, (0, 100, 0), acft_data['name'],
                                              acft_data['speed'], acft_data['label'], self.screen,
                                              acft_data['acft_type'])
                        new_label_view = AircraftLabelView(new_aircraft, self.font)
                        self.label_views.append(new_label_view)
                        self.aircraft_timers[current_exercise_key].remove(acft_data)
            else:
                # Opcional: manejar el caso donde el número de ejercicio no tiene datos
                print(f"Advertencia: No hay datos para el ejercicio {self.exercise_num}")
                
            self.all_sprites.update(dt) #
            

            # --- Lógica de Dibujo ---
            self.screen.fill((0, 0, 0)) #
            # ... (dibujo de rutas como antes) ...
            for route_name, route_data in ROUTES.items():
                route_label = self.font.render(f"{route_name} ", True, (0, 255, 0))
                if route_data["type"] == "star" and route_name != "DIMIL_star":
                    self.screen.blit(route_label, route_data["pixel_points"][0] )
                if route_data["type"] == "sid":
                    self.screen.blit(route_label, route_data["pixel_points"][-1] )
                for i in range(len(route_data["pixel_points"]) - 1):
                    pygame.draw.aaline(self.screen, route_data["color"], route_data["pixel_points"][i], route_data["pixel_points"][i + 1], 1)
            # Dibujar sprites y sus etiquetas
            self.all_sprites.draw(self.screen) # Dibuja el círculo/imagen base de los sprites
            
            
            for label_view in self.label_views:
                label_view.draw() # Llamar al método draw de la vista

            self.ui.draw() # Pedir a UI que se dibuje (menú, ventana nivel)
            self.display_time() #
            collision_check(self.all_sprites, self.screen) #
            pygame.display.update() #

        pygame.quit() #

if __name__ == '__main__':
    #pygame.init()  # Initialize Pygame
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    font = pygame.font.Font(None, 36)

    # Get exercise input
    #exercise_num = get_exercise_input(screen, font)

    # Pass the exercise number to the Game instance
    radar = Game()
    radar.exercise_num = 0  # Set exercise number
    radar.run()

