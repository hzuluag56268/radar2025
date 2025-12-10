"""
Aircraft model - contains state and logic for aircraft movement and behavior.

This module defines the AircraftModel class which represents a single aircraft in the simulation.
The model handles:
- Position tracking along route segments
- Altitude changes (descent for STAR, climb for SID)
- Speed management (acceleration, speed restrictions)
- Route segment transitions
- Holding pattern logic
- Command processing (altitude changes, holding)

The model is updated each frame by the Game class and provides data to views for rendering.
"""

from settings import *


class AircraftModel:
    """
    Represents a single aircraft in the simulation.
    
    The model maintains all aircraft state and handles movement logic:
    - Position along route (interpolated between waypoints)
    - Altitude (calculated based on distance from descent/climb start)
    - Speed (with acceleration and restrictions)
    - Route progression (segment transitions, holding patterns)
    - Command processing (altitude changes, holding entry/exit)
    
    The model is independent of rendering - views read from the model to display information.
    """
    
    def __init__(self, route_name, initial_speed, label, acft_type, initial_altitude, desired_altitude_init, initial_pos, route_type_val, routes_data):
        """
        Initialize a new aircraft model.
        
        Args:
            route_name: Name of the route (must exist in routes_data)
            initial_speed: Starting speed in knots
            label: Aircraft callsign/identifier
            acft_type: Aircraft type code (e.g., "A320", "B737")
            initial_altitude: Starting altitude in feet
            desired_altitude_init: Initial target altitude (6000 for STAR, 24000 for SID)
            initial_pos: Starting pixel position [x, y]
            route_type_val: "star" (arrival) or "sid" (departure)
            routes_data: Dictionary of all route definitions (injected dependency)
        """
        self.routes_data = routes_data  # All route definitions for route switching (e.g., to HOLDING)

        # Basic aircraft properties
        self.route_name = route_name
        self.current_speed = float(initial_speed)
        self.label = label
        self.acft_type = acft_type

        # Route information
        self.route_type = route_type_val  # "star" (arrival) or "sid" (departure)
        self.start_pos = initial_pos  # Starting pixel position
        self.altitude = float(initial_altitude)  # Current altitude in feet
        self.start_altitude = float(initial_altitude)  # Altitude at start of current descent/climb
        self.desired_altitude = float(desired_altitude_init)  # Target altitude

        # Position tracking
        self.moving_point = list(initial_pos)  # Current pixel position [x, y]

        # Movement parameters
        self.descent_rate = 400  # Feet per nautical mile (used for both descent and climb)
        self.creation_time = time.time()  # When this model was created

        # Distance tracking
        self.distance_covered_on_segment_nm = 0.0  # Distance traveled on current segment
        self.target_speed = float(initial_speed)  # Target speed (for acceleration)
        self.acceleration_rate = 1.0  # Knots per second acceleration/deceleration

        # Altitude change tracking
        # Distance from route start to where last altitude change command was issued
        self.cumulative_distance_to_last_descent_start_nm = 0.0
        # Distance from route start to beginning of current segment
        self.partial_cumulative_distance_travelled_nm = 0.0

        # Route segment tracking
        self.current_segment_index = 0  # Which segment of the route we're on

        # Holding pattern state
        self.in_holding_pattern = False  # Currently in holding pattern
        self.pending_holding_pattern = False  # Will enter holding at end of route
        self.finish_holding_pattern = False  # Will exit holding at end of route
        self._is_pending_continue_descent_or_climb = False  # Flag for "continue" altitude commands
        self.alive = True  # Set to False when aircraft should be removed

    def _get_current_route_data(self):
        """
        Get route data for the current route (normal route or holding).
        
        Returns:
            Dictionary with route information (pixel_points, distances, etc.) or None if route not found
        """
        return self.routes_data.get(self.route_name, None)

    def set_desired_altitude(self, altitude_str):
        """
        Set a new target altitude for the aircraft.
        
        This method handles both new altitude commands and "continue" commands:
        - New command: Starts descent/climb from current altitude
        - Continue command: Continues previous descent/climb from current position
        
        The altitude change is calculated based on distance traveled, not time.
        
        Args:
            altitude_str: Target altitude as string (will be converted to float)
        """
        try:
            new_desired_altitude = float(altitude_str)
            
            if self._is_pending_continue_descent_or_climb:
                # This is a "continue" command - resume from current altitude
                self.start_altitude = self.altitude
                # Update distance reference point to current position
                self.cumulative_distance_to_last_descent_start_nm = \
                    self.partial_cumulative_distance_travelled_nm + self.distance_covered_on_segment_nm
                self._is_pending_continue_descent_or_climb = False
                print(f"{self.label}: Altitud de inicio para continuación actualizada a {self.start_altitude:.0f} ft")

            elif self.desired_altitude != new_desired_altitude:
                # New altitude command (different from current target)
                self.start_altitude = self.altitude  # Start from current altitude
                # Set distance reference point to current position
                self.cumulative_distance_to_last_descent_start_nm = \
                    self.partial_cumulative_distance_travelled_nm + self.distance_covered_on_segment_nm

            self.desired_altitude = new_desired_altitude
            print(f"{self.label}: Altitud deseada actualizada a {self.desired_altitude:.0f} ft")
        except ValueError:
            print(f"Error: Valor de altitud inválido '{altitude_str}' para {self.label}")

    def set_pending_holding(self, flag: bool):
        """
        Set flag to enter holding pattern at end of current route.
        
        Args:
            flag: True to enter holding, False to cancel
        """
        self.pending_holding_pattern = flag
        if flag:
            # Can't finish a holding pattern we haven't entered yet
            self.finish_holding_pattern = False
        print(f"{self.label}: Pending holding pattern: {self.pending_holding_pattern}")

    def set_finish_holding(self, flag: bool):
        """
        Set flag to exit holding pattern at end of current holding cycle.
        
        Args:
            flag: True to exit holding, False to continue
        """
        if self.in_holding_pattern:  # Can only finish if already in holding
            self.finish_holding_pattern = flag
            print(f"{self.label}: Finish holding pattern: {self.finish_holding_pattern}")
        else:
            print(f"{self.label}: No se puede finalizar holding, no está en patrón de espera.")

    def set_continue_descent_climb_flag(self, flag: bool):
        """
        Set flag indicating next altitude command is a "continue" command.
        
        This is called before set_desired_altitude() when user selects
        "Continue descent to" or "continue climb to" from the menu.
        
        Args:
            flag: True if next command is a continuation
        """
        self._is_pending_continue_descent_or_climb = flag

    def _interpolate(self, p1, p2, t):
        """
        Linear interpolation between two points.
        
        Args:
            p1: Start point [x, y]
            p2: End point [x, y]
            t: Interpolation factor (0.0 to 1.0)
            
        Returns:
            Interpolated point (x, y)
        """
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        return (x, y)

    def _calculate_altitude_change(self, cumulative_distance_from_change_point_nm):
        """
        Calculate altitude based on distance traveled since altitude change command.
        
        Altitude changes are distance-based, not time-based:
        - STAR (arrival): Descends at descent_rate feet per nautical mile
        - SID (departure): Climbs at descent_rate feet per nautical mile
        
        Args:
            cumulative_distance_from_change_point_nm: Distance traveled since altitude change started
            
        Returns:
            New altitude in feet
        """
        if self.route_type == "star":  # Descending
            # Descend: start_altitude - (distance * rate), but don't go below desired
            return max(self.start_altitude - (cumulative_distance_from_change_point_nm * self.descent_rate), 
                      self.desired_altitude)
        else:  # Climbing (SID)
            # Climb: start_altitude + (distance * rate), but don't go above desired
            return min(self.start_altitude + (cumulative_distance_from_change_point_nm * self.descent_rate), 
                      self.desired_altitude)

    def update_speed_and_distance(self, dt):
        """
        Update aircraft speed and distance traveled this frame.
        
        Handles:
        - Speed restrictions (250 kts below 10,000 ft, except in holding)
        - Acceleration/deceleration toward target speed
        - Distance calculation based on current speed
        
        Args:
            dt: Delta time in seconds since last frame
        """
        # Speed restriction: 250 kts below 10,000 ft (unless in holding)
        if self.altitude < 10000 and self.current_speed > 250 and self.target_speed > 250 and not self.in_holding_pattern:
            self.target_speed = 250.0

        # Accelerate/decelerate toward target speed
        speed_difference = self.target_speed - self.current_speed
        if abs(speed_difference) > 0.1:  # Threshold to avoid oscillation
            change = self.acceleration_rate * dt * (1 if speed_difference > 0 else -1)
            # Don't overshoot target
            if abs(change) > abs(speed_difference):
                self.current_speed = self.target_speed
            else:
                self.current_speed += change

        # Calculate distance traveled this frame
        # Convert speed (knots) to nautical miles per second, then multiply by dt
        distance_this_frame_nm = self.current_speed * (dt / 3600.0)
        self.distance_covered_on_segment_nm += distance_this_frame_nm

    def update_position(self):
        """
        Update aircraft position along current route segment.
        
        Uses linear interpolation between segment waypoints based on
        distance traveled along the segment.
        
        Returns:
            t_distance: Fraction of segment completed (0.0 to 1.0), or None if error
        """
        route_data = self._get_current_route_data()
        if not route_data or not route_data["pixel_points"] or self.current_segment_index + 1 >= len(route_data["pixel_points"]):
            # Invalid route data or segment index out of range
            # This can happen if route doesn't exist or aircraft completed all segments
            return None

        # Get segment endpoints
        p1 = route_data["pixel_points"][self.current_segment_index]
        p2 = route_data["pixel_points"][self.current_segment_index + 1]

        # Get total distance of this segment
        current_segment_total_distance_nm = route_data["distances"][self.current_segment_index]

        # Calculate interpolation factor (0.0 = start, 1.0 = end)
        if current_segment_total_distance_nm <= 0:  # Avoid division by zero
            t_distance = 1.0  # Assume segment completed if distance is zero
        else:
            t_distance = self.distance_covered_on_segment_nm / current_segment_total_distance_nm

        # Clamp to valid range
        t_distance = max(0.0, min(t_distance, 1.0))
        
        # Interpolate position
        self.moving_point = self._interpolate(p1, p2, t_distance)
        return t_distance

    def update_altitude_state(self):
        """
        Update aircraft altitude based on distance traveled since altitude change command.
        
        Altitude is calculated from distance, not time, to maintain realistic
        descent/climb profiles regardless of frame rate.
        """
        # Calculate total distance traveled since altitude change started
        dist_for_alt_calc_nm = (self.partial_cumulative_distance_travelled_nm + 
                               self.distance_covered_on_segment_nm) - \
                               self.cumulative_distance_to_last_descent_start_nm
        
        # Update altitude based on distance
        self.altitude = self._calculate_altitude_change(dist_for_alt_calc_nm)

    def update_segment_or_holding_logic(self, t_distance):
        """
        Handle segment transitions and holding pattern logic.
        
        When a segment is completed (t_distance >= 1.0):
        - Move to next segment
        - Check if route is complete
        - Handle holding pattern entry/exit
        - Mark aircraft as dead if route complete
        
        Args:
            t_distance: Fraction of current segment completed (from update_position)
        """
        route_data = self._get_current_route_data()
        if not route_data:
            self.alive = False
            return

        current_segment_total_distance_nm = route_data["distances"][self.current_segment_index]

        if t_distance >= 1.0:  # Segment completed
            # Update cumulative distance
            self.partial_cumulative_distance_travelled_nm += current_segment_total_distance_nm
            # Move to next segment
            self.current_segment_index += 1
            # Reset distance for new segment
            self.distance_covered_on_segment_nm = 0

            # Check if reached end of route
            if self.current_segment_index >= len(route_data["pixel_points"]) - 1:
                if self.in_holding_pattern:
                    # Already in holding pattern
                    if self.finish_holding_pattern:
                        # Exit holding and end route
                        print(f"{self.label} saliendo de holding y terminando ruta.")
                        self.alive = False
                    else:
                        # Continue in holding - loop back to start
                        self.current_segment_index = 0
                        
                elif self.pending_holding_pattern:
                    # Enter holding pattern
                    print(f"{self.label} entrando en holding.")
                    self.in_holding_pattern = True
                    self.pending_holding_pattern = False
                    self.route_name = "HOLDING"  # Switch to holding route
                    
                    # Get holding route data
                    new_route_data = self._get_current_route_data()
                    if not new_route_data:
                        print(f"Error: Ruta HOLDING no encontrada para {self.label}")
                        self.alive = False
                        return
                    
                    # Reset for holding pattern
                    self.current_segment_index = 0
                    self.partial_cumulative_distance_travelled_nm = 0
                    self.distance_covered_on_segment_nm = 0
                    self.start_pos = new_route_data["pixel_points"][0]
                    self.moving_point = list(self.start_pos)
                    # Set holding speed (typically 200 kts)
                    self.target_speed = 200
                    
                else:
                    # Route complete, no holding - remove aircraft
                    print(f"{self.label} completó su ruta.")
                    self.alive = False

    def update(self, dt):
        """
        Main update method called each frame by Game class.
        
        Updates aircraft state in this order:
        1. Speed and distance
        2. Position along route
        3. Altitude
        4. Segment transitions and holding logic
        
        Args:
            dt: Delta time in seconds since last frame
        """
        if not self.alive or dt == 0:
            return

        # Update speed and calculate distance traveled
        self.update_speed_and_distance(dt)
        
        # Update position along current segment
        t_distance = self.update_position()  # Returns fraction of segment completed
        
        # Update altitude based on distance
        self.update_altitude_state()
        
        # Handle segment transitions if position was updated successfully
        if t_distance is not None:
            self.update_segment_or_holding_logic(t_distance)

    def get_info_for_label(self):
        """
        Get aircraft information for label display.
        
        This method provides data to AircraftLabelView for rendering.
        The view reads from the model but doesn't modify it.
        
        Returns:
            Dictionary with label, altitude, speed, type, and position
        """
        return {
            'label': self.label,
            'altitude': self.altitude,
            'current_speed': self.current_speed,
            'acft_type': self.acft_type,
            'moving_point': self.moving_point  # For drawing connector line from aircraft to label
        }
