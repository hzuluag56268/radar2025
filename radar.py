# radar.py
import pygame
import time
import json

from settings import *
from util_funct import *
from views import AircraftSprite, AircraftLabelView 
from models import AircraftModel
from ui import ui # En tu __init__ lo llamas self.ui_manager
from other_funct import * 
from panel_ui import SidePanel 

pygame.init()

TAXIING_DURATION = 180 # 3 minutos en segundos. ¡Asegúrate de que esto esté definido!

class Game:
    def __init__(self):
        print('ejercicio 0') 
        self.screen = pygame.display.set_mode((SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Radar Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.panel_font = pygame.font.Font(None, 18) 
        self.running = True
        
        self.elapsed_time = 0.0 
        self.ui_manager = ui() # Usar self.ui_manager consistentemente
        self.level_str = ""
        self.exercise_num_str = "1" 
        
        self.routes_config = ROUTES 
        self.aircraft_creation_data = self.load_exercise_data('data/exercises_config.json') 
        self.selected_aircraft_model  = None
        self.label_views = []

        self.all_sprites = pygame.sprite.Group()
        self.aircraft_models = []

        self.side_panel = SidePanel(self.screen, self.panel_font, self)
        # print(f"Ejercicio {self.exercise_num_str} cargado.") # Descomenta si quieres confirmación

    def load_exercise_data(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            for ex_num_key in data: 
                if isinstance(data[ex_num_key], list): 
                    for ac_data in data[ex_num_key]:
                        ac_data.setdefault('_is_authorized_early', False)
                        ac_data.setdefault('_processed_and_killed', False)
                        ac_data.setdefault('_authorization_time', 0.0) 
            return data
        except FileNotFoundError:
            print(f"Error: El archivo de configuración de ejercicios '{file_path}' no fue encontrado.")
            return {} 
        except json.JSONDecodeError:
            print(f"Error: El archivo '{file_path}' contiene JSON inválido.")
            return {}

    def display_time(self):
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_text_content = f"Tiempo 00:{minutes:02d}:{seconds:02d}"
        time_text = self.font.render(time_text_content, True, (0, 255, 0))
        self.screen.blit(time_text, (10, 10))
    
    def handle_collision_visualization(self):
        active_sprites = list(self.all_sprites)
        detected_conflicts = check_separations(active_sprites) 
        for conflict in detected_conflicts:
            sprite1 = conflict['sprite1']
            sprite2 = conflict['sprite2']
            severity = conflict['severity']
            color = (255, 0, 0) if severity == "critical" else (255, 255, 0)
            pygame.draw.aaline(self.screen, color, sprite1.rect.center, sprite2.rect.center, 2)
    
    def request_early_departure(self, aircraft_label_to_launch):
        if self.exercise_num_str in self.aircraft_creation_data:
            for acft_data_entry in self.aircraft_creation_data[self.exercise_num_str]:
                if acft_data_entry['label'] == aircraft_label_to_launch:
                    if not acft_data_entry.get('_processed_and_killed', False) and \
                    not acft_data_entry.get('_is_authorized_early', False):

                        current_time = self.elapsed_time
                        actual_takeoff_time = current_time + TAXIING_DURATION 

                        print(f"Game: Autorizando {aircraft_label_to_launch}. Rodaje inicia en t={current_time:.2f}, despegue programado para t={actual_takeoff_time:.2f}")

                        acft_data_entry['_is_authorized_early'] = True 
                        acft_data_entry['_authorization_time'] = current_time 
                        acft_data_entry['time'] = actual_takeoff_time # ESTA ES LA LÍNEA CRÍTICA

                    elif acft_data_entry.get('_is_authorized_early', False):
                        print(f"Game: {aircraft_label_to_launch} ya fue autorizado previamente.")
                    else: 
                        print(f"Game: {aircraft_label_to_launch} no pudo ser autorizado (ya procesado).")
                    break
   
    def run(self):
        start_time = time.time()
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.elapsed_time = time.time() - start_time
            
            self.aircraft_models = [model for model in self.aircraft_models if model.alive]
            self.label_views = [lv for lv in self.label_views if lv.aircraft_model.alive]

            mouse_pos_tuple = pygame.mouse.get_pos()
            mouse_buttons_pressed = pygame.mouse.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False; break 
                
                label_drag_consumed_event = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for lv in self.label_views:
                        if lv.aircraft_model.alive and lv.handle_input_for_drag(event, mouse_pos_tuple, mouse_buttons_pressed):
                            label_drag_consumed_event = True; break
                elif event.type == pygame.MOUSEMOTION:
                    for lv in self.label_views:
                        if lv.dragging_label and lv.handle_input_for_drag(event, mouse_pos_tuple, mouse_buttons_pressed):
                            label_drag_consumed_event = True; break
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for lv in self.label_views:
                        if lv.dragging_label and lv.handle_input_for_drag(event, mouse_pos_tuple, mouse_buttons_pressed):
                            label_drag_consumed_event = True; break
                if label_drag_consumed_event and (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP) :
                    continue

                panel_consumed_click = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                     if mouse_pos_tuple[0] >= SCREEN_WIDTH: 
                        panel_consumed_click = self.side_panel.handle_panel_input(event, mouse_pos_tuple)
                if panel_consumed_click: continue
                
                if event.type == pygame.KEYDOWN:
                    if self.ui_manager.level_window_active: 
                        enter_pressed = self.ui_manager.handle_level_input_keypress(event)
                        if enter_pressed:
                            entered_level = self.ui_manager.hide_level_input()
                            if self.selected_aircraft_model:
                                self.selected_aircraft_model.set_continue_descent_climb_flag(
                                    self.ui_manager.is_continue_descent
                                )
                                self.selected_aircraft_model.set_desired_altitude(entered_level)
                            self.selected_aircraft_model = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3: 
                        self.ui_manager.hide_menu() 
                        self.ui_manager.hide_level_input() 
                        newly_selected_model = None
                        for label_view in self.label_views:
                            if label_view.is_clicked(mouse_pos_tuple) and label_view.aircraft_model.alive:
                                newly_selected_model = label_view.aircraft_model; break
                        if not newly_selected_model:
                            for sprite_candidate in self.all_sprites:
                                if sprite_candidate.rect.collidepoint(mouse_pos_tuple) and sprite_candidate.model.alive:
                                    newly_selected_model = sprite_candidate.model; break
                        self.selected_aircraft_model = newly_selected_model
                        if self.selected_aircraft_model:
                            self.ui_manager.display_menu(mouse_pos_tuple, self.selected_aircraft_model.route_type)
                    elif event.button == 1: 
                        if self.ui_manager.show_menu: 
                            action = self.ui_manager.process_menu_click(mouse_pos_tuple) 
                            if action:
                                self.ui_manager.hide_menu() 
                                if action == "close_menu": self.selected_aircraft_model = None
                                elif self.selected_aircraft_model:
                                    if action == "Join Holding Pattern": self.selected_aircraft_model.set_pending_holding(True)
                                    elif action == "Finish Holding Pattern": self.selected_aircraft_model.set_finish_holding(True) 
                                    elif action in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to"]:
                                        self.ui_manager.display_level_input(mouse_pos_tuple) 
                                    elif action == "disregard": self.selected_aircraft_model = None 
                                    if action not in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to"]:
                                        self.selected_aircraft_model = None
            if not self.running: break
            
            self.side_panel.update(self.aircraft_models, self.aircraft_creation_data, self.elapsed_time)

            if self.exercise_num_str in self.aircraft_creation_data:
                entries_to_create_this_frame = [] 
                for acft_data in self.aircraft_creation_data[self.exercise_num_str]:
                    if not acft_data.get('_processed_and_killed', False) and self.elapsed_time >= acft_data['time']:
                        entries_to_create_this_frame.append(acft_data)
                
                for acft_data in entries_to_create_this_frame:
                    if acft_data.get('_processed_and_killed', False): continue

                    route_name = acft_data['name']
                    if route_name in self.routes_config:
                        route_info = self.routes_config[route_name]
                        model = AircraftModel(
                            route_name=route_name, initial_speed=acft_data['speed'],
                            label=acft_data['label'], acft_type=acft_data['acft_type'],
                            initial_altitude=route_info['altitude'],
                            desired_altitude_init= 6000 if route_info["type"] == "star" else 24000,
                            initial_pos=route_info["pixel_points"][0],
                            route_type_val=route_info["type"], routes_data=self.routes_config
                        )
                        self.aircraft_models.append(model)
                        sprite_color = (0, 200, 0) if route_info["type"] == "star" else (200, 200, 0)
                        sprite = AircraftSprite(model, sprite_color, self.screen)
                        self.all_sprites.add(sprite)
                        label_view = AircraftLabelView(model, self.font, self.screen)
                        self.label_views.append(label_view)
                        acft_data['_processed_and_killed'] = True 
                        print(f"Game: Aeronave {acft_data['label']} CREADA y marcada _processed_and_killed=True en t={self.elapsed_time:.2f} (programada para t={acft_data['time']:.2f}).")
                    else:
                        print(f"Advertencia: Ruta '{route_name}' no encontrada para {acft_data['label']}.")
                        acft_data['_processed_and_killed'] = True 

            for model in self.aircraft_models:
                model.update(dt)
            self.all_sprites.update()
            
            self.screen.fill((0, 0, 0))
            for route_name, route_data in self.routes_config.items():
                route_label = self.font.render(f"{route_name} ", True, (0, 255, 0))
                if route_data["type"] == "star" and route_name != "DIMIL_star":
                    self.screen.blit(route_label, route_data["pixel_points"][0] )
                if route_data["type"] == "sid":
                    self.screen.blit(route_label, route_data["pixel_points"][-1] )
                for i in range(len(route_data["pixel_points"]) - 1):
                    pygame.draw.aaline(self.screen, route_data["color"], route_data["pixel_points"][i], route_data["pixel_points"][i + 1], 1)

            self.all_sprites.draw(self.screen)
            for label_view in self.label_views:
                label_view.draw()

            self.ui_manager.draw() 
            self.side_panel.draw() 
            self.display_time()
            self.handle_collision_visualization()
            
            pygame.display.update()
        pygame.quit()

if __name__ == '__main__':
    radar_game = Game()
    radar_game.exercise_num_str = "5" 
    radar_game.aircraft_creation_data = radar_game.load_exercise_data('data/exercises_config.json') 
    radar_game.run()
