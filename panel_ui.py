# panel_ui.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH # Importar dimensiones necesarias
# Se podrían añadir colores específicos para el panel en settings.py o definirlos aquí.

# --- Colors and configurations for the panel and strips ---
TEXT_COLOR = (0, 255, 0)  # Radar green
PANEL_BG_COLOR = (10, 20, 30) # Dark blue/grey for panel background
STRIP_BG_COLOR = (20, 40, 55) # Slightly lighter for strip background
STRIP_BORDER_COLOR = (40, 70, 100) # Border for the strip
SEPARATOR_COLOR = (0, 100, 0) # Dividing line

STRIP_HEIGHT = 95  # Height of each flight strip (adjust for 5 lines + padding)
STRIP_PADDING_VERTICAL = 5  # Vertical space between strips
STRIP_PADDING_HORIZONTAL = 5 # Horizontal space from panel edge to strip

LINE_SPACING = 16 # Space between lines of text within the strip (adjust based on font size)
TEXT_PADDING_X = 8 # Horizontal padding for text inside the strip
TEXT_PADDING_Y = 5 # Vertical padding for text inside the strip (top margin for first line)

class FlightStripView:
    """
    Manages the display of a single flight strip.
    """
    def __init__(self, data, strip_type, font, strip_width):
        """
        Initializes a flight strip view.
        Args:
            data: Can be an AircraftModel instance (for active aircraft)
                  or a dictionary from aircraft_creation_data (for pending SIDs).
            strip_type (str): "STAR" or "SID".
            font (pygame.font.Font): The font to use for rendering text.
            strip_width (int): The width of the flight strip.
        """
        self.data = data
        self.strip_type = strip_type
        self.font = font
        self.strip_width = strip_width
        # The actual rect (position and size) will be set by SidePanel before drawing.
        # Initialize with width and height; x, y will be updated.
        self.rect = pygame.Rect(0, 0, self.strip_width - 2 * STRIP_PADDING_HORIZONTAL, STRIP_HEIGHT)

        # Check if data is an active AircraftModel or a pending data dictionary
        self.is_active_model = hasattr(self.data, 'get_info_for_label') # AircraftModel has this method

    def draw(self, surface, elapsed_time=0): # Add elapsed_time for countdown
        """Draws the flight strip onto the given surface."""
        # Draw background and border for the strip
        pygame.draw.rect(surface, STRIP_BG_COLOR, self.rect)
        pygame.draw.rect(surface, STRIP_BORDER_COLOR, self.rect, 1)

        lines_to_render = []
        if self.is_active_model: # Active aircraft (AircraftModel)
            model_info = self.data.get_info_for_label()
            lines_to_render.append(f"{model_info['label']}")
            lines_to_render.append(f"{model_info['acft_type']}")
            
            alt_val = model_info['altitude']
            alt_text = f"FL{int(alt_val / 100):03d}"
            # Optional: Show desired altitude if different
            # desired_alt_val = self.data.desired_altitude # Assuming AircraftModel has desired_altitude
            # if int(alt_val) != int(desired_alt_val):
            #     direction = ">" if desired_alt_val < alt_val else "<"
            #     alt_text += f" {direction}FL{int(desired_alt_val / 100):03d}"
            lines_to_render.append(alt_text)
            lines_to_render.append(f"{int(model_info['current_speed'])}kts")
            lines_to_render.append(f"{self.data.route_name}") # Assuming AircraftModel has route_name
        else: # Pending SID (dictionary from aircraft_creation_data)
            lines_to_render.append(f"{self.data['label']}")
            lines_to_render.append(f"{self.data['acft_type']}")
            lines_to_render.append(f"Ruta: {self.data['name']}") # 'name' is the route_name in creation_data
            
            # Countdown for departure (Phase 2 refinement)
            time_to_departure = self.data['time'] - elapsed_time
            if self.data.get('_is_authorized_early', False) and not self.is_active_model:
                 lines_to_render.append("AUTORIZADO")
            elif time_to_departure > 0:
                minutes = int(time_to_departure) // 60
                seconds = int(time_to_departure) % 60
                lines_to_render.append(f"Sale en: {minutes:02d}:{seconds:02d}")
            else:
                lines_to_render.append("Listo Salida") # Or "Esperando"

            lines_to_render.append(f"Vel: {self.data['speed']}kts") # Initial speed

        # Render and blit each line of text
        current_y = self.rect.top + TEXT_PADDING_Y
        for i, line_text in enumerate(lines_to_render):
            if i >= 5: break # Limit to 5 lines
            text_surface = self.font.render(line_text, True, TEXT_COLOR)
            surface.blit(text_surface, (self.rect.left + TEXT_PADDING_X, current_y))
            current_y += LINE_SPACING

    def is_clicked(self, pos):
        """Checks if the given position (mouse click) is within this strip."""
        return self.rect.collidepoint(pos)

    def handle_click(self, game_ref):
        """
        Handles a click event on this strip.
        Relevant for pending SIDs to authorize early departure.
        """
        if not self.is_active_model and self.strip_type == "SID":
            # Check if it's not already authorized to prevent multiple calls
            if not self.data.get('_is_authorized_early', False):
                print(f"FlightStripView: SID '{self.data['label']}' clicked. Requesting early departure.")
                game_ref.request_early_departure(self.data['label'])
                self.data['_is_authorized_early'] = True # Mark it locally for immediate feedback if needed
            else:
                print(f"FlightStripView: SID '{self.data['label']}' was already authorized.")


class SidePanel:
    """
    Manages the side panel display, including arrival and departure flight strips.
    """
    def __init__(self, screen, font, game_ref):
        """
        Initializes the side panel.
        Args:
            screen (pygame.Surface): The main Pygame display surface.
            font (pygame.font.Font): The font to use for the strips.
            game_ref: Reference to the main Game instance.
        """
        self.screen = screen
        self.font = font
        self.game_ref = game_ref # To access elapsed_time, aircraft_creation_data, routes_config

        self.panel_x = SCREEN_WIDTH # Starts where the radar screen ends
        self.panel_y = 0
        self.panel_width = PANEL_WIDTH
        self.panel_height = SCREEN_HEIGHT

        # Define areas for arrivals (top half) and departures (bottom half)
        self.arrivals_rect = pygame.Rect(
            self.panel_x, self.panel_y,
            self.panel_width, self.panel_height / 2
        )
        self.departures_rect = pygame.Rect(
            self.panel_x, self.panel_y + self.panel_height / 2,
            self.panel_width, self.panel_height / 2
        )

        self.arrival_strips = []
        self.departure_strips = []

    def update(self, active_aircraft_models, pending_aircraft_creation_data, elapsed_time):
        """
        Updates the lists of arrival and departure strips based on current game state.
        Args:
            active_aircraft_models (list): List of currently active AircraftModel instances.
            pending_aircraft_creation_data (list): List of dicts for aircraft yet to be created.
            elapsed_time (float): Current game time in seconds.
        """
        self.arrival_strips.clear()
        self.departure_strips.clear()

        # Populate arrival strips (STARs that are active)
        for model in active_aircraft_models:
            if model.route_type == "star":
                strip = FlightStripView(model, "STAR", self.font, self.panel_width)
                self.arrival_strips.append(strip)

        # Populate departure strips
        active_sid_labels = set() # Keep track of SIDs already active to avoid duplication
        # First, add active SIDs
        for model in active_aircraft_models:
            if model.route_type == "sid":
                strip = FlightStripView(model, "SID", self.font, self.panel_width)
                self.departure_strips.append(strip)
                active_sid_labels.add(model.label)

        # Then, add pending SIDs from aircraft_creation_data
        # These are SIDs that haven't met their creation time yet OR have been authorized early
        if self.game_ref.exercise_num_str in pending_aircraft_creation_data:
            for ac_data in pending_aircraft_creation_data[self.game_ref.exercise_num_str]:
                route_name = ac_data['name']
                # Ensure it's a SID and not already active
                if route_name in self.game_ref.routes_config and \
                   self.game_ref.routes_config[route_name]['type'] == 'sid' and \
                   ac_data['label'] not in active_sid_labels:
                    
                    # Show if:
                    # 1. Its scheduled time is in the future OR
                    # 2. It was authorized early and hasn't been fully processed into an active model yet
                    #    (The `_processed_and_removed` flag handles cases where it's fully gone)
                   if not ac_data.get('_processed_and_removed', False) and \
                       (ac_data['time'] > elapsed_time or ac_data.get('_is_authorized_early', False)):
                        strip = FlightStripView(ac_data, "SID", self.font, self.panel_width)
                        self.departure_strips.append(strip)

    def draw(self):
        """Draws the entire side panel, including background, divider, and all strips."""
        # Draw panel background
        panel_main_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_main_rect)

        # Draw dividing line between arrivals and departures
        divider_y = self.arrivals_rect.bottom
        pygame.draw.line(self.screen, SEPARATOR_COLOR, 
                         (self.panel_x, divider_y), 
                         (self.panel_x + self.panel_width, divider_y), 2)

        # --- Draw Arrival Strips ---
        current_y = self.arrivals_rect.top + STRIP_PADDING_VERTICAL
        for strip in self.arrival_strips:
            # Check if the strip fits in the arrivals area
            if current_y + STRIP_HEIGHT > self.arrivals_rect.bottom:
                break 
            strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
            # strip.rect.width and strip.rect.height are set in FlightStripView.__init__
            strip.draw(self.screen) # elapsed_time not strictly needed for active STARs here
            current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL

        # --- Draw Departure Strips ---
        current_y = self.departures_rect.top + STRIP_PADDING_VERTICAL
        for strip in self.departure_strips:
            # Check if the strip fits in the departures area
            if current_y + STRIP_HEIGHT > self.departures_rect.bottom:
                break
            strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
            strip.draw(self.screen, self.game_ref.elapsed_time) # Pass elapsed_time for countdown
            current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL

    def handle_panel_input(self, event, mouse_pos):
        """
        Handles mouse input events for the panel, specifically clicks on strips.
        Returns:
            bool: True if the event was consumed by the panel, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
            # Check clicks only for departure strips for now (for authorization)
            for strip in self.departure_strips:
                if strip.is_clicked(mouse_pos):
                    # Only non-active SIDs are clickable for authorization
                    if not strip.is_active_model and strip.strip_type == "SID":
                        strip.handle_click(self.game_ref)
                        return True # Event consumed
        return False
