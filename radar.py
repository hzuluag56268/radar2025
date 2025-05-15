'''
pygame.init() # <<<--- MOVER pygame.init() AL INICIO DE __init__ DE Game
'''
# check if collision_check(self.all_sprites, self.screen)
from settings import *
from util_funct import *
#from aircraft import *
from views import *
from models import *
from ui import *
from other_funct import *
from views import AircraftLabelView # <<<--- Importar la nueva clase
from panel_ui import SidePanel 
# Pygame initialization


pygame.init()

class Game:
    def __init__(self):
        print('ejercicio 0')
        self.screen = pygame.display.set_mode((SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Radar Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)  # Added font for aircraft labels
        self.panel_font = pygame.font.Font(None, 18) # <<<--- FUENTE PARA EL PANEL
        self.running = True
        
        self.elapsed_time = 0
        self.ui_manager = ui()
        self.level_str = ""
        self.exercise_num_str = "1"
        #self.exercise_num_str = input("Enter the exercise number: ")
        #print(f"Exercise number: {self.exercise_num_str}")
        self.routes_config = ROUTES 
        self.aircraft_creation_data = self.load_exercise_data('data/exercises_config.json') # <<<--- Cargar aquí
        self.selected_aircraft_model  = None # Para guardar la A/C seleccionada
        self.label_views = []

        self.all_sprites = pygame.sprite.Group() # Para AircraftSprite
        self.aircraft_models = [] # Para AircraftModel

        self.side_panel = SidePanel(self.screen, self.panel_font, self) # <<<--- INICIALIZAR SidePanel
    

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
    # Calculate elapsed, time in minutes and seconds
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        # Render the time
        time_text = self.font.render(f"Time  00 : {minutes} : {seconds:02d} ", True, (0, 255, 0))
        
        # Position the text on the screen
        self.screen.blit(time_text, (10, 10))  # Adjust position as needed
    
    def handle_collision_visualization(self):
        """Detecta conflictos y los dibuja en la pantalla."""
        # Obtener la lista de sprites activos. self.all_sprites ya debería
        # auto-limpiarse de sprites cuyos modelos no están 'alive'.
        active_sprites = list(self.all_sprites) # Convertir el grupo a lista para la función

        detected_conflicts = check_separations(active_sprites)

        for conflict in detected_conflicts:
            sprite1 = conflict['sprite1']
            sprite2 = conflict['sprite2']
            severity = conflict['severity']

            color = (255, 0, 0) if severity == "critical" else (255, 255, 0) # Rojo para crítico, Amarillo para advertencia

            # Dibujar la línea entre los centros de los sprites
            pygame.draw.aaline(self.screen, color, sprite1.rect.center, sprite2.rect.center, 2) # Línea un poco más gruesa
    # En radar.py, clase Game, método run
    
    def request_early_departure(self, aircraft_label_to_launch):
        """Autoriza un despegue temprano para un SID."""
        if self.exercise_num_str in self.aircraft_creation_data:
            for acft_data_entry in self.aircraft_creation_data[self.exercise_num_str]:
                if acft_data_entry['label'] == aircraft_label_to_launch:
                    # Solo modificar si su tiempo programado es futuro
                    if acft_data_entry['time'] > self.elapsed_time:
                        print(f"Game: Autorizando despegue para {aircraft_label_to_launch} en t={self.elapsed_time:.2f}")
                        acft_data_entry['time'] = self.elapsed_time
                        # Añadir una bandera para que update sepa que esta fue autorizada y no la vuelva a poner como "pendiente" si el tiempo coincide
                        acft_data_entry['_is_authorized_early'] = True 
                    elif not acft_data_entry.get('_is_authorized_early', False) and acft_data_entry['time'] <= self.elapsed_time:
                         # Si ya pasó su tiempo pero no fue autorizado (quizás un bug o condición de borde), igual se marca
                        acft_data_entry['_is_authorized_early'] = True
                        print(f"Game: {aircraft_label_to_launch} ya debería estar activo o fue autorizado en el mismo ciclo.")
                    break
        else:
            print(f"Error: No se encontró el ejercicio {self.exercise_num_str} para autorizar {aircraft_label_to_launch}")


    
    def run(self): #
        start_time = time.time() #
        while self.running: #
            dt = self.clock.tick(60) / 1000.0 #
            self.elapsed_time = time.time() - start_time #
            
            # Limpiar modelos y vistas de etiquetas de aeronaves "muertas"
            self.aircraft_models = [model for model in self.aircraft_models if model.alive]
            self.label_views = [lv for lv in self.label_views if lv.aircraft_model.alive]

            mouse_pos_tuple = pygame.mouse.get_pos()
            # mouse_buttons_pressed = pygame.mouse.get_pressed() # Ya no se usa directamente aquí para el panel

            label_event_consumed = False # Mover esta definición más arriba si es necesario

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                # Resetear label_event_consumed por cada evento si es lógico
                label_event_consumed_by_drag = False # Renombrar para claridad

                # 1. MANEJO DE ARRASTRE DE ETIQUETAS (como estaba)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for lv in self.label_views:
                        if lv.aircraft_model.alive:
                            if lv.handle_input_for_drag(event, mouse_pos_tuple, pygame.mouse.get_pressed()): # pasar mouse_pressed
                                label_event_consumed_by_drag = True
                                break
                elif event.type == pygame.MOUSEMOTION:
                    for lv in self.label_views:
                        if lv.dragging_label:
                            if lv.handle_input_for_drag(event, mouse_pos_tuple, pygame.mouse.get_pressed()):
                                label_event_consumed_by_drag = True
                            break
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for lv in self.label_views:
                        if lv.dragging_label:
                            if lv.handle_input_for_drag(event, mouse_pos_tuple, pygame.mouse.get_pressed()):
                                label_event_consumed_by_drag = True
                            break
                
                # Si el arrastre de etiqueta consumió el evento, no procesar más para este evento de botón
                if label_event_consumed_by_drag and (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP) :
                    continue


                # 2. MANEJO DE INPUT DEL PANEL LATERAL (antes que otros clics de UI si no fue arrastre)
                # Solo si el evento es un clic y no fue consumido por el arrastre de etiquetas.
                panel_consumed_click = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not label_event_consumed_by_drag:
                    panel_consumed_click = self.side_panel.handle_panel_input(event, mouse_pos_tuple)
                
                if panel_consumed_click: # Si el panel manejó el clic, no procesar más clics para este evento
                    continue


                # 3. OTROS EVENTOS DE UI (MENÚ, NIVEL) SI NO FUERON CONSUMIDOS ARRIBA
                if not label_event_consumed_by_drag and not panel_consumed_click: # Asegurar que no se procese doble
                    if event.type == pygame.KEYDOWN:
                        if self.ui_manager.level_window_active: # Usar self.ui_manager
                            enter_pressed = self.ui_manager.handle_level_input_keypress(event)
                            if enter_pressed:
                                entered_level = self.ui_manager.hide_level_input()
                                if self.selected_aircraft_model:
                                    # ... (lógica de set_desired_altitude como estaba) ...
                                    self.selected_aircraft_model.set_continue_descent_climb_flag(
                                        self.ui_manager.is_continue_descent
                                    )
                                    self.selected_aircraft_model.set_desired_altitude(entered_level)
                                self.selected_aircraft_model = None

                    elif event.type == pygame.MOUSEBUTTONDOWN: # Otros clics del ratón
                        if event.button == 3: # Clic Derecho: Seleccionar Aeronave / Mostrar Menú
                            self.ui_manager.hide_menu()
                            self.ui_manager.hide_level_input()
                            newly_selected_model = None
                            
                            # Prioridad al clic en etiqueta para selección (si la etiqueta no está siendo arrastrada)
                            for label_view in self.label_views:
                                if label_view.is_clicked(mouse_pos_tuple) and label_view.aircraft_model.alive:
                                    newly_selected_model = label_view.aircraft_model
                                    break
                            
                            if not newly_selected_model: # Si no, verificar clic en sprite de aeronave
                                for sprite_candidate in self.all_sprites: # self.all_sprites son AircraftSprite
                                    if sprite_candidate.rect.collidepoint(mouse_pos_tuple) and sprite_candidate.model.alive:
                                        newly_selected_model = sprite_candidate.model
                                        break
                            
                            self.selected_aircraft_model = newly_selected_model
                            
                            if self.selected_aircraft_model: # Ya se verificó .alive
                                print(f"Game: Modelo de aeronave seleccionado {self.selected_aircraft_model.label}")
                                self.ui_manager.display_menu(mouse_pos_tuple, self.selected_aircraft_model.route_type)
                            else:
                                self.selected_aircraft_model = None # Asegurar deselección

                        elif event.button == 1: # Clic Izquierdo: Procesar Menú
                            if self.ui_manager.show_menu:
                                action = self.ui_manager.process_menu_click(mouse_pos_tuple)
                                if action:
                                    self.ui_manager.hide_menu()
                                    if action == "close_menu":
                                        self.selected_aircraft_model = None
                                    elif self.selected_aircraft_model:
                                        # ... (lógica para acciones del menú como la tenías)
                                        if action == "Join Holding Pattern":
                                            self.selected_aircraft_model.set_pending_holding(True)
                                        
                                        elif action == "Finish Holding Pattern":
                                            self.selected_aircraft.set_finish_holding(True)
                                        elif action == "Stop descent at" or action == "Stop climb at":
                                            # Decirle a UI que muestre la ventana de nivel
                                            self.ui_manager.display_level_input(event.pos)
                                            # No deseleccionar aún, esperar input de nivel
                                        elif action == "Continue descent to" or action == "continue climb to":
                                            # Decirle a UI que muestre la ventana de nivel
                                            self.ui_manager.display_level_input(event.pos)
                                            # No deseleccionar aún
                                        elif action == "disregard":
                                            print("Game: Acción 'disregard' seleccionada.")
                                            self.selected_aircraft = None # Deseleccionar

                                            
                                        if action not in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to"]:
                                            self.selected_aircraft_model = None
                                    else: # Clic en menú pero no hay aeronave seleccionada (raro, pero por si acaso)
                                        self.selected_aircraft_model = None
            
            # --- FIN DEL BUCLE DE EVENTOS ---


            # --- Lógica de Actualización ---
            # Preparar datos para SidePanel update
            pending_sids_data = []
            if self.exercise_num_str in self.aircraft_creation_data:
                for acft_data in self.aircraft_creation_data[self.exercise_num_str]:
                    route_info = self.routes_config.get(acft_data['name'])
                    # Solo SIDs, que aún no han pasado su tiempo O fueron autorizados para verse en el panel
                    if route_info and route_info["type"] == "sid":
                        if acft_data['time'] > self.elapsed_time or acft_data.get('_is_authorized_early', False):
                             # Y que no estén ya 'muertos' (si se eliminan de la lista principal por alguna razón)
                            if not acft_data.get('_processed_and_killed', False):
                                pending_sids_data.append(acft_data)
            
            self.side_panel.update(self.aircraft_models, pending_sids_data, self.elapsed_time)


            
            # Acceder a los datos del ejercicio usando la clave como string
            if self.exercise_num_str in self.aircraft_creation_data:
                # Iterar sobre una copia si se va a remover elementos: self.aircraft_creation_data[self.exercise_num_str][:]
                # O marcar como procesados para evitar re-procesamiento si no se remueven
                entries_to_remove = []
                for acft_data in self.aircraft_creation_data[self.exercise_num_str]:
                    if acft_data.get('_processed_and_killed', False): # Si ya se procesó y marcó para no reaparecer
                        continue

                    
                    if self.elapsed_time >= acft_data['time']:
                        route_name = acft_data['name']
                        if route_name in self.routes_config:
                            
                            # Crear el Modelo
                            model = AircraftModel(
                                route_name=route_name,
                                initial_speed=acft_data['speed'],
                                label=acft_data['label'],
                                acft_type=acft_data['acft_type'],
                                initial_altitude=self.routes_config[route_name]['altitude'],
                                desired_altitude_init= 6000 if self.routes_config[route_name]["type"] == "star" else 24000,
                                initial_pos=self.routes_config[route_name]["pixel_points"][0],
                                route_type_val=self.routes_config[route_name]["type"],
                                routes_data=self.routes_config
                            )
                            self.aircraft_models.append(model)

                            
                            # Crear el Sprite (Vista)
                            # Determinar color para el sprite, puede ser fijo o basado en tipo, etc.
                            
                            sprite_color = (0, 200, 0) if self.routes_config[route_name]["type"] == "star" else (200, 200, 0)
                            sprite = AircraftSprite(model, sprite_color, self.screen)
                            self.all_sprites.add(sprite)

                            label_view = AircraftLabelView(model, self.font, self.screen)
                            self.label_views.append(label_view)
                            
                            # Marcar como procesado para que no se cree de nuevo y no aparezca en pending_sids si se actualiza su tiempo
                            # Si se remueve de la lista, no es necesario marcarlo así.
                            # self.aircraft_creation_data[self.exercise_num_str].remove(acft_data)
                            entries_to_remove.append(acft_data) # Mejor remover al final del bucle
                            # O si no se remueve, marcarlo:
                            # acft_data['_processed_and_killed'] = True 
                        else:
                            print(f"Advertencia: Ruta '{route_name}' no encontrada en la configuración de rutas.")
                            # self.aircraft_creation_data[self.exercise_num_str].remove(acft_data)
                            entries_to_remove.append(acft_data)
                            # acft_data['_processed_and_killed'] = True
                
                # Remover entradas procesadas (si se opta por este método)
                for entry in entries_to_remove:
                    if entry in self.aircraft_creation_data[self.exercise_num_str]:
                         self.aircraft_creation_data[self.exercise_num_str].remove(entry)




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

            self.ui_manager.draw() # Pedir a UI que se dibuje (menú, ventana nivel)
            self.side_panel.draw() # <<<--- DIBUJAR EL PANEL LATERAL
            self.display_time() #
            # Detección y dibujo de colisiones (ver Parte 3)
            self.handle_collision_visualization() # Nuevo método
            
            pygame.display.update() #

        pygame.quit() #


if __name__ == '__main__':
    #pygame.init()  # Initialize Pygame
    #screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    font = pygame.font.Font(None, 36)

    # Get exercise input
    #exercise_num_str = get_exercise_input(screen, font)

    # Pass the exercise number to the Game instance
    radar = Game()
    radar.exercise_num_str = "5"  # Set exercise number
    radar.run()

