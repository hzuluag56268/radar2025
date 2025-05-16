# panel_ui.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH 

# --- Colors and configurations for the panel and strips ---
TEXT_COLOR = (0, 255, 0)
PANEL_BG_COLOR = (10, 20, 30) 
STRIP_BG_COLOR = (20, 40, 55) 
STRIP_BORDER_COLOR = (40, 70, 100) 
SEPARATOR_COLOR = (0, 100, 0) 
TAXIING_TEXT_COLOR = (255, 255, 0) # Solo para SIDs en rodaje
LINE_COLOR = (60, 90, 130)

STRIP_HEIGHT = 95  
STRIP_PADDING_VERTICAL = 5  
STRIP_PADDING_HORIZONTAL = 5 
TEXT_PADDING_X = 5 
TEXT_PADDING_Y = 3 

class FlightStripView:
    def __init__(self, data, strip_type, font, strip_width):
        self.data = data
        self.strip_type = strip_type 
        self.font = font
        self.strip_width = strip_width
        self.rect = pygame.Rect(0, 0, self.strip_width - 2 * STRIP_PADDING_HORIZONTAL, STRIP_HEIGHT)
        self.is_active_model = hasattr(self.data, 'get_info_for_label')

    def _render_text_in_cell(self, surface, text, cell_rect, text_color=TEXT_COLOR, center_align=False):
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect()
        if center_align:
            text_rect.center = cell_rect.center
        else:
            text_rect.left = cell_rect.left + TEXT_PADDING_X
            text_rect.centery = cell_rect.centery
        if text_rect.width > cell_rect.width - (2 * TEXT_PADDING_X):
            area_to_blit = pygame.Rect(0,0, cell_rect.width - (2 * TEXT_PADDING_X), text_rect.height)
            surface.blit(text_surface, text_rect.topleft, area=area_to_blit)
        else:
            surface.blit(text_surface, text_rect)

    def draw(self, surface, elapsed_time=0):
        pygame.draw.rect(surface, STRIP_BG_COLOR, self.rect)
        pygame.draw.rect(surface, STRIP_BORDER_COLOR, self.rect, 1)

        if not self.is_active_model: 
            # Todas las aeronaves pendientes (STARs y SIDs) usan el formato detallado
            self._draw_detailed_format(surface, elapsed_time)
        # else:
            # Los modelos activos ya no se pasan al SidePanel para dibujar,
            # así que este 'else' no debería ejecutarse para fichas del panel.
            # print(f"Advertencia: FlightStripView.draw() llamada para modelo activo {self.data.label}")


    def _draw_detailed_format(self, surface, elapsed_time):
        col1_width_ratio = 0.60 
        col1_width = int(self.rect.width * col1_width_ratio)
        col2_width = self.rect.width - col1_width
        # ... (definiciones de celdas c1_r1_rect, etc. como en la versión anterior) ...
        c1_base_rect = pygame.Rect(self.rect.left, self.rect.top, col1_width, self.rect.height)
        c1_row_height = self.rect.height // 3
        c1_r1_rect = pygame.Rect(c1_base_rect.left, c1_base_rect.top, c1_base_rect.width, c1_row_height)
        c1_r2_rect = pygame.Rect(c1_base_rect.left, c1_base_rect.top + c1_row_height, c1_base_rect.width, c1_row_height)
        c1_r3_rect = pygame.Rect(c1_base_rect.left, c1_base_rect.top + 2 * c1_row_height, c1_base_rect.width, self.rect.height - 2*c1_row_height)
        c1_r2_subcol_width = c1_r2_rect.width // 2
        c1_r2_left_rect = pygame.Rect(c1_r2_rect.left, c1_r2_rect.top, c1_r2_subcol_width, c1_r2_rect.height)
        c1_r2_right_rect = pygame.Rect(c1_r2_rect.left + c1_r2_subcol_width, c1_r2_rect.top, c1_r2_rect.width - c1_r2_subcol_width, c1_r2_rect.height)

        c2_base_rect = pygame.Rect(self.rect.left + col1_width, self.rect.top, col2_width, self.rect.height)
        c2_row_height = self.rect.height // 2
        c2_r1_rect = pygame.Rect(c2_base_rect.left, c2_base_rect.top, c2_base_rect.width, c2_row_height)
        c2_r2_rect = pygame.Rect(c2_base_rect.left, c2_base_rect.top + c2_row_height, c2_base_rect.width, self.rect.height - c2_row_height)

        pygame.draw.line(surface, LINE_COLOR, (c1_base_rect.right, self.rect.top), (c1_base_rect.right, self.rect.bottom), 1)
        pygame.draw.line(surface, LINE_COLOR, (c1_base_rect.left, c1_r1_rect.bottom), (c1_base_rect.right, c1_r1_rect.bottom), 1)
        pygame.draw.line(surface, LINE_COLOR, (c1_base_rect.left, c1_r2_rect.bottom), (c1_base_rect.right, c1_r2_rect.bottom), 1)
        pygame.draw.line(surface, LINE_COLOR, (c1_r2_left_rect.right, c1_r2_rect.top), (c1_r2_left_rect.right, c1_r2_rect.bottom), 1)
        pygame.draw.line(surface, LINE_COLOR, (c2_base_rect.left, c2_r1_rect.bottom), (c2_base_rect.right, c2_r1_rect.bottom), 1)

        callsign = self.data.get('label', 'N/A')
        acft_type = self.data.get('acft_type', 'N/A')
        speed = f"{self.data.get('speed', 'N/A')}kts" 
        fixed_location_text = "Cúcuta" 
        route_name_display = self.data.get('name', 'N/A')

        status_line = ""
        status_text_color = TEXT_COLOR 
        event_time = self.data.get('time', float('inf'))

        if self.strip_type == "SID":
            is_authorized = self.data.get('_is_authorized_early', False)
            status_text_color = TEXT_COLOR 
            if is_authorized:
                if elapsed_time < event_time :
                    status_text_color = TAXIING_TEXT_COLOR
                    time_to_takeoff = event_time - elapsed_time
                    minutes = int(time_to_takeoff) // 60
                    seconds = int(time_to_takeoff) % 60
                    status_line = f"RODANDO {minutes:02d}:{seconds:02d}"
                else: 
                    status_text_color = TAXIING_TEXT_COLOR 
                    status_line = "LISTO DESP." 
            else: 
                time_to_scheduled_departure = event_time - elapsed_time
                if time_to_scheduled_departure > 0:
                    minutes = int(time_to_scheduled_departure) // 60
                    seconds = int(time_to_scheduled_departure) % 60
                    status_line = f"Sale en: {minutes:02d}:{seconds:02d}"
                else: 
                    status_line = "PROGRAMADO"
        
        elif self.strip_type == "STAR":
            status_text_color = TEXT_COLOR 
            time_to_arrival_event = event_time - elapsed_time
            if time_to_arrival_event > 0:
                minutes = int(time_to_arrival_event) // 60
                seconds = int(time_to_arrival_event) % 60
                status_line = f"Llega en: {minutes:02d}:{seconds:02d}"
            else:
                status_line = "LISTO LLEG." 

        self._render_text_in_cell(surface, callsign, c1_r1_rect)
        self._render_text_in_cell(surface, acft_type, c1_r2_left_rect)
        self._render_text_in_cell(surface, speed, c1_r2_right_rect)
        self._render_text_in_cell(surface, fixed_location_text, c1_r3_rect)
        self._render_text_in_cell(surface, status_line, c2_r1_rect, text_color=status_text_color, center_align=True)
        self._render_text_in_cell(surface, route_name_display, c2_r2_rect, center_align=True)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def handle_click(self, game_ref):
        if not self.is_active_model and self.strip_type == "SID":
            if not self.data.get('_is_authorized_early', False): 
                game_ref.request_early_departure(self.data['label'])


class SidePanel:
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

        # No se usan active_aircraft_models para poblar el panel,
        # solo se usa full_aircraft_creation_data

        if self.game_ref.exercise_num_str in full_aircraft_creation_data:
            for ac_data in full_aircraft_creation_data[self.game_ref.exercise_num_str]:
                # Condición principal: Si ya fue procesada y "matada" (convertida a AircraftModel),
                # no debe aparecer en el SidePanel.
                if ac_data.get('_processed_and_killed', False):
                    continue 

                route_name = ac_data.get('name') # Usar .get() para evitar KeyError si 'name' falta
                if not route_name or route_name not in self.game_ref.routes_config:
                    # print(f"SidePanel Update: Ruta {route_name} no encontrada o inválida para {ac_data.get('label')}")
                    continue 

                route_type = self.game_ref.routes_config[route_name].get('type')
                if not route_type:
                    # print(f"SidePanel Update: Tipo de ruta no definido para {route_name}")
                    continue
                
                # 'event_time' es el tiempo de aparición (STARs) o despegue (SIDs)
                event_time = ac_data.get('time', float('inf')) 
                show_in_panel = False

                if route_type == "star":
                    # Mostrar STARs pendientes si su tiempo de evento es futuro
                    if elapsed_time < event_time:
                        show_in_panel = True
                elif route_type == "sid":
                    # Mostrar SIDs pendientes si:
                    # 1. Su tiempo de despegue (event_time, que incluye rodaje si está autorizado) es futuro, O
                    # 2. Está autorizado (_is_authorized_early es True) y aún no ha llegado su tiempo de despegue
                    #    (esto cubre el estado de RODANDO).
                    # La condición `elapsed_time < event_time` cubre ambos casos si `event_time` se actualiza correctamente
                    # en `request_early_departure`.
                    # La bandera `_is_authorized_early` se usa en FlightStripView para el *display*, no tanto para la *inclusión* aquí.
                    if elapsed_time < event_time: # Si el tiempo de despegue real aún no ha llegado
                        show_in_panel = True
                    elif ac_data.get('_is_authorized_early', False) and abs(elapsed_time - event_time) < 1.0 and not ac_data.get('_processed_and_killed', False):
                        # Caso límite: autorizado, tiempo casi cumplido, aún no procesado. Mostrar como "LISTO DESP."
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
                    if not strip.is_active_model and strip.strip_type == "SID":
                        strip.handle_click(self.game_ref)
                        return True 
            # No hay interactividad de clic para STARs en el panel por ahora
        return False
