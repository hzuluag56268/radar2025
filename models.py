from settings import *


class AircraftModel:
    def __init__(self, route_name, initial_speed, label, acft_type, initial_altitude, desired_altitude_init, initial_pos, route_type_val, routes_data):
        self.routes_data = routes_data # Inyectar ROUTES

        self.route_name = route_name
        self.current_speed = float(initial_speed)
        self.label = label
        self.acft_type = acft_type

        self.route_type = route_type_val # e.g., "star" o "sid"
        self.start_pos = initial_pos # Este es el punto de píxel inicial
        self.altitude = float(initial_altitude)
        self.start_altitude = float(initial_altitude) # Altitud al inicio del segmento/descenso actual
        self.desired_altitude = float(desired_altitude_init)

        self.moving_point = list(initial_pos) # Posición actual en píxeles [x, y]

        self.descent_rate = 400  # pies por milla náutica
        self.creation_time = time.time()

        self.distance_covered_on_segment_nm = 0.0
        self.target_speed = float(initial_speed)
        self.acceleration_rate = 1.0 # kts por segundo

        self.cumulative_distance_to_last_descent_start_nm = 0.0 # Distancia acumulada en la ruta hasta el inicio del último comando de descenso/ascenso
        self.partial_cumulative_distance_travelled_nm = 0.0 # Distancia acumulada en la ruta hasta el inicio del segmento actual

        self.current_segment_index = 0
        # self.current_segment_distance_nm = 0 # Se obtiene del route_data

        self.in_holding_pattern = False
        self.pending_holding_pattern = False
        self.finish_holding_pattern = False
        self._is_pending_continue_descent_or_climb = False
        self.alive = True # Para marcar si debe ser eliminado

    def _get_current_route_data(self):
        """Devuelve los datos de la ruta actual (normal o holding)."""
        return self.routes_data.get(self.route_name, None)

    def set_desired_altitude(self, altitude_str):
        try:
            new_desired_altitude = float(altitude_str)
            if self._is_pending_continue_descent_or_climb:
                # Si es una continuación, la altitud actual es el nuevo punto de partida para el cálculo.
                self.start_altitude = self.altitude
                # La distancia acumulada hasta el punto actual se convierte en la base para el nuevo cálculo de descenso/ascenso.
                self.cumulative_distance_to_last_descent_start_nm = \
                    self.partial_cumulative_distance_travelled_nm + self.distance_covered_on_segment_nm
                self._is_pending_continue_descent_or_climb = False
                print(f"{self.label}: Altitud de inicio para continuación actualizada a {self.start_altitude:.0f} ft")

            elif self.desired_altitude != new_desired_altitude: # Si es un nuevo comando y diferente al actual
                self.start_altitude = self.altitude # Iniciar el cálculo desde la altitud actual
                # La distancia acumulada hasta el punto actual.
                self.cumulative_distance_to_last_descent_start_nm = \
                    self.partial_cumulative_distance_travelled_nm + self.distance_covered_on_segment_nm

            self.desired_altitude = new_desired_altitude
            print(f"{self.label}: Altitud deseada actualizada a {self.desired_altitude:.0f} ft")
        except ValueError:
            print(f"Error: Valor de altitud inválido '{altitude_str}' para {self.label}")

    def set_pending_holding(self, flag: bool):
        self.pending_holding_pattern = flag
        if flag:
             self.finish_holding_pattern = False # No puedes querer terminar un holding que apenas vas a iniciar
        print(f"{self.label}: Pending holding pattern: {self.pending_holding_pattern}")

    def set_finish_holding(self, flag: bool):
        if self.in_holding_pattern: # Solo se puede finalizar si ya está en holding
            self.finish_holding_pattern = flag
            print(f"{self.label}: Finish holding pattern: {self.finish_holding_pattern}")
        else:
            print(f"{self.label}: No se puede finalizar holding, no está en patrón de espera.")


    def set_continue_descent_climb_flag(self, flag: bool):
        self._is_pending_continue_descent_or_climb = flag

    def _interpolate(self, p1, p2, t):
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        return (x, y)

    def _calculate_altitude_change(self, cumulative_distance_from_change_point_nm):
        """Calcula la altitud basándose en la distancia desde el punto donde se inició el cambio de altitud."""
        if self.route_type == "star": # Descenso
            return max(self.start_altitude - (cumulative_distance_from_change_point_nm * self.descent_rate), self.desired_altitude)
        else: # Ascenso (SID)
            return min(self.start_altitude + (cumulative_distance_from_change_point_nm * self.descent_rate), self.desired_altitude)

    def update_speed_and_distance(self, dt):
        """Actualiza la velocidad y la distancia cubierta en el frame."""
        if self.altitude < 10000 and self.current_speed > 250 and self.target_speed > 250 and not self.in_holding_pattern:
            self.target_speed = 250.0

        speed_difference = self.target_speed - self.current_speed
        if abs(speed_difference) > 0.1: # Umbral
            change = self.acceleration_rate * dt * (1 if speed_difference > 0 else -1)
            if abs(change) > abs(speed_difference):
                self.current_speed = self.target_speed
            else:
                self.current_speed += change

        distance_this_frame_nm = self.current_speed * (dt / 3600.0) # dt en segundos
        self.distance_covered_on_segment_nm += distance_this_frame_nm

    def update_position(self):
        """Actualiza la posición de la aeronave a lo largo del segmento actual."""
        route_data = self._get_current_route_data()
        if not route_data or not route_data["pixel_points"] or self.current_segment_index + 1 >= len(route_data["pixel_points"]):
            # Si no hay datos de ruta válidos o el índice del segmento está fuera de rango, no se puede actualizar la posición.
            # Esto podría pasar si la ruta no existe o si ya completó todos los segmentos y está esperando ser eliminada.
            return

        p1 = route_data["pixel_points"][self.current_segment_index]
        p2 = route_data["pixel_points"][self.current_segment_index + 1]

        current_segment_total_distance_nm = route_data["distances"][self.current_segment_index]

        if current_segment_total_distance_nm <= 0: # Evitar división por cero
             t_distance = 1.0 # Asumir que se completó el segmento si la distancia es cero o negativa
        else:
            t_distance = self.distance_covered_on_segment_nm / current_segment_total_distance_nm

        t_distance = max(0.0, min(t_distance, 1.0))
        self.moving_point = self._interpolate(p1, p2, t_distance)
        return t_distance


    def update_altitude_state(self):
        """Actualiza la altitud de la aeronave."""
        # Distancia total recorrida en la ruta desde que se inició el último comando de cambio de altitud.
        dist_for_alt_calc_nm = (self.partial_cumulative_distance_travelled_nm + self.distance_covered_on_segment_nm) - self.cumulative_distance_to_last_descent_start_nm
        self.altitude = self._calculate_altitude_change(dist_for_alt_calc_nm)

    def update_segment_or_holding_logic(self, t_distance):
        """Actualiza el segmento actual o maneja la lógica de holding."""
        route_data = self._get_current_route_data()
        if not route_data:
            self.alive = False
            return

        current_segment_total_distance_nm = route_data["distances"][self.current_segment_index]

        if t_distance >= 1.0: # Si se completó el segmento
            self.partial_cumulative_distance_travelled_nm += current_segment_total_distance_nm
            self.current_segment_index += 1
            self.distance_covered_on_segment_nm = 0 # Reiniciar para el nuevo segmento

            # ¿Llegó al final de la ruta definida?
            if self.current_segment_index >= len(route_data["pixel_points"]) - 1:
                if self.in_holding_pattern:
                    if self.finish_holding_pattern:
                        print(f"{self.label} saliendo de holding y terminando ruta.")
                        self.alive = False # Termina después de salir del holding
                    else: # Continuar en el patrón de espera
                        self.current_segment_index = 0 # Reinicia al inicio del patrón de espera
                        # Mantener velocidad de holding si está definida, o la que tenía
                elif self.pending_holding_pattern:
                    print(f"{self.label} entrando en holding.")
                    self.in_holding_pattern = True
                    self.pending_holding_pattern = False
                    self.route_name = "HOLDING" # Cambiar a la ruta de holding
                    # Actualizar datos de ruta para holding
                    new_route_data = self._get_current_route_data()
                    if not new_route_data:
                        print(f"Error: Ruta HOLDING no encontrada para {self.label}")
                        self.alive = False
                        return
                    self.current_segment_index = 0
                    self.partial_cumulative_distance_travelled_nm = 0 # Reiniciar distancia acumulada para el holding
                    self.distance_covered_on_segment_nm = 0
                    self.start_pos = new_route_data["pixel_points"][0]
                    self.moving_point = list(self.start_pos)
                    # Ajustar altitud y velocidad para el holding si es necesario
                    # self.desired_altitude = altitud_de_holding (ej. la actual o una fija)
                    self.target_speed = 200 # Velocidad típica de holding
                else: # No está en holding y no hay pendiente, llegó al final
                    print(f"{self.label} completó su ruta.")
                    self.alive = False


    def update(self, dt):
        if not self.alive or dt == 0:
            return

        self.update_speed_and_distance(dt)
        t_distance = self.update_position() # t_distance es la fracción del segmento completada
        self.update_altitude_state()
        if t_distance is not None: # Solo si la posición se pudo actualizar
             self.update_segment_or_holding_logic(t_distance)

    def get_info_for_label(self):
        """Devuelve un diccionario con la información necesaria para la etiqueta."""
        return {
            'label': self.label,
            'altitude': self.altitude,
            'current_speed': self.current_speed,
            'acft_type': self.acft_type,
            'moving_point': self.moving_point # Para la línea conectora de la etiqueta
        }