# radar.py
"""
Main game controller and entry point for the radar simulation.

This module contains the Game class which orchestrates the entire simulation:
- Manages the game loop (60 FPS)
- Handles user input (mouse, keyboard)
- Creates aircraft when scheduled
- Updates all models and views each frame
- Renders everything to the screen
- Coordinates between models, views, UI, and panel components

Architecture: This follows an MVC pattern where:
- Models (models.py): Aircraft state and logic
- Views (views.py, ui.py, panel_ui.py): Visual representation
- Controller (this file): Orchestrates everything
"""

import pygame
import time
import json

from settings import *
from util_funct import *
from views import AircraftSprite, AircraftLabelView 
from models import AircraftModel
from ui import ui
from other_funct import * 
from panel_ui import SidePanel 

pygame.init()

# Duration for aircraft to taxi before takeoff when early departure is authorized (3 minutes)
TAXIING_DURATION = 180


class Game:
    """
    Main game controller class that manages the entire radar simulation.
    
    Responsibilities:
    - Initialize pygame and create game window
    - Load exercise configuration from JSON
    - Manage game loop at 60 FPS
    - Handle all user input events
    - Create aircraft when scheduled time arrives
    - Update all models and views each frame
    - Render all components to screen
    - Coordinate interactions between components
    """
    
    def __init__(self):
        """Initialize the game: set up pygame, load data, create UI components."""
        print('ejercicio 0') 
        
        # Initialize pygame display (main screen + side panel)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Radar Simulation")
        self.clock = pygame.time.Clock()  # For maintaining 60 FPS
        self.font = pygame.font.Font(None, 24)  # Main font for labels
        self.panel_font = pygame.font.Font(None, 18)  # Smaller font for panel
        self.running = True  # Game loop flag
        
        # Time tracking
        self.elapsed_time = 0.0  # Real-time clock since simulation start
        
        # UI components
        self.ui_manager = ui()  # Context menu handler
        self.level_str = ""  # Currently unused
        self.exercise_num_str = "1"  # Current exercise number (loaded from JSON)
        
        # Route and aircraft data
        self.routes_config = ROUTES  # All route definitions from settings.py
        self.aircraft_creation_data = self.load_exercise_data('data/exercises_config.json')  # Aircraft schedule
        self.selected_aircraft_model = None  # Currently selected aircraft (for commands)
        self.label_views = []  # List of label views for all aircraft
        
        # Sprite and model management
        self.all_sprites = pygame.sprite.Group()  # Pygame sprite group for efficient rendering
        self.aircraft_models = []  # List of all active AircraftModel instances
        
        # Side panel for flight strips
        self.side_panel = SidePanel(self.screen, self.panel_font, self)

    def load_exercise_data(self, file_path):
        """
        Load aircraft schedule data from JSON file.
        
        Args:
            file_path: Path to exercises_config.json file
            
        Returns:
            Dictionary with exercise numbers as keys and lists of aircraft data as values.
            Each aircraft entry gets internal flags added:
            - _is_authorized_early: True if early departure authorized
            - _processed_and_killed: True if aircraft already created
            - _authorization_time: Time when early departure was authorized
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Add internal tracking flags to each aircraft entry
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
        """Display the current simulation time in the top-left corner of the screen."""
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_text_content = f"Tiempo 00:{minutes:02d}:{seconds:02d}"
        time_text = self.font.render(time_text_content, True, (0, 255, 0))
        self.screen.blit(time_text, (10, 10))
    
    def handle_collision_visualization(self):
        """
        Detect and visualize conflicts between aircraft.
        
        Checks separation between all active aircraft:
        - Vertical separation: Must be >= 1000 ft
        - Horizontal separation: Must be >= 10 nautical miles
        
        Draws colored lines between conflicting aircraft:
        - Red: Critical conflict (< 5 NM separation)
        - Yellow: Warning conflict (5-10 NM separation)
        """
        active_sprites = list(self.all_sprites)
        detected_conflicts = check_separations(active_sprites) 
        
        # Draw conflict lines
        for conflict in detected_conflicts:
            sprite1 = conflict['sprite1']
            sprite2 = conflict['sprite2']
            severity = conflict['severity']
            # Red for critical, yellow for warning
            color = (255, 0, 0) if severity == "critical" else (255, 255, 0)
            pygame.draw.aaline(self.screen, color, sprite1.rect.center, sprite2.rect.center, 2)
    
    def request_early_departure(self, aircraft_label_to_launch):
        """
        Authorize early departure for a SID aircraft.
        
        When a departure strip is clicked in the panel, this method:
        1. Finds the aircraft in the creation data
        2. Checks if it can be authorized (not already processed or authorized)
        3. Calculates new takeoff time: current_time + TAXIING_DURATION
        4. Updates the aircraft's scheduled time
        
        Args:
            aircraft_label_to_launch: The callsign/label of the aircraft to authorize
        """
        if self.exercise_num_str in self.aircraft_creation_data:
            for acft_data_entry in self.aircraft_creation_data[self.exercise_num_str]:
                if acft_data_entry['label'] == aircraft_label_to_launch:
                    # Check if aircraft can be authorized
                    if not acft_data_entry.get('_processed_and_killed', False) and \
                       not acft_data_entry.get('_is_authorized_early', False):

                        current_time = self.elapsed_time
                        # New takeoff time = current time + taxiing duration (3 minutes)
                        actual_takeoff_time = current_time + TAXIING_DURATION 

                        
                            
                        print(f"Game: Autorizando {aircraft_label_to_launch}. Rodaje inicia en t={current_time:.2f}, despegue programado para t={actual_takeoff_time:.2f}")

                        # Mark as authorized and update scheduled time
                        acft_data_entry['_is_authorized_early'] = True 
                        acft_data_entry['_authorization_time'] = current_time 
                        acft_data_entry['time'] = actual_takeoff_time  # CRITICAL: Update scheduled time
                        
                    elif acft_data_entry.get('_is_authorized_early', False):
                        print(f"Game: {aircraft_label_to_launch} ya fue autorizado previamente.")
                    else: 
                        print(f"Game: {aircraft_label_to_launch} no pudo ser autorizado (ya procesado).")
                    break
   
    def run(self):
        """
        Main game loop - runs at 60 FPS until user quits.
        
        Loop structure:
        1. Calculate delta time and elapsed time
        2. Clean up dead aircraft
        3. Process all input events (mouse, keyboard)
        4. Update side panel
        5. Create new aircraft if scheduled time arrived
        6. Update all aircraft models
        7. Update all sprites
        8. Render everything (routes, sprites, labels, UI, panel, time, conflicts)
        9. Update display
        """
        start_time = time.time()
        
        while self.running:
            # Calculate delta time (seconds since last frame) and elapsed time
            dt = self.clock.tick(60) / 1000.0  # Convert milliseconds to seconds
            self.elapsed_time = time.time() - start_time
            
            # Remove dead aircraft from lists (models marked alive=False)
            self.aircraft_models = [model for model in self.aircraft_models if model.alive]
            self.label_views = [lv for lv in self.label_views if lv.aircraft_model.alive]

            # Get current mouse state
            mouse_pos_tuple = pygame.mouse.get_pos()
            mouse_buttons_pressed = pygame.mouse.get_pressed()

            # Process all pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break 
                
                # Handle label dragging (left mouse button on labels)
                label_drag_consumed_event = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if any label was clicked for dragging
                    for lv in self.label_views:
                        if lv.aircraft_model.alive and lv.handle_input_for_drag(event, mouse_pos_tuple, mouse_buttons_pressed):
                            label_drag_consumed_event = True
                            break
                elif event.type == pygame.MOUSEMOTION:
                   
                    # Continue dragging if already dragging
                    for lv in self.label_views:
                        if lv.dragging_label and lv.handle_input_for_drag(event, mouse_pos_tuple, mouse_buttons_pressed):
                            label_drag_consumed_event = True
                            break
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    # Stop dragging
                    for lv in self.label_views:
                        if lv.dragging_label and lv.handle_input_for_drag(event, mouse_pos_tuple, mouse_buttons_pressed):
                            label_drag_consumed_event = True
                            break
                
                # If label drag consumed the event, skip other processing
                if label_drag_consumed_event and (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP):
                    continue

                # Handle panel clicks (side panel for flight strips)
                panel_consumed_click = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if click is in panel area (x >= SCREEN_WIDTH)
                    if mouse_pos_tuple[0] >= SCREEN_WIDTH: 
                        panel_consumed_click = self.side_panel.handle_panel_input(event, mouse_pos_tuple)
                if panel_consumed_click:
                    continue
                
                # Handle keyboard input (for altitude entry)
                if event.type == pygame.KEYDOWN:
                    if self.ui_manager.level_window_active: 
                        # User is entering altitude
                        enter_pressed = self.ui_manager.handle_level_input_keypress(event)
                        if enter_pressed:
                            # Get entered altitude and apply to selected aircraft
                            entered_level = self.ui_manager.hide_level_input()
                            if self.selected_aircraft_model:
                                # Set flag if this is a "continue" command
                                self.selected_aircraft_model.set_continue_descent_climb_flag(
                                    self.ui_manager.is_continue_descent
                                )
                                # Apply altitude change
                                self.selected_aircraft_model.set_desired_altitude(entered_level)
                            self.selected_aircraft_model = None
                            
                # Handle mouse clicks
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:  # Right-click: Select aircraft and show menu
                        # Hide any open menus
                        self.ui_manager.hide_menu() 
                        self.ui_manager.hide_level_input() 
                        
                        # Try to find clicked aircraft (check labels first, then sprites)
                        newly_selected_model = None
                        for label_view in self.label_views:
                            if label_view.is_clicked(mouse_pos_tuple) and label_view.aircraft_model.alive:
                                newly_selected_model = label_view.aircraft_model
                                break
                        
                        # If not found in labels, check sprites
                        if not newly_selected_model:
                            for sprite_candidate in self.all_sprites:
                                if sprite_candidate.rect.collidepoint(mouse_pos_tuple) and sprite_candidate.model.alive:
                                    newly_selected_model = sprite_candidate.model
                                    break
                        
                        # Show context menu if aircraft selected
                        self.selected_aircraft_model = newly_selected_model
                        if self.selected_aircraft_model:
                            self.ui_manager.display_menu(mouse_pos_tuple, self.selected_aircraft_model.route_type)
                            
                    elif event.button == 1:  # Left-click: Process menu selection
                        if self.ui_manager.show_menu: 
                            # Get selected menu action
                            action = self.ui_manager.process_menu_click(mouse_pos_tuple) 
                            if action:
                                self.ui_manager.hide_menu() 
                                
                                # Handle different menu actions
                                if action == "close_menu":
                                    self.selected_aircraft_model = None
                                elif self.selected_aircraft_model:
                                    # Holding pattern commands
                                    if action == "Join Holding Pattern":
                                        self.selected_aircraft_model.set_pending_holding(True)
                                    elif action == "Finish Holding Pattern":
                                        self.selected_aircraft_model.set_finish_holding(True) 
                                    # Altitude commands (show input window)
                                    elif action in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to"]:
                                        self.ui_manager.display_level_input(mouse_pos_tuple) 
                                    elif action == "disregard":
                                        self.selected_aircraft_model = None 
                                    
                                    # Clear selection for non-altitude commands
                                    if action not in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to"]:
                                        self.selected_aircraft_model = None
                                        
            # Exit loop if user quit
            if not self.running:
                break
            
            # Update side panel with current aircraft data
            self.side_panel.update(self.aircraft_models, self.aircraft_creation_data, self.elapsed_time)

            # Create new aircraft if scheduled time has arrived
            if self.exercise_num_str in self.aircraft_creation_data:
                # Find all aircraft that should be created this frame
                entries_to_create_this_frame = [] 
                for acft_data in self.aircraft_creation_data[self.exercise_num_str]:
                    if not acft_data.get('_processed_and_killed', False) and self.elapsed_time >= acft_data['time']:
                        entries_to_create_this_frame.append(acft_data)
                
                # Create aircraft for each scheduled entry
                for acft_data in entries_to_create_this_frame:
                    if acft_data.get('_processed_and_killed', False):
                        continue

                    route_name = acft_data['name']
                    if route_name in self.routes_config:
                        route_info = self.routes_config[route_name]
                        
                        # Create aircraft model
                        model = AircraftModel(
                            route_name=route_name,
                            initial_speed=acft_data['speed'],
                            label=acft_data['label'],
                            acft_type=acft_data['acft_type'],
                            initial_altitude=route_info['altitude'],
                            # STAR aircraft start at 6000ft, SID at 24000ft
                            desired_altitude_init=6000 if route_info["type"] == "star" else 24000,
                            initial_pos=route_info["pixel_points"][0],
                            route_type_val=route_info["type"],
                            routes_data=self.routes_config
                        )
                        self.aircraft_models.append(model)
                        
                        # Create sprite (visual representation)
                        # Green for STAR (arrivals), yellow for SID (departures)
                        sprite_color = (0, 200, 0) if route_info["type"] == "star" else (200, 200, 0)
                        sprite = AircraftSprite(model, sprite_color, self.screen)
                        self.all_sprites.add(sprite)
                        
                        # Create label view (information display)
                        label_view = AircraftLabelView(model, self.font, self.screen)
                        self.label_views.append(label_view)
                        
                        # Mark as processed so it won't be created again
                        acft_data['_processed_and_killed'] = True 
                        print(f"Game: Aeronave {acft_data['label']} CREADA y marcada _processed_and_killed=True en t={self.elapsed_time:.2f} (programada para t={acft_data['time']:.2f}).")
                    else:
                        print(f"Advertencia: Ruta '{route_name}' no encontrada para {acft_data['label']}.")
                        acft_data['_processed_and_killed'] = True 

            # Update all aircraft models (position, altitude, speed, etc.)
            for model in self.aircraft_models:
                model.update(dt)
            
            # Update all sprites (positions from models)
            self.all_sprites.update()
            
            # === RENDERING ===
            # Clear screen
            self.screen.fill((0, 0, 0))
            
            # Draw all routes
            for route_name, route_data in self.routes_config.items():
                route_label = self.font.render(f"{route_name} ", True, (0, 255, 0))
                # Draw route name at start for STAR, at end for SID
                if route_data["type"] == "star" and route_name != "DIMIL_star":
                    self.screen.blit(route_label, route_data["pixel_points"][0])
                if route_data["type"] == "sid":
                    self.screen.blit(route_label, route_data["pixel_points"][-1])
                
                # Draw route lines between waypoints
                for i in range(len(route_data["pixel_points"]) - 1):
                    pygame.draw.aaline(self.screen, route_data["color"], 
                                     route_data["pixel_points"][i], 
                                     route_data["pixel_points"][i + 1], 1)

            # Draw all aircraft sprites
            self.all_sprites.draw(self.screen)
            
            # Draw all aircraft labels
            for label_view in self.label_views:
                label_view.draw()

            # Draw UI elements (context menu, level input)
            self.ui_manager.draw() 
            
            # Draw side panel (flight strips)
            self.side_panel.draw() 
            
            # Draw time display
            self.display_time()
            
            # Draw conflict visualization
            self.handle_collision_visualization()
            
            # Update display
            pygame.display.update()
            
        pygame.quit()


if __name__ == '__main__':
    # Create game instance
    radar_game = Game()
    
    # Set exercise number (change this to test different scenarios)
    radar_game.exercise_num_str = "5" 
    
    # Reload exercise data (in case exercise number changed)
    radar_game.aircraft_creation_data = radar_game.load_exercise_data('data/exercises_config.json') 
    
    # Start game loop
    radar_game.run()
