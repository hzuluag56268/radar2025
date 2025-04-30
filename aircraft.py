from settings import *

#Revisar si puedo quitar. self.current_segment_distance_nm = 0 En el init y dejarlo solo como una variable de la función update.
class Aircraft(pygame.sprite.Sprite):
    def __init__(self, groups, color, route_name, initial_speed,label, screen, ui, acft_type):  # Added `label` parameter
        super().__init__(groups)
        self.color = color
        self.route_name = route_name
        self.current_speed = float(initial_speed)  # Convert to float for accurate calculation of initial_speed
        self.label = label  # Added to store a unique identifier for the aircraft
        self.screen = screen
        
        self.acft_type = acft_type
        
        self.route_type = ROUTES[self.route_name]["type"]
        self.start_pos = ROUTES[self.route_name]["pixel_points"][0]
        self.altitude =self.start_altitude = ROUTES[self.route_name]['altitude']
        self.desired_altitude = 6000 if ROUTES[self.route_name]["type"] == "star" else 24000
        self.moving_point = ROUTES[self.route_name]["pixel_points"][0]
        
        self.radius = 8
        self.descent_rate = 400  # feet per nautical mile
        self.creation_time = time.time()
        

        self.distance_covered_on_segment_nm = 0.0
        self.target_speed = float(initial_speed)  # Convert to float for accurate calculation of initial_speed0
        self.acceleration_rate = 1.0

        self.cumulative_distance_to_last_descent = 0.0
        self.partial_cumulative_distance_travelled = 0.0

        
        
        self.current_segment = 0
        self.current_segment_distance_nm = 0
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center= self.start_pos)
        
        self.in_holding_pattern = False
        self.pending_holding_pattern = False
        self.finish_holding_pattern = False
        
        self.label_offset = (15, -20)  # Default offset for the label relative to the aircraft
        self.dragging_label = False  # Track whether the label is being dragged

         #Añadir un Rect para la etiqueta (para detección de clics)
        self.label_rect = pygame.Rect(0, 0, 0, 0) # Inicializar
        self._is_pending_continue_descent_or_climb = False
    
    def draw_label(self, screen, font, icon=None):
        """
        Draws a radar-style label with each piece of information displayed on a separate line.
        """
        # Define radar-green color
        radar_green = (0, 255, 0)
        background_color = (0, 50, 0)  # Dark green for the rectangle background

        # Aircraft data for the label
        label_lines = [
            f"{self.label}",             # Aircraft identifier
            f"{self.altitude/100:.0f}00 ft",  # Current altitude
            f"{self.current_speed} kts",      # Aircraft current_speed
            f"{self.acft_type}"
        ]

        # Render each line of text
        rendered_lines = [font.render(line, True, radar_green) for line in label_lines]

        # Calculate the size of the label box
        line_height = rendered_lines[0].get_height()
        text_width = max(line.get_width() for line in rendered_lines)
        text_height = len(rendered_lines) * line_height + 6  # Add spacing between lines
        padding = 10
        rect_width = text_width + 2 * padding
        rect_height = text_height + padding

        # Determine the label's position relative to the aircraft
        if not self.dragging_label:
            # Calculate position relative to the aircraft
            rect_x = self.rect.centerx + self.label_offset[0]
            rect_y = self.rect.centery + self.label_offset[1]
        else:
            # Maintain the label position while dragging
            rect_x, rect_y = self.label_position

        # Dynamic placement to ensure label stays within screen bounds
        rect_x = max(0, min(rect_x, screen.get_width() - rect_width))
        rect_y = max(0, min(rect_y, screen.get_height() - rect_height))
        self.label_position = (rect_x, rect_y)

        self.label_rect.topleft = (rect_x, rect_y)
        self.label_rect.size = (rect_width, rect_height)

        # Draw a thin line connecting the label to the aircraft
        pygame.draw.line(screen, radar_green, self.rect.center, (rect_x + rect_width / 2, rect_y), 1)

        # Draw the rounded rectangle background
        pygame.draw.rect(
            screen,
        background_color,
            (rect_x, rect_y, rect_width, rect_height),
            border_radius=8
        )

        # Draw the rectangle border
        pygame.draw.rect(
            screen,
            radar_green,
            (rect_x, rect_y, rect_width, rect_height),
            width=2,
            border_radius=8
        )

        # Blit each line of text onto the rectangle
        for i, line_surface in enumerate(rendered_lines):
            line_y = rect_y + padding + i * line_height  # Position each line below the previous one
            screen.blit(line_surface, (rect_x + padding, line_y))

        # Handle mouse events for dragging and selection
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        label_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

        if mouse_pressed[0]:  # Left mouse button is pressed
            if label_rect.collidepoint(mouse_pos) and not self.dragging_label:
                # Start dragging when clicking on the label
                self.dragging_label = True
                self.drag_offset = (rect_x - mouse_pos[0], rect_y - mouse_pos[1])
            elif self.dragging_label:
                # Update label position while dragging
                self.label_position = (mouse_pos[0] + self.drag_offset[0], mouse_pos[1] + self.drag_offset[1])
                # Update the offset relative to the aircraft
                self.label_offset = (self.label_position[0] - self.rect.centerx,
                                     self.label_position[1] - self.rect.centery)
        
        else:
            # Stop dragging when the mouse button is released
            self.dragging_label = False
            # Update the offset relative to the aircraft
            self.label_offset = (self.label_position[0] - self.rect.centerx,
                                 self.label_position[1] - self.rect.centery)
    #def acft_selected(self):
    '''
    def acft_selected(self):
        if self.ui.show_menu:
            return
        print(" route type ", self.route_type, "ui star", self.ui.is_star)
        self.ui.is_star = self.route_type == "star"
        self.ui.left = self.rect.centerx
        self.ui.top = self.rect.centery
        print(" route type ", self.route_type, "ui star", self.ui.is_star)     

        self.ui.show_menu = True
        
        self.ui.acft = self
        '''
    def is_label_clicked(self, pos):
        """ Verifica si la posición dada está dentro del rectángulo de la etiqueta. """
    # self.label_rect se actualiza en draw_label
        return self.label_rect.collidepoint(pos)
    def set_desired_altitude(self, altitude_str):
        """ Establece la altitud deseada (llamado por Game). """
        try:
            # Reiniciar descenso/ascenso si es continuación
            if hasattr(self, '_is_pending_continue_descent_or_climb') and self._is_pending_continue_descent_or_climb:
                self.start_altitude = self.altitude #
                # Calcula distancia acumulada hasta el punto actual
                self.cumulative_distance_to_last_descent = \
                    self.partial_cumulative_distance_travelled + self.distance_covered_on_segment_nm
                self._is_pending_continue_descent_or_climb = False # Resetear bandera
                print(f"{self.label}: Altitud de inicio actualizada a {self.start_altitude}")

            self.desired_altitude = int(altitude_str) #
            print(f"{self.label}: Altitud deseada actualizada a {self.desired_altitude}")
        except ValueError:
            print(f"Error: Valor de altitud inválido '{altitude_str}' para {self.label}")

    def set_pending_holding(self, flag: bool):
        """ Establece si la aeronave debe entrar en holding (llamado por Game). """
        self.pending_holding_pattern = flag #
        print(f"{self.label}: Pending holding pattern: {self.pending_holding_pattern}")

    def set_finish_holding(self, flag: bool):
        """ Establece si la aeronave debe terminar el holding (llamado por Game). """
        self.finish_holding_pattern = flag #
        print(f"{self.label}: Finish holding pattern: {self.finish_holding_pattern}")

    def set_continue_descent_climb_flag(self, flag: bool):
        """ Bandera temporal para indicar que el próximo set_desired_altitude es una continuación """
        # Asegúrate de inicializar esta bandera en __init__
        # self._is_pending_continue_descent_or_climb = False
        self._is_pending_continue_descent_or_climb = flag
    def interpolate(self, p1, p2, t):
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        return (x, y)

    def calculate_altitude(self, cumulative_distance_from_last_descent, start_altitude, desired_altitude):
        if ROUTES[self.route_name]["type"] == "star":
            return max(start_altitude - (cumulative_distance_from_last_descent * self.descent_rate), desired_altitude)    
        else:
            return min(start_altitude + (cumulative_distance_from_last_descent * self.descent_rate), desired_altitude)
    #
    #Estas funciones  que tiene update son usadas dentro de la función update.
    def update_pos(self):
        p1, p2 = ROUTES[self.route_name]["pixel_points"][self.current_segment], \
                 ROUTES[self.route_name]["pixel_points"][self.current_segment + 1]
        
        self.current_segment_distance_nm = ROUTES[self.route_name]["distances"][self.current_segment]
        
        
        self.t_distance = self.distance_covered_on_segment_nm / self.current_segment_distance_nm
        self.t_distance = max(0.0, min(self.t_distance, 1.0)) 
        self.moving_point = self.interpolate(p1, p2, self.t_distance)
        self.rect.center = self.moving_point
    def update_altitude(self):
        dist_for_alt_calc  = \
            (self.partial_cumulative_distance_travelled + self.distance_covered_on_segment_nm) - \
            self.cumulative_distance_to_last_descent
        self.altitude = \
            self.calculate_altitude(dist_for_alt_calc , self.start_altitude, self.desired_altitude)
    def update_speed(self, dt):
    # Decide si self.target_speed debe cambiar (basado en altitud, etc.)

        if self.altitude < 10000 and self.current_speed > 250 and self.target_speed > 250:
            print(f"{self.label}: Estableciendo target_speed a 250 kts")
            self.target_speed = 250.0
        
        speed_difference = self.target_speed - self.current_speed
        if abs(speed_difference) > 0.1: # Un pequeño umbral para evitar oscilaciones
            change = self.acceleration_rate * dt * (1 if speed_difference > 0 else -1)
            # No sobrepasar el objetivo
            if abs(change) > abs(speed_difference):
                self.current_speed = self.target_speed
            else:
                self.current_speed += change

         #--- 2. Calcular Distancia Recorrida en este Frame ---
        distance_this_frame_nm = self.current_speed * (dt / 3600.0)
        self.distance_covered_on_segment_nm += distance_this_frame_nm
        
    def update_segment_or_hold(self):
        if self.t_distance >= 1:
            self.partial_cumulative_distance_travelled += self.current_segment_distance_nm
            self.current_segment += 1
            
            if self.current_segment >= len(ROUTES[self.route_name]["pixel_points"]) - 1:
                if self.in_holding_pattern and self.finish_holding_pattern:
                    self.kill()
                elif not self.in_holding_pattern and self.pending_holding_pattern:
                    self.in_holding_pattern = True
                    self.current_segment = 0
                    self.route_name = "HOLDING"
                    holding_speed = 200 # Ejemplo
                    self.target_speed = holding_speed
                elif not self.in_holding_pattern and not self.pending_holding_pattern:
                    self.kill()
                elif self.in_holding_pattern:
                    self.current_segment = 0
    def update(self, dt):
        if dt == 0:
            return
        #self.get_input()
         # --- 1. Actualizar Velocidad Instantánea ---
        self.update_speed(dt)
        
        self.update_pos()
        # --- 3. Actualizar Altitud ---
        self.update_altitude() 
        # --- 4. Actualizar Segmento ---
        #   4.1. Calcular Distancia Recorrida en el Segmento Actual
        self.update_segment_or_hold()

        self.draw_label(self.screen, pygame.font.Font(None, 24))
        
