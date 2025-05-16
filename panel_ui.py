# panel_ui.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH 

# --- Colors and configurations ---
TEXT_COLOR = (0, 255, 0)
PANEL_BG_COLOR = (10, 20, 30) 
STRIP_BG_COLOR = (20, 40, 55) 
STRIP_BORDER_COLOR = (40, 70, 100) 
SEPARATOR_COLOR = (0, 100, 0) 
TAXIING_TEXT_COLOR = (255, 255, 0) 
LINE_COLOR = (60, 90, 130)
ERROR_TEXT_COLOR = (255, 50, 50)

STRIP_HEIGHT = 80 # Reducimos un poco la altura, ya que hay menos filas
STRIP_PADDING_VERTICAL = 5  
STRIP_PADDING_HORIZONTAL = 5 
TEXT_PADDING_X = 5 
TEXT_PADDING_Y = 3 

class FlightStripView:
    def __init__(self, data, strip_type, font, strip_width):
        self.data = data
        self.strip_type = strip_type.lower() if isinstance(strip_type, str) else ""
        self.font = font
        self.strip_width = strip_width
        # Ajustar la altura del rect de la ficha si STRIP_HEIGHT cambió
        self.rect = pygame.Rect(0, 0, self.strip_width - 2 * STRIP_PADDING_HORIZONTAL, STRIP_HEIGHT)

    def _render_text_in_cell(self, surface, text, cell_rect, text_color=TEXT_COLOR, center_align=False):
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect()
        if center_align:
            text_rect.center = cell_rect.center
        else:
            text_rect.left = cell_rect.left + TEXT_PADDING_X
            text_rect.centery = cell_rect.centery
        
        # Clipping básico
        if text_rect.width > cell_rect.width - (2 * TEXT_PADDING_X):
            area_to_blit = pygame.Rect(0,0, cell_rect.width - (2 * TEXT_PADDING_X), text_rect.height)
            surface.blit(text_surface, text_rect.topleft, area=area_to_blit)
        else:
            surface.blit(text_surface, text_rect)

    def draw(self, surface, elapsed_time=0):
        pygame.draw.rect(surface, STRIP_BG_COLOR, self.rect)
        pygame.draw.rect(surface, STRIP_BORDER_COLOR, self.rect, 1)
        self._draw_detailed_format(surface, elapsed_time)

    def _draw_detailed_format(self, surface, elapsed_time):
        callsign = self.data.get('label', 'N/A')
        acft_type = self.data.get('acft_type', 'N/A')
        speed = f"{self.data.get('speed', 'N/A')}kts" 
        route_name_display = self.data.get('name', 'N/A')
        
        # --- Geometría Modificada ---
        col1_width_ratio = 0.60 
        col1_width = int(self.rect.width * col1_width_ratio)
        col2_width = self.rect.width - col1_width

        # Columna 1 ahora tiene 2 filas
        c1_base_rect = pygame.Rect(self.rect.left, self.rect.top, col1_width, self.rect.height)
        c1_row_height = self.rect.height // 2 # Dos filas de igual altura

        c1_r1_rect = pygame.Rect(c1_base_rect.left, c1_base_rect.top, c1_base_rect.width, c1_row_height)
        # La Fila 2 de la Columna 1 ahora ocupa la mitad inferior
        c1_r2_rect = pygame.Rect(c1_base_rect.left, c1_base_rect.top + c1_row_height, c1_base_rect.width, self.rect.height - c1_row_height) 
        
        # Subdivisión de Columna 1, Fila 2 (para tipo y velocidad)
        c1_r2_subcol_width = c1_r2_rect.width // 2
        c1_r2_left_rect = pygame.Rect(c1_r2_rect.left, c1_r2_rect.top, c1_r2_subcol_width, c1_r2_rect.height)
        c1_r2_right_rect = pygame.Rect(c1_r2_rect.left + c1_r2_subcol_width, c1_r2_rect.top, c1_r2_rect.width - c1_r2_subcol_width, c1_r2_rect.height)

        # Columna 2 sigue teniendo 2 filas
        c2_base_rect = pygame.Rect(self.rect.left + col1_width, self.rect.top, col2_width, self.rect.height)
        c2_row_height = self.rect.height // 2
        c2_r1_rect = pygame.Rect(c2_base_rect.left, c2_base_rect.top, c2_base_rect.width, c2_row_height)
        c2_r2_rect = pygame.Rect(c2_base_rect.left, c2_base_rect.top + c2_row_height, c2_base_rect.width, self.rect.height - c2_row_height)

        # --- Dibujar líneas de separación Modificadas ---
        # Línea vertical principal (entre Columna 1 y Columna 2)
        pygame.draw.line(surface, LINE_COLOR, (c1_base_rect.right, self.rect.top), (c1_base_rect.right, self.rect.bottom), 1)
        
        # Línea horizontal en Columna 1 (solo una, dividiendo sus dos filas)
        pygame.draw.line(surface, LINE_COLOR, (c1_base_rect.left, c1_r1_rect.bottom), (c1_base_rect.right, c1_r1_rect.bottom), 1)
        
        # Línea vertical en Columna 1, Fila 2 (para dividir tipo y velocidad)
        pygame.draw.line(surface, LINE_COLOR, (c1_r2_left_rect.right, c1_r2_rect.top), (c1_r2_left_rect.right, c1_r2_rect.bottom), 1)
        
        # Línea horizontal en Columna 2 (dividiendo sus dos filas)
        pygame.draw.line(surface, LINE_COLOR, (c2_base_rect.left, c2_r1_rect.bottom), (c2_base_rect.right, c2_r1_rect.bottom), 1)

        # --- Lógica de Estado y Tiempo (sin cambios) ---
        status_line = "ERR: NO STATE" 
        status_text_color = ERROR_TEXT_COLOR 
        
        event_time = self.data.get('time', float('inf')) 
        is_authorized = self.data.get('_is_authorized_early', False)

        if self.strip_type == "sid": 
            if is_authorized: 
                status_text_color = TAXIING_TEXT_COLOR 
                if elapsed_time < event_time :
                    time_to_takeoff = event_time - elapsed_time
                    minutes = int(time_to_takeoff) // 60
                    seconds = int(time_to_takeoff) % 60
                    status_line = f"RODANDO {minutes:02d}:{seconds:02d}"
                else: 
                    status_line = "LISTO DESP." 
            else: 
                status_text_color = TEXT_COLOR
                time_to_scheduled_departure = event_time - elapsed_time
                if time_to_scheduled_departure > 0:
                    minutes = int(time_to_scheduled_departure) // 60
                    seconds = int(time_to_scheduled_departure) % 60
                    status_line = f"Sale en: {minutes:02d}:{seconds:02d}"
                else: 
                    status_line = "PROGRAMADO"
        
        elif self.strip_type == "star": 
            status_text_color = TEXT_COLOR 
            time_to_arrival_event = event_time - elapsed_time
            if time_to_arrival_event > 0:
                minutes = int(time_to_arrival_event) // 60
                seconds = int(time_to_arrival_event) % 60
                status_line = f"Llega en: {minutes:02d}:{seconds:02d}"
            else:
                status_line = "LISTO LLEG." 
        
        # --- Renderizar Texto en Celdas (sin "Cúcuta") ---
        # print(f"RENDERING: Label: {callsign}, Type: {self.strip_type}, EventTime: {event_time:.2f}, Elapsed: {elapsed_time:.2f}, Auth: {is_authorized}, Final Status: '{status_line}', Color: {status_text_color}") # Mantener para debug si es necesario
        
        self._render_text_in_cell(surface, callsign, c1_r1_rect)
        self._render_text_in_cell(surface, acft_type, c1_r2_left_rect)
        self._render_text_in_cell(surface, speed, c1_r2_right_rect)
        # No renderizar fixed_location_text (Cúcuta)
        
        self._render_text_in_cell(surface, status_line, c2_r1_rect, text_color=status_text_color, center_align=True)
        self._render_text_in_cell(surface, route_name_display, c2_r2_rect, center_align=True)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def handle_click(self, game_ref):
        if self.strip_type == "sid": 
            if not self.data.get('_is_authorized_early', False): 
                game_ref.request_early_departure(self.data['label'])

class SidePanel:
    # ... (El resto de la clase SidePanel sin cambios respecto a tu última versión) ...
    def __init__(self, screen, font, game_ref):
        self.screen = screen
        self.font = font
        self.game_ref = game_ref
        self.panel_x = SCREEN_WIDTH
        self.panel_y = 0
        self.panel_width = PANEL_WIDTH
        self.panel_height = SCREEN_HEIGHT
        self.arrivals_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height / 2)
        self.departures_rect = pygame.Rect(self.panel_x, self.panel_y + self.panel_height / 2, self.panel_width, self.panel_height / 2)
        self.arrival_strips = []
        self.departure_strips = []

    def update(self, active_aircraft_models, full_aircraft_creation_data, elapsed_time): 
        self.arrival_strips.clear()
        self.departure_strips.clear()

        if self.game_ref.exercise_num_str in full_aircraft_creation_data:
            for ac_data in full_aircraft_creation_data[self.game_ref.exercise_num_str]:
                if ac_data.get('_processed_and_killed', False):
                    continue 

                route_name = ac_data.get('name')
                if not route_name or route_name not in self.game_ref.routes_config:
                    continue 

                route_type_from_config = self.game_ref.routes_config[route_name].get('type')
                if not route_type_from_config: 
                    continue
                
                route_type = route_type_from_config.lower()
                
                event_time = ac_data.get('time', float('inf')) 
                show_in_panel = False

                if route_type == "star":
                    if elapsed_time < event_time:
                        show_in_panel = True
                elif route_type == "sid":
                    if elapsed_time < event_time: 
                        show_in_panel = True
                    elif ac_data.get('_is_authorized_early', False) and abs(elapsed_time - event_time) < 1.0: 
                        show_in_panel = True
                
                if show_in_panel:
                    strip = FlightStripView(ac_data, route_type, self.font, self.panel_width)
                    if route_type == "star":
                        self.arrival_strips.append(strip)
                    elif route_type == "sid":
                        self.departure_strips.append(strip)
    
    def draw(self):
        panel_main_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_main_rect)
        divider_y = self.arrivals_rect.bottom
        pygame.draw.line(self.screen, SEPARATOR_COLOR, (self.panel_x, divider_y), (self.panel_x + self.panel_width, divider_y), 2)

        current_y = self.arrivals_rect.top + STRIP_PADDING_VERTICAL
        for strip in self.arrival_strips: 
            if current_y + STRIP_HEIGHT > self.arrivals_rect.bottom: break 
            strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
            strip.draw(self.screen, self.game_ref.elapsed_time) 
            current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL

        current_y = self.departures_rect.top + STRIP_PADDING_VERTICAL
        for strip in self.departure_strips: 
            if current_y + STRIP_HEIGHT > self.departures_rect.bottom: break
            strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
            strip.draw(self.screen, self.game_ref.elapsed_time) 
            current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL

    def handle_panel_input(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for strip in self.departure_strips: 
                if strip.is_clicked(mouse_pos):
                    if strip.strip_type == "sid": 
                        strip.handle_click(self.game_ref)
                        return True 
        return False
