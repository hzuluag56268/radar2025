#Parte 3: Modificar aircraft_modelLabelView
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

#Parte 3: Modificar AircraftLabelView
class AircraftLabelView:

    """
    Clase responsable de dibujar la etiqueta de una aeronave
    y manejar la interacción de arrastre con ella.
    """
    
    def __init__(self, aircraft_model, font, screen): # Cambiado: aircraft_model
        self.aircraft_model = aircraft_model
        self.font = font
        self.screen = screen # Necesaria para dibujar

        self.label_rect = pygame.Rect(0, 0, 0, 0) # Se calculará en draw
        # Para mantener la posición relativa durante el arrastre y entre updates
        # Se calcula respecto al centro del modelo (moving_point)
        self.relative_offset_from_aircraft = pygame.math.Vector2(15, -20)


        self.dragging_label = False
        # drag_start_mouse_pos y drag_start_label_pos son para calcular el movimiento durante el arrastre
        self.drag_start_mouse_pos = pygame.math.Vector2(0,0)
        self.drag_start_label_topleft = pygame.math.Vector2(0,0)

    def draw(self):
        if not self.aircraft_model.alive:
            return # No dibujar si el modelo no está vivo

        model_data = self.aircraft_model.get_info_for_label() # Obtener datos del modelo

        radar_green = (0, 255, 0)
        background_color = (0, 50, 0) # Un verde oscuro para el fondo de la etiqueta

        label_lines_text = [
            f"{model_data['label']}",
            f"{model_data['altitude']/100:.0f}00 ft", # FL
            f"{model_data['current_speed']:.0f}kts",   # Speed
            f"{model_data['acft_type']}"
        ]
        
        rendered_lines = [self.font.render(line, True, radar_green) for line in label_lines_text]

        # Calcular tamaño del rectángulo de la etiqueta
        line_height = rendered_lines[0].get_height() if rendered_lines else 10
        padding_internal = 3 # Espacio entre el texto y el borde del rectángulo
        padding_external = 5 # Espacio alrededor del texto para el rectángulo
        
        # El ancho de la etiqueta se basa en el texto más ancho
        text_widths = [surf.get_width() for surf in rendered_lines]
        max_text_width = max(text_widths) if text_widths else 50
        
        rect_width = max_text_width + 2 * padding_external
        rect_height = (len(rendered_lines) * line_height) + ( (len(rendered_lines) -1 ) * padding_internal if len(rendered_lines)>1 else 0) + 2*padding_external


        # Posición de la aeronave (centro del modelo)
        aircraft_center_pos = pygame.math.Vector2(model_data['moving_point'])
        
        # Calcular la posición top-left de la etiqueta usando el offset relativo
        current_label_topleft = aircraft_center_pos + self.relative_offset_from_aircraft

        # Asegurar que la etiqueta permanezca en pantalla (opcional, pero buena idea)
        current_label_topleft.x = max(0, min(current_label_topleft.x, self.screen.get_width() - rect_width))
        current_label_topleft.y = max(0, min(current_label_topleft.y, self.screen.get_height() - rect_height))
        
        self.label_rect.topleft = (current_label_topleft.x, current_label_topleft.y)
        self.label_rect.size = (rect_width, rect_height)

        # Dibujar línea conectora desde el centro de la aeronave al borde más cercano de la etiqueta
        # pygame.draw.line(self.screen, radar_green, aircraft_center_pos, self.label_rect.midleft, 1) # ejemplo
        # O a un punto fijo en la etiqueta, ej. centro del borde izquierdo
        connector_target_x = self.label_rect.left if aircraft_center_pos.x > self.label_rect.centerx else self.label_rect.right
        connector_target_y = self.label_rect.centery 
        pygame.draw.line(self.screen, radar_green, aircraft_center_pos, (connector_target_x,connector_target_y) , 1)


        # Dibujar rectángulo de la etiqueta
        pygame.draw.rect(self.screen, background_color, self.label_rect, border_radius=5)
        pygame.draw.rect(self.screen, radar_green, self.label_rect, width=1, border_radius=5)

        # Dibujar texto
        current_y = self.label_rect.top + padding_external
        for i, line_surface in enumerate(rendered_lines):
            self.screen.blit(line_surface, (self.label_rect.left + padding_external, current_y))
            current_y += line_height + padding_internal

    def handle_input_for_drag(self, event, mouse_pos_tuple, mouse_pressed):
        """Maneja la entrada para el arrastre de la etiqueta."""
        # Esta función sería llamada desde el bucle de eventos de Game
        # solo para las etiquetas visibles y activas.
        mouse_pos = pygame.math.Vector2(mouse_pos_tuple)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Clic izquierdo
            if self.label_rect.collidepoint(mouse_pos):
                self.dragging_label = True
                self.drag_start_mouse_pos = mouse_pos
                # Guardamos la posición inicial del topleft de la etiqueta al iniciar el arrastre
                self.drag_start_label_topleft = pygame.math.Vector2(self.label_rect.topleft)
                return True # Indica que este evento fue consumido por esta etiqueta

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_label:
                self.dragging_label = False
                # Al soltar, actualizamos el `relative_offset_from_aircraft`
                # para que la etiqueta recuerde su posición relativa al avión
                aircraft_center_pos = pygame.math.Vector2(self.aircraft_model.moving_point)
                self.relative_offset_from_aircraft = pygame.math.Vector2(self.label_rect.topleft) - aircraft_center_pos
                return True # Evento consumido

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_label:
                # Mover la etiqueta según el movimiento del ratón
                current_label_topleft = self.drag_start_label_topleft + (mouse_pos - self.drag_start_mouse_pos)
                
                # Actualizar el offset relativo mientras se arrastra
                aircraft_center_pos = pygame.math.Vector2(self.aircraft_model.moving_point)
                self.relative_offset_from_aircraft = current_label_topleft - aircraft_center_pos
                return True # Evento consumido
        
        return False # Evento no consumido por esta etiqueta

    def is_clicked(self, pos_tuple):
        """Verifica si la posición (tupla) colisiona con el rectángulo de esta etiqueta."""
        return self.label_rect.collidepoint(pos_tuple)
    


