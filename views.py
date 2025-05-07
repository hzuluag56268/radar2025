#Parte 3: Modificar AircraftLabelView
# views.py
from settings import *

class AircraftSprite(pygame.sprite.Sprite):
    def __init__(self, aircraft_model, color, screen):
        super().__init__()
        self.model = aircraft_model
        self.color = color # Podría venir del modelo o ser específico de la vista
        self.screen = screen # Necesario para el sprite si no se pasa al grupo de sprites

        self.radius = 6 # Radio visual del círculo

        # La imagen se crea una vez, pero su posición (rect) se actualiza
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)

        # El rect se actualiza en update() basado en model.moving_point
        self.rect = self.image.get_rect(center=self.model.moving_point)

    def update(self):
        """Actualiza la posición del sprite basada en el modelo."""
        if self.model.alive:
            self.rect.center = self.model.moving_point
        else:
            self.kill() # Elimina este sprite del grupo si el modelo ya no está vivo

    # No necesita un método draw() explícito si se añade a un pygame.sprite.Group
    # y se usa group.draw(screen). El grupo usa self.image y self.rect.


#Parte 3: Modificar AircraftLabelView
class AircraftLabelView:
    """
    Clase responsable de dibujar la etiqueta de una aeronave
    y manejar la interacción de arrastre con ella.
    """
    def __init__(self, aircraft, font):
        self.aircraft = aircraft  # Referencia a la instancia de Aircraft (el modelo)
        self.font = font
        # Obtenemos la pantalla desde la instancia de aircraft (asumiendo que aircraft tiene self.screen)
        # Si no, necesitarías pasar screen como parámetro a __init__
        self.screen = aircraft.screen
        # --- Atributos de estado de la etiqueta (movidos desde Aircraft) ---
        self.label_rect = pygame.Rect(0, 0, 0, 0)
        self.label_offset = (15, -20)  # Offset inicial por defecto
        self.label_position = (0, 0)   # Posición actual (se calculará)
        self.dragging_label = False
        self.drag_offset = (0, 0)

    def draw(self):
        """ Dibuja la etiqueta y maneja el arrastre. """
        # Define colores
        radar_green = (0, 255, 0)
        background_color = (0, 50, 0)

        # Obtener datos de la aeronave asociada
        label_lines = [
            f"{self.aircraft.label}",
            f"{self.aircraft.altitude/100:.0f}00 ft",
            # Asegúrate que current_speed sea formateado si es float
            f"{self.aircraft.current_speed:.0f} kts",
            f"{self.aircraft.acft_type}"
        ]

        # Renderizar texto
        rendered_lines = [self.font.render(line, True, radar_green) for line in label_lines]

        # Calcular tamaño de la caja
        line_height = rendered_lines[0].get_height()
        text_width = max(line.get_width() for line in rendered_lines)
        text_height = len(rendered_lines) * line_height + 6
        padding = 10
        rect_width = text_width + 2 * padding
        rect_height = text_height + padding

        # --- Lógica de Posición y Arrastre (usa self.xxx para estado de la etiqueta) ---
        # Usamos self.aircraft.rect para la posición base de la aeronave
        if not self.dragging_label:
            rect_x = self.aircraft.rect.centerx + self.label_offset[0]
            rect_y = self.aircraft.rect.centery + self.label_offset[1]
        else:
            rect_x, rect_y = self.label_position

        # Asegurar que la etiqueta permanezca en pantalla
        rect_x = max(0, min(rect_x, self.screen.get_width() - rect_width))
        rect_y = max(0, min(rect_y, self.screen.get_height() - rect_height))
        self.label_position = (rect_x, rect_y) # Guardar posición actual

        # Actualizar el Rect de la etiqueta para clics y dibujo
        self.label_rect.topleft = self.label_position
        self.label_rect.size = (rect_width, rect_height)

        # --- Lógica de Dibujo ---
        # Línea conectora (usa self.aircraft.rect.center)
        pygame.draw.line(self.screen, radar_green, self.aircraft.rect.center, (rect_x + rect_width / 2, rect_y), 1)
        # Fondo y borde de la etiqueta (usa self.label_rect)
        pygame.draw.rect(self.screen, background_color, self.label_rect, border_radius=8)
        pygame.draw.rect(self.screen, radar_green, self.label_rect, width=2, border_radius=8)
        # Texto
        for i, line_surface in enumerate(rendered_lines):
             line_y = rect_y + padding + i * line_height
             self.screen.blit(line_surface, (rect_x + padding, line_y))

        # --- Lógica de Input para Arrastre ---
        # (Considera mover esto a Game/InteractionManager eventualmente para mayor separación)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        if mouse_pressed[0]: # Botón izquierdo
            # Comprobar colisión con el Rect de esta etiqueta
            if self.label_rect.collidepoint(mouse_pos) and not self.dragging_label:
                self.dragging_label = True
                # Calcular offset inicial del arrastre respecto a la posición del ratón
                self.drag_offset = (self.label_position[0] - mouse_pos[0], self.label_position[1] - mouse_pos[1])
            elif self.dragging_label:
                # Actualizar posición de la etiqueta mientras se arrastra
                self.label_position = (mouse_pos[0] + self.drag_offset[0], mouse_pos[1] + self.drag_offset[1])
                # Actualizar el offset relativo a la aeronave (opcional, útil si quieres que recuerde la posición relativa)
                self.label_offset = (self.label_position[0] - self.aircraft.rect.centerx,
                                     self.label_position[1] - self.aircraft.rect.centery)
        else: # Botón izquierdo no presionado
             if self.dragging_label: # Si se soltó el botón mientras se arrastraba
                self.dragging_label = False
                # Guardar el último offset relativo a la aeronave
                self.label_offset = (self.label_position[0] - self.aircraft.rect.centerx,
                                     self.label_position[1] - self.aircraft.rect.centery)

    def is_clicked(self, pos):
         """ Verifica si la posición dada colisiona con el rectángulo de esta etiqueta. """
         return self.label_rect.collidepoint(pos)