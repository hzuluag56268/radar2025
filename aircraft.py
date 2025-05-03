from settings import *

#Revisar si puedo quitar. self.current_segment_distance_nm = 0 En el init y dejarlo solo como una variable de la función update.
class Aircraft(pygame.sprite.Sprite):
    def __init__(self, groups, color, route_name, initial_speed,label, screen, acft_type):  # Added `label` parameter
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
        
        
        self._is_pending_continue_descent_or_climb = False
    
  
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
            self.distance_covered_on_segment_nm = 0
            
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

        
        
