# check if collision_check(self.all_sprites, self.screen)
from settings import *
from util_funct import *
from aircraft import *
from views import *
from models import *
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
        self.ui = ui()
        self.level_str = ""
        self.exercise_num_str = "1"
        #self.Aircraft = Aircraft
        #self.exercise_num_str = input("Enter the exercise number: ")
        #print(f"Exercise number: {self.exercise_num_str}")
        self.routes_config = ROUTES 
        self.aircraft_timers = self.load_exercise_data('data/exercises_config.json') # <<<--- Cargar aquí
        self.selected_aircraft_model  = None # Para guardar la A/C seleccionada
        self.label_views = []

        self.all_sprites = pygame.sprite.Group() # Para AircraftSprite
        self.aircraft_models = [] # Para AircraftModel

    def load_exercise_data(self, file_path): # <<<--- Nueva función para cargar
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            # JSON guarda las claves numéricas como strings, convertirlas si es necesario
            # o acceder a ellas como strings. En tu caso, `self.aircraft_timers[str(self.exercise_num_str)]`
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
            
            # Limpiar modelos y vistas de etiquetas de aeronaves "muertas"
            self.aircraft_models = [model for model in self.aircraft_models if model.alive]
            self.label_views = [lv for lv in self.label_views if lv.aircraft_model.alive] # AircraftLabelView necesitará ref. a model


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
                            if self.selected_aircraft_model: # Aplicar al seleccionado
                                # Pasar la bandera de continuación desde UI a Aircraft
                                self.selected_aircraft_model.set_continue_descent_climb_flag(
                                    self.ui.is_continue_descent
                                )
                                self.selected_aircraft_model.set_desired_altitude(entered_level)
                            # Deseleccionar después de la acción de nivel
                            self.selected_aircraft_model = None

                # --- Manejo de Clics del Mouse ---
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3: # Clic derecho
                        self.ui.hide_menu()
                        self.ui.hide_level_input()
                        newly_selected_model = None
                        
                        # Prioridad al clic en etiqueta si existe
                        for label_view in self.label_views:
                            if label_view.is_clicked(event.pos):
                                newly_selected_model = label_view.aircraft_model # Asumiendo que label_view tiene ref al model
                                break
                        
                        # Si no se hizo clic en etiqueta, comprobar clic en sprite de aeronave
                        if not newly_selected_model:
                            for sprite in self.all_sprites: # self.all_sprites contiene AircraftSprite
                                if sprite.rect.collidepoint(event.pos) and hasattr(sprite, 'model'):
                                    newly_selected_model = sprite.model
                                    break
                        
                        self.selected_aircraft_model = newly_selected_model
                        
                        if self.selected_aircraft_model and self.selected_aircraft_model.alive:
                            print(f"Game: Modelo de aeronave seleccionado {self.selected_aircraft_model.label}")
                            route_type = self.selected_aircraft_model.route_type
                            self.ui.display_menu(event.pos, route_type) # display_menu podría necesitar el tipo o el modelo
                        else:
                            self.selected_aircraft_model = None # Deseleccionar si no es válido
                            # print("Game: Clic derecho en espacio vacío o aeronave no viva.")

                    elif event.button == 1: # Clic izquierdo
                        if self.ui.show_menu:
                            action = self.ui.process_menu_click(event.pos)
                            if action:
                                self.ui.hide_menu()
                                if action == "close_menu":
                                    self.selected_aircraft_model = None
                                elif self.selected_aircraft_model:
                                    print(f"Game: Ejecutando acción '{action}' para {self.selected_aircraft_model.label}")
                                    if action == "Join Holding Pattern":
                                        self.selected_aircraft_model.set_pending_holding(True)
                                    elif action == "Finish Holding Pattern":
                                        self.selected_aircraft_model.set_finish_holding(True)
                                    elif action == "Stop descent at" or action == "Stop climb at":
                                        self.ui.display_level_input(event.pos) # UI se encarga de mostrar
                                    elif action == "Continue descent to" or action == "continue climb to ":
                                        self.ui.display_level_input(event.pos)
                                    elif action == "disregard":
                                        self.selected_aircraft_model = None
                                    
                                    if action not in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to "]:
                                        self.selected_aircraft_model = None
                                else: # Clic en menú sin modelo seleccionado
                                    self.selected_aircraft_model = None
                        # else: # Clic izquierdo fuera del menú, podría ser para arrastrar etiquetas
                        #     for lv in self.label_views:
                        #         lv.handle_drag_input(event, pygame.mouse.get_pos(), pygame.mouse.get_pressed())

            # --- Fin del bucle de eventos ---

            # --- Lógica de Actualización ---
            # Acceder a los datos del ejercicio usando la clave como string
            if self.exercise_num_str in self.aircraft_creation_data:
                for acft_data in self.aircraft_creation_data[self.exercise_num_str][:]:
                    if self.elapsed_time >= acft_data['time']:
                        route_name = acft_data['name']
                        if route_name in self.routes_config:
                            route_info = self.routes_config[route_name]
                            
                            # Crear el Modelo
                            model = AircraftModel(
                                route_name=route_name,
                                initial_speed=acft_data['speed'],
                                label=acft_data['label'],
                                acft_type=acft_data['acft_type'],
                                initial_altitude=route_info['altitude'], # Altitud inicial de la ruta
                                desired_altitude_init= 6000 if route_info["type"] == "star" else 24000, # Altitud deseada inicial
                                initial_pos=route_info["pixel_points"][0],
                                route_type_val=route_info["type"],
                                routes_data=self.routes_config # Pasar la configuración completa de rutas
                            )
                            self.aircraft_models.append(model)

                            # Crear el Sprite (Vista)
                            # Determinar color para el sprite, puede ser fijo o basado en tipo, etc.
                            sprite_color = (0, 200, 0) if route_info["type"] == "star" else (200, 200, 0)
                            sprite = AircraftSprite(model, sprite_color, self.screen)
                            self.all_sprites.add(sprite)

                            # Crear la Vista de Etiqueta (asumiendo que se actualiza para tomar el modelo)
                            # AircraftLabelView ahora tomará el AircraftModel
                            label_view = AircraftLabelView(model, self.font, self.screen) # Pasar screen si es necesario
                            self.label_views.append(label_view)
                            
                            self.aircraft_creation_data[self.exercise_num_str].remove(acft_data)
                        else:
                            print(f"Advertencia: Ruta '{route_name}' no encontrada en la configuración de rutas.")
                            self.aircraft_creation_data[self.exercise_num_str].remove(acft_data) # Evitar reintentos


            # --- Lógica de Actualización de Modelos ---
            for model in self.aircraft_models:
                model.update(dt)

                
            self.all_sprites.update() #
            

            # --- Lógica de Dibujo ---
            self.screen.fill((0, 0, 0)) #
            # ... (dibujo de rutas como antes) ...
            for route_name, route_data in self.routes_config.items():
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
            # Detección y dibujo de colisiones (ver Parte 3)
            self.handle_collision_visualization() # Nuevo método
            collision_check(self.all_sprites, self.screen) #
            pygame.display.update() #

        pygame.quit() #

def handle_collision_visualization(self):
        # Esta función llamará a la función de utilidad (que solo detecta)
        # y luego dibujará aquí. (Se detalla en la Parte 3)
        pass

if __name__ == '__main__':
    #pygame.init()  # Initialize Pygame
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    font = pygame.font.Font(None, 36)

    # Get exercise input
    #exercise_num_str = get_exercise_input(screen, font)

    # Pass the exercise number to the Game instance
    radar = Game()
    radar.exercise_num_str = "0"  # Set exercise number
    radar.run()

