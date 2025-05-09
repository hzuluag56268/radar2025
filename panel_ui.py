# panel_ui.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH # Importar dimensiones necesarias

# Colores y configuraciones para el panel y las fichas
TEXT_COLOR = (0, 255, 0)  # Verde radar
PANEL_BG_COLOR = (15, 25, 35) # Un azul oscuro/gris para el fondo del panel
STRIP_BG_COLOR = (25, 45, 65) # Un poco más claro para el fondo de la ficha
STRIP_BORDER_COLOR = (50, 80, 120) # Borde para la ficha
SEPARATOR_COLOR = (0, 100, 0) # Línea divisoria
STRIP_HEIGHT = 90  # Altura de cada ficha (ajustar según necesidad para 5 líneas)
STRIP_PADDING = 5  # Espacio vertical entre fichas
LINE_SPACING = 16 # Espacio entre líneas de texto dentro de la ficha (ajustar según tamaño de fuente)
TEXT_PADDING_X = 8 # Padding horizontal para el texto dentro de la ficha
TEXT_PADDING_Y = 5 # Padding vertical para el texto dentro de la ficha

class FlightStripView:
    def __init__(self, data, strip_type, font, strip_width):
        """
        Inicializa una vista de ficha de vuelo.
        data: Puede ser una instancia de AircraftModel (para aeronaves activas)
              o un diccionario de aircraft_creation_data (para SIDs pendientes).
        strip_type: "STAR" o "SID".
        font: La instancia de pygame.font.Font a utilizar.
        strip_width: El ancho de la ficha.
        """
        self.data = data
        self.strip_type = strip_type
        self.font = font
        self.strip_width = strip_width
        self.rect = pygame.Rect(0, 0, self.strip_width, STRIP_HEIGHT) # Posición (x,y) será asignada por SidePanel

        self.is_active_model = hasattr(self.data, 'label') and hasattr(self.data, 'altitude') # Comprueba si es AircraftModel

    def draw(self, surface):
        """Dibuja la ficha de vuelo en la superficie dada."""
        # Dibujar fondo y borde de la ficha
        pygame.draw.rect(surface, STRIP_BG_COLOR, self.rect)
        pygame.draw.rect(surface, STRIP_BORDER_COLOR, self.rect, 1)

        lines_to_render = []
        if self.is_active_model: # Aeronave activa (AircraftModel)
            lines_to_render.append(f"{self.data.label}")
            lines_to_render.append(f"{self.data.acft_type}")
            alt_text = f"FL{int(self.data.altitude / 100):03d}"
            # Opcional: Mostrar altitud deseada
            # if self.data.altitude != self.data.desired_altitude:
            #     direction = ">" if self.data.desired_altitude < self.data.altitude else "<"
            #     alt_text += f" {direction} FL{int(self.data.desired_altitude / 100):03d}"
            lines_to_render.append(alt_text)
            lines_to_render.append(f"{int(self.data.current_speed)}kts")
            lines_to_render.append(f"{self.data.route_name}")
        else: # SID pendiente (diccionario de aircraft_creation_data)
            lines_to_render.append(f"{self.data['label']}")
            lines_to_render.append(f"{self.data['acft_type']}")
            lines_to_render.append(f"Ruta: {self.data['name']}")
            lines_to_render.append("Programado") # Placeholder, Fase 2 mostrará countdown
            lines_to_render.append(f"Vel: {self.data['speed']}kts")


        # Renderizar y blittear cada línea de texto
        current_y = self.rect.top + TEXT_PADDING_Y
        for i, line_text in enumerate(lines_to_render):
            if i >= 5: break # Limitar a 5 líneas por ahora
            text_surface = self.font.render(line_text, True, TEXT_COLOR)
            surface.blit(text_surface, (self.rect.left + TEXT_PADDING_X, current_y))
            current_y += LINE_SPACING

    def is_clicked(self, pos):
        """Comprueba si la posición del clic está dentro de esta ficha."""
        return self.rect.collidepoint(pos)

    def handle_click(self, game_ref):
        """Maneja un clic en la ficha (se implementará en Fase 2 para SIDs)."""
        # Por ahora, solo para SIDs pendientes y si es clickeable
        if not self.is_active_model and self.strip_type == "SID":
            print(f"Ficha SID (programada) '{self.data['label']}' clickeada. Autorizando despegue...")
            game_ref.request_early_departure(self.data['label'])
            # Podríamos cambiar un estado aquí para que draw() muestre "Autorizado"
            # o simplemente dejar que la lógica de update del panel la reemplace
            # cuando se convierta en un modelo activo.


class SidePanel:
    def __init__(self, screen, font, game_ref):
        """
        Inicializa la barra lateral.
        screen: La superficie principal de Pygame.
        font: La instancia de pygame.font.Font para las fichas.
        game_ref: Referencia a la instancia de Game.
        """
        self.screen = screen
        self.font = font # Considera usar una fuente más pequeña para el panel
        self.game_ref = game_ref

        self.panel_x = SCREEN_WIDTH
        self.panel_y = 0
        self.panel_width = PANEL_WIDTH
        self.panel_height = SCREEN_HEIGHT

        self.arrivals_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height / 2)
        self.departures_rect = pygame.Rect(self.panel_x, self.panel_y + self.panel_height / 2, self.panel_width, self.panel_height / 2)

        self.arrival_strips = []
        self.departure_strips = []

        # Podrías querer una fuente específica (más pequeña) para el panel
        # self.panel_font = pygame.font.Font(None, 18) # Ejemplo

    def update(self, active_models, pending_ac_data, elapsed_time):
        """Actualiza las listas de fichas de llegada y salida."""
        self.arrival_strips.clear()
        self.departure_strips.clear()

        # Llegadas (STARs activas)
        for model in active_models:
            if model.route_type == "star":
                strip = FlightStripView(model, "STAR", self.font, self.panel_width)
                self.arrival_strips.append(strip)

        # Salidas (SIDs)
        # Primero, SIDs activos
        active_sids_labels = set()
        for model in active_models:
            if model.route_type == "sid":
                strip = FlightStripView(model, "SID", self.font, self.panel_width)
                self.departure_strips.append(strip)
                active_sids_labels.add(model.label)

        # Luego, SIDs pendientes (que no estén ya activos)
        for data_entry in pending_ac_data:
            # Asegurarse que solo se añaden SIDs y que no estén ya en la lista de activos
            # (esto último es importante si un SID se activa por clic antes de su tiempo)
            route_info = self.game_ref.routes_config.get(data_entry['name'])
            if route_info and route_info["type"] == "sid" and data_entry['label'] not in active_sids_labels:
                # Y que realmente esté pendiente (su tiempo es futuro)
                if data_entry['time'] > elapsed_time or data_entry.get('_is_authorized_early', False):
                    strip = FlightStripView(data_entry, "SID", self.font, self.panel_width)
                    self.departure_strips.append(strip)


    def draw(self):
        """Dibuja la barra lateral completa, incluyendo las fichas."""
        # Dibujar fondo del panel
        panel_main_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_main_rect)

        # Dibujar línea divisoria
        divider_y = self.arrivals_rect.bottom
        pygame.draw.line(self.screen, SEPARATOR_COLOR, (self.panel_x, divider_y), (self.panel_x + self.panel_width, divider_y), 2)

        # Dibujar Fichas de Llegada
        current_y = self.arrivals_rect.top + STRIP_PADDING
        for strip in self.arrival_strips:
            if current_y + STRIP_HEIGHT > self.arrivals_rect.bottom: # No dibujar si excede el área
                break
            strip.rect.topleft = (self.panel_x, current_y)
            strip.draw(self.screen)
            current_y += STRIP_HEIGHT + STRIP_PADDING

        # Dibujar Fichas de Salida
        current_y = self.departures_rect.top + STRIP_PADDING
        for strip in self.departure_strips:
            if current_y + STRIP_HEIGHT > self.departures_rect.bottom: # No dibujar si excede el área
                break
            strip.rect.topleft = (self.panel_x, current_y)
            strip.draw(self.screen)
            current_y += STRIP_HEIGHT + STRIP_PADDING

    def handle_panel_input(self, event, mouse_pos):
        """Maneja la entrada del mouse para el panel (clics en fichas)."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Clic izquierdo
            # Solo chequear clics en las fichas de salida por ahora para la interactividad
            for strip in self.departure_strips:
                if strip.is_clicked(mouse_pos):
                    # Solo las fichas de SIDs pendientes son interactivas de esta manera
                    if not strip.is_active_model and strip.strip_type == "SID":
                        strip.handle_click(self.game_ref)
                        # Podríamos retornar True para indicar que el clic fue consumido
                        return True
        return False