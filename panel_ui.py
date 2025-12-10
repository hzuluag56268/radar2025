"""
Side panel UI for flight strips (arrival/departure information).

This module provides:
- SidePanel: Main panel container that displays flight strips
- FlightStripView: Individual flight strip showing aircraft information

Flight strips show scheduled aircraft with their status:
- Arrivals (STAR): Time until arrival
- Departures (SID): Time until departure, taxiing status, early departure authorization

The panel is divided into two sections:
- Top half: Arrival strips
- Bottom half: Departure strips
"""

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH

# --- Colors and configurations ---
TEXT_COLOR = (0, 255, 0)  # Green text
PANEL_BG_COLOR = (10, 20, 30)  # Dark blue-gray background
STRIP_BG_COLOR = (20, 40, 55)  # Slightly lighter for strips
STRIP_BORDER_COLOR = (40, 70, 100)  # Border color
SEPARATOR_COLOR = (0, 100, 0)  # Green separator line
TAXIING_TEXT_COLOR = (255, 255, 0)  # Yellow for taxiing status
LINE_COLOR = (60, 90, 130)  # Light blue for grid lines
ERROR_TEXT_COLOR = (255, 50, 50)  # Red for errors

# Strip dimensions and spacing
STRIP_HEIGHT = 80  # Height of each flight strip
STRIP_PADDING_VERTICAL = 5  # Vertical spacing between strips
STRIP_PADDING_HORIZONTAL = 5  # Horizontal padding inside panel
TEXT_PADDING_X = 5  # Horizontal padding for text
TEXT_PADDING_Y = 3  # Vertical padding for text (currently unused)


class FlightStripView:
    """
    Represents a single flight strip (arrival or departure information card).
    
    Each strip displays:
    - Callsign (aircraft label)
    - Aircraft type
    - Speed
    - Route name
    - Status (time until event, taxiing status, etc.)
    
    Strips can be clicked to authorize early departure (for SID aircraft).
    """
    
    def __init__(self, data, strip_type, font, strip_width):
        """
        Initialize flight strip view.
        
        Args:
            data: Dictionary with aircraft data (from exercises_config.json)
            strip_type: "star" (arrival) or "sid" (departure)
            font: Pygame font for text rendering
            strip_width: Width of the strip (panel width minus padding)
        """
        self.data = data  # Aircraft data dictionary
        self.strip_type = strip_type.lower() if isinstance(strip_type, str) else ""
        self.font = font
        self.strip_width = strip_width
        
        # Strip rectangle (position set in SidePanel.draw())
        self.rect = pygame.Rect(0, 0, self.strip_width - 2 * STRIP_PADDING_HORIZONTAL, STRIP_HEIGHT)

    def _render_text_in_cell(self, surface, text, cell_rect, text_color=TEXT_COLOR, center_align=False):
        """
        Render text within a cell rectangle.
        
        Handles text clipping if text is too wide for the cell.
        
        Args:
            surface: Pygame surface to draw on
            text: Text string to render
            cell_rect: Rectangle defining cell bounds
            text_color: RGB color tuple for text
            center_align: If True, center text; otherwise left-align
        """
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect()
        
        if center_align:
            text_rect.center = cell_rect.center
        else:
            text_rect.left = cell_rect.left + TEXT_PADDING_X
            text_rect.centery = cell_rect.centery
        
        # Clip text if too wide
        if text_rect.width > cell_rect.width - (2 * TEXT_PADDING_X):
            area_to_blit = pygame.Rect(0, 0, cell_rect.width - (2 * TEXT_PADDING_X), text_rect.height)
            surface.blit(text_surface, text_rect.topleft, area=area_to_blit)
        else:
            surface.blit(text_surface, text_rect)

    def draw(self, surface, elapsed_time=0):
        """
        Draw the flight strip.
        
        Args:
            surface: Pygame surface to draw on
            elapsed_time: Current simulation time (for calculating time until events)
        """
        # Draw strip background and border
        pygame.draw.rect(surface, STRIP_BG_COLOR, self.rect)
        pygame.draw.rect(surface, STRIP_BORDER_COLOR, self.rect, 1)
        
        # Draw detailed content
        self._draw_detailed_format(surface, elapsed_time)

    def _draw_detailed_format(self, surface, elapsed_time):
        """
        Draw the detailed flight strip layout with all information.
        
        Layout:
        - Column 1 (60% width):
          - Row 1: Callsign
          - Row 2: Aircraft type (left) | Speed (right)
        - Column 2 (40% width):
          - Row 1: Status (time until event, taxiing, etc.)
          - Row 2: Route name
        
        Args:
            surface: Pygame surface to draw on
            elapsed_time: Current simulation time
        """
        # Get data from aircraft entry
        callsign = self.data.get('label', 'N/A')
        acft_type = self.data.get('acft_type', 'N/A')
        speed = f"{self.data.get('speed', 'N/A')}kts"
        route_name_display = self.data.get('name', 'N/A')
        
        # --- Calculate cell geometry ---
        # Column widths
        col1_width_ratio = 0.60  # Column 1 is 60% of strip width
        col1_width = int(self.rect.width * col1_width_ratio)
        col2_width = self.rect.width - col1_width

        # Column 1: Two rows
        c1_base_rect = pygame.Rect(self.rect.left, self.rect.top, col1_width, self.rect.height)
        c1_row_height = self.rect.height // 2  # Each row is half the height

        c1_r1_rect = pygame.Rect(c1_base_rect.left, c1_base_rect.top, c1_base_rect.width, c1_row_height)
        c1_r2_rect = pygame.Rect(c1_base_rect.left, c1_base_rect.top + c1_row_height,
                                 c1_base_rect.width, self.rect.height - c1_row_height)
        
        # Subdivide Column 1, Row 2 (for type and speed)
        c1_r2_subcol_width = c1_r2_rect.width // 2
        c1_r2_left_rect = pygame.Rect(c1_r2_rect.left, c1_r2_rect.top, c1_r2_subcol_width, c1_r2_rect.height)
        c1_r2_right_rect = pygame.Rect(c1_r2_rect.left + c1_r2_subcol_width, c1_r2_rect.top,
                                       c1_r2_rect.width - c1_r2_subcol_width, c1_r2_rect.height)

        # Column 2: Two rows
        c2_base_rect = pygame.Rect(self.rect.left + col1_width, self.rect.top, col2_width, self.rect.height)
        c2_row_height = self.rect.height // 2
        c2_r1_rect = pygame.Rect(c2_base_rect.left, c2_base_rect.top, c2_base_rect.width, c2_row_height)
        c2_r2_rect = pygame.Rect(c2_base_rect.left, c2_base_rect.top + c2_row_height,
                                 c2_base_rect.width, self.rect.height - c2_row_height)

        # --- Draw grid lines ---
        # Vertical line between columns
        pygame.draw.line(surface, LINE_COLOR, (c1_base_rect.right, self.rect.top),
                        (c1_base_rect.right, self.rect.bottom), 1)
        
        # Horizontal line in Column 1 (between rows)
        pygame.draw.line(surface, LINE_COLOR, (c1_base_rect.left, c1_r1_rect.bottom),
                        (c1_base_rect.right, c1_r1_rect.bottom), 1)
        
        # Vertical line in Column 1, Row 2 (between type and speed)
        pygame.draw.line(surface, LINE_COLOR, (c1_r2_left_rect.right, c1_r2_rect.top),
                        (c1_r2_left_rect.right, c1_r2_rect.bottom), 1)
        
        # Horizontal line in Column 2 (between rows)
        pygame.draw.line(surface, LINE_COLOR, (c2_base_rect.left, c2_r1_rect.bottom),
                        (c2_base_rect.right, c2_r1_rect.bottom), 1)

        # --- Calculate status text and color ---
        status_line = "ERR: NO STATE"
        status_text_color = ERROR_TEXT_COLOR
        
        event_time = self.data.get('time', float('inf'))  # Scheduled time
        is_authorized = self.data.get('_is_authorized_early', False)  # Early departure authorized

        if self.strip_type == "sid":  # Departure
            if is_authorized:
                # Aircraft is taxiing (authorized for early departure)
                status_text_color = TAXIING_TEXT_COLOR  # Yellow
                if elapsed_time < event_time:
                    # Still taxiing - show time remaining
                    time_to_takeoff = event_time - elapsed_time
                    minutes = int(time_to_takeoff) // 60
                    seconds = int(time_to_takeoff) % 60
                    status_line = f"RODANDO {minutes:02d}:{seconds:02d}"
                else:
                    # Ready for departure
                    status_line = "LISTO DESP."
            else:
                # Not authorized yet - show time until scheduled departure
                status_text_color = TEXT_COLOR
                time_to_scheduled_departure = event_time - elapsed_time
                if time_to_scheduled_departure > 0:
                    minutes = int(time_to_scheduled_departure) // 60
                    seconds = int(time_to_scheduled_departure) % 60
                    status_line = f"Sale en: {minutes:02d}:{seconds:02d}"
                else:
                    status_line = "PROGRAMADO"
        
        elif self.strip_type == "star":  # Arrival
            status_text_color = TEXT_COLOR
            time_to_arrival_event = event_time - elapsed_time
            if time_to_arrival_event > 0:
                # Show time until arrival
                minutes = int(time_to_arrival_event) // 60
                seconds = int(time_to_arrival_event) % 60
                status_line = f"Llega en: {minutes:02d}:{seconds:02d}"
            else:
                # Ready for arrival
                status_line = "LISTO LLEG."
        
        # --- Render text in cells ---
        self._render_text_in_cell(surface, callsign, c1_r1_rect)
        self._render_text_in_cell(surface, acft_type, c1_r2_left_rect)
        self._render_text_in_cell(surface, speed, c1_r2_right_rect)
        
        self._render_text_in_cell(surface, status_line, c2_r1_rect, text_color=status_text_color, center_align=True)
        self._render_text_in_cell(surface, route_name_display, c2_r2_rect, center_align=True)

    def is_clicked(self, pos):
        """
        Check if strip was clicked.
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            True if position is within strip rectangle
        """
        return self.rect.collidepoint(pos)

    def handle_click(self, game_ref):
        """
        Handle click on this strip.
        
        For SID (departure) strips, clicking authorizes early departure.
        
        Args:
            game_ref: Reference to Game instance (for calling request_early_departure)
        """
        if self.strip_type == "sid":  # Only departures can be authorized
            if not self.data.get('_is_authorized_early', False):  # Not already authorized
                game_ref.request_early_departure(self.data['label'])


class SidePanel:
    """
    Side panel container for flight strips.
    
    The panel is divided into two sections:
    - Top half: Arrival strips (STAR aircraft)
    - Bottom half: Departure strips (SID aircraft)
    
    Strips are automatically updated based on current time and aircraft schedule.
    Only aircraft that haven't been created yet (or are taxiing) are shown.
    """
    
    def __init__(self, screen, font, game_ref):
        """
        Initialize side panel.
        
        Args:
            screen: Pygame surface for drawing
            font: Font for strip text
            game_ref: Reference to Game instance (for accessing data and methods)
        """
        self.screen = screen
        self.font = font
        self.game_ref = game_ref  # Reference to Game for data access
        
        # Panel position and size
        self.panel_x = SCREEN_WIDTH  # Panel starts at right edge of main screen
        self.panel_y = 0
        self.panel_width = PANEL_WIDTH
        self.panel_height = SCREEN_HEIGHT
        
        # Define two sections
        self.arrivals_rect = pygame.Rect(self.panel_x, self.panel_y,
                                         self.panel_width, self.panel_height / 2)
        self.departures_rect = pygame.Rect(self.panel_x, self.panel_y + self.panel_height / 2,
                                          self.panel_width, self.panel_height / 2)
        
        # Lists of strips (updated each frame)
        self.arrival_strips = []
        self.departure_strips = []

    def update(self, active_aircraft_models, full_aircraft_creation_data, elapsed_time):
        """
        Update flight strips based on current time and aircraft schedule.
        
        Creates new strip views for aircraft that:
        - Haven't been created yet (scheduled time hasn't arrived)
        - Are taxiing (authorized for early departure, within 1 second of takeoff)
        
        Args:
            active_aircraft_models: List of currently active AircraftModel instances
            full_aircraft_creation_data: Full aircraft schedule from exercises_config.json
            elapsed_time: Current simulation time
        """
        # Clear existing strips
        self.arrival_strips.clear()
        self.departure_strips.clear()

        # Process aircraft from current exercise
        if self.game_ref.exercise_num_str in full_aircraft_creation_data:
            for ac_data in full_aircraft_creation_data[self.game_ref.exercise_num_str]:
                # Skip aircraft that have already been created
                if ac_data.get('_processed_and_killed', False):
                    continue

                # Get route information
                route_name = ac_data.get('name')
                if not route_name or route_name not in self.game_ref.routes_config:
                    continue

                route_type_from_config = self.game_ref.routes_config[route_name].get('type')
                if not route_type_from_config:
                    continue
                
                route_type = route_type_from_config.lower()
                event_time = ac_data.get('time', float('inf'))
                show_in_panel = False

                # Determine if this aircraft should be shown in panel
                if route_type == "star":  # Arrival
                    # Show if scheduled time hasn't arrived yet
                    if elapsed_time < event_time:
                        show_in_panel = True
                elif route_type == "sid":  # Departure
                    # Show if scheduled time hasn't arrived, or if taxiing (within 1 second of takeoff)
                    if elapsed_time < event_time:
                        show_in_panel = True
                    elif ac_data.get('_is_authorized_early', False) and abs(elapsed_time - event_time) < 1.0:
                        show_in_panel = True
                
                # Create strip if should be shown
                if show_in_panel:
                    strip = FlightStripView(ac_data, route_type, self.font, self.panel_width)
                    if route_type == "star":
                        self.arrival_strips.append(strip)
                    elif route_type == "sid":
                        self.departure_strips.append(strip)

    def draw(self):
        """
        Draw the side panel with all flight strips.
        
        Draws:
        - Panel background
        - Separator line between arrivals and departures
        - All arrival strips (top half)
        - All departure strips (bottom half)
        """
        # Draw panel background
        panel_main_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_main_rect)
        
        # Draw separator line between arrivals and departures
        divider_y = self.arrivals_rect.bottom
        pygame.draw.line(self.screen, SEPARATOR_COLOR,
                        (self.panel_x, divider_y),
                        (self.panel_x + self.panel_width, divider_y), 2)

        # Draw arrival strips (top half)
        current_y = self.arrivals_rect.top + STRIP_PADDING_VERTICAL
        for strip in self.arrival_strips:
            # Stop if we've run out of space
            if current_y + STRIP_HEIGHT > self.arrivals_rect.bottom:
                break
            # Position strip
            strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
            # Draw strip
            strip.draw(self.screen, self.game_ref.elapsed_time)
            # Move to next position
            current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL

        # Draw departure strips (bottom half)
        current_y = self.departures_rect.top + STRIP_PADDING_VERTICAL
        for strip in self.departure_strips:
            # Stop if we've run out of space
            if current_y + STRIP_HEIGHT > self.departures_rect.bottom:
                break
            # Position strip
            strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
            # Draw strip
            strip.draw(self.screen, self.game_ref.elapsed_time)
            # Move to next position
            current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL

    def handle_panel_input(self, event, mouse_pos):
        """
        Handle mouse clicks in the panel area.
        
        Checks if a departure strip was clicked and handles early departure authorization.
        
        Args:
            event: Pygame event object
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            # Check all departure strips
            for strip in self.departure_strips:
                if strip.is_clicked(mouse_pos):
                    if strip.strip_type == "sid":  # Only departures can be clicked
                        strip.handle_click(self.game_ref)
                        return True  # Event handled
        return False  # Event not handled
