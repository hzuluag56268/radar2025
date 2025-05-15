# panel_ui.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH 

# --- Colors and configurations for the panel and strips ---
TEXT_COLOR = (0, 255, 0)
PANEL_BG_COLOR = (10, 20, 30) 
STRIP_BG_COLOR = (20, 40, 55) 
STRIP_BORDER_COLOR = (40, 70, 100) 
SEPARATOR_COLOR = (0, 100, 0) 

STRIP_HEIGHT = 95  
STRIP_PADDING_VERTICAL = 5  
STRIP_PADDING_HORIZONTAL = 5 

LINE_SPACING = 16 
TEXT_PADDING_X = 8 
TEXT_PADDING_Y = 5 

class FlightStripView:
    def __init__(self, data, strip_type, font, strip_width):
        self.data = data
        self.strip_type = strip_type
        self.font = font
        self.strip_width = strip_width
        self.rect = pygame.Rect(0, 0, self.strip_width - 2 * STRIP_PADDING_HORIZONTAL, STRIP_HEIGHT)
        self.is_active_model = hasattr(self.data, 'get_info_for_label')

    def draw(self, surface, elapsed_time=0):
        pygame.draw.rect(surface, STRIP_BG_COLOR, self.rect)
        pygame.draw.rect(surface, STRIP_BORDER_COLOR, self.rect, 1)

        lines_to_render = []
        if self.is_active_model:
            model_info = self.data.get_info_for_label()
            lines_to_render.append(f"{model_info['label']}")
            lines_to_render.append(f"{model_info['acft_type']}")
            alt_val = model_info['altitude']
            alt_text = f"FL{int(alt_val / 100):03d}"
            lines_to_render.append(alt_text)
            lines_to_render.append(f"{int(model_info['current_speed'])}kts")
            lines_to_render.append(f"{self.data.route_name}")
        else: # Pending SID
            lines_to_render.append(f"{self.data['label']}")
            lines_to_render.append(f"{self.data['acft_type']}")
            lines_to_render.append(f"Ruta: {self.data['name']}")
            
            time_to_departure = self.data['time'] - elapsed_time
            if self.data.get('_is_authorized_early', False) and not self.is_active_model : # Si está autorizado y aún no es modelo activo
                 lines_to_render.append("AUTORIZADO")
            elif time_to_departure > 0:
                minutes = int(time_to_departure) // 60
                seconds = int(time_to_departure) % 60
                lines_to_render.append(f"Sale en: {minutes:02d}:{seconds:02d}")
            else: # Tiempo cumplido, esperando ser procesado por Game
                lines_to_render.append("Listo Salida") 

            lines_to_render.append(f"Vel: {self.data['speed']}kts")

        current_y = self.rect.top + TEXT_PADDING_Y
        for i, line_text in enumerate(lines_to_render):
            if i >= 5: break
            text_surface = self.font.render(line_text, True, TEXT_COLOR)
            surface.blit(text_surface, (self.rect.left + TEXT_PADDING_X, current_y))
            current_y += LINE_SPACING

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def handle_click(self, game_ref):
        if not self.is_active_model and self.strip_type == "SID":
            if not self.data.get('_is_authorized_early', False): # Solo autorizar si no lo está ya
                print(f"FlightStripView: SID '{self.data['label']}' clickeada. Solicitando despegue temprano.")
                game_ref.request_early_departure(self.data['label'])
                # self.data['_is_authorized_early'] = True # game_ref.request_early_departure lo hará
            else:
                print(f"FlightStripView: SID '{self.data['label']}' ya estaba autorizado.")


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

    def update(self, active_aircraft_models, full_aircraft_creation_data, elapsed_time): # Recibe el dict completo
        self.arrival_strips.clear()
        self.departure_strips.clear()

        for model in active_aircraft_models:
            if model.route_type == "star":
                strip = FlightStripView(model, "STAR", self.font, self.panel_width)
                self.arrival_strips.append(strip)

        active_sid_labels = set()
        for model in active_aircraft_models:
            if model.route_type == "sid":
                strip = FlightStripView(model, "SID", self.font, self.panel_width)
                self.departure_strips.append(strip)
                active_sid_labels.add(model.label)

        # Procesar SIDs pendientes desde full_aircraft_creation_data
        if self.game_ref.exercise_num_str in full_aircraft_creation_data:
            for ac_data in full_aircraft_creation_data[self.game_ref.exercise_num_str]: # Iterar sobre la lista del ejercicio actual
                route_name = ac_data['name']
                if route_name in self.game_ref.routes_config and \
                   self.game_ref.routes_config[route_name]['type'] == 'sid' and \
                   ac_data['label'] not in active_sid_labels:
                    
                    # Condición para mostrar un SID pendiente:
                    # No ha sido procesado Y (su tiempo es futuro O ha sido autorizado temprano)
                    if not ac_data.get('_processed_and_killed', False) and \
                       (ac_data['time'] > elapsed_time or ac_data.get('_is_authorized_early', False)):
                        strip = FlightStripView(ac_data, "SID", self.font, self.panel_width)
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
            strip.draw(self.screen) 
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
        return False
