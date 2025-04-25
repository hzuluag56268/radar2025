class Aircraft(pygame.sprite.Sprite):
    def __init__(self, groups, color, route_name, speed,label, screen, ui, acft_type):  # Added `label` parameter
        super().__init__(groups)
        self.route_name = route_name
        self.route_type = ROUTES[self.route_name]["type"]
        self.start_pos = ROUTES[self.route_name]["pixel_points"][0]
        self.radius = 8
        self.color = color
        self.label = label  # Added to store a unique identifier for the aircraft
        self.creation_time = time.time()
        self.start_segment_time = time.time()
        self.speed = speed
        self.acft_type = acft_type
        self.cumulative_distance_to_last_descent = 0
        self.partial_cumulative_distance_travelled = 0
        self.cumulative_distance_travelled = 0
        self.cumulative_segment_distance = 0
        self.current_segment = 0
        self.current_segment_distance_nm = 0
        self.ui = ui
        self.altitude =self.start_altitude = ROUTES[self.route_name]['altitude']
        self.desired_altitude = 6000 if ROUTES[self.route_name]["type"] == "star" else 24000
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center= self.start_pos)
        self.moving_point = ROUTES[self.route_name]["pixel_points"][0]
        self.descent_rate = 333  # feet per nautical mile
        self.in_holding_pattern = False
        self.pending_holding_pattern = False
        self.finish_holding_pattern = False
        self.screen = screen
        self.label_offset = (15, -20)  # Default offset for the label relative to the aircraft
        self.dragging_label = False  # Track whether the label is being dragged


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
            #f"{self.speed} kts",      # Aircraft speed
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
        elif mouse_pressed[2]:  # Right mouse button is pressed
            if label_rect.collidepoint(mouse_pos):
                # Right-click selects the aircraft
                self.acft_selected()
        else:
            # Stop dragging when the mouse button is released
            self.dragging_label = False
            # Update the offset relative to the aircraft
            self.label_offset = (self.label_position[0] - self.rect.centerx,
                                 self.label_position[1] - self.rect.centery)
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
        

    def update(self):
        #self.get_input()
        
        p1, p2 = ROUTES[self.route_name]["pixel_points"][self.current_segment], \
                 ROUTES[self.route_name]["pixel_points"][self.current_segment + 1]
        self.current_segment_distance_nm = ROUTES[self.route_name]["distances"][self.current_segment]
        time_required_sec = (self.current_segment_distance_nm / self.speed) * 3600
        segment_elapsed = time.time() - self.start_segment_time
        t = min(segment_elapsed / time_required_sec, 1)
        self.moving_point = self.interpolate(p1, p2, t)
        self.rect.center = self.moving_point
        self.cumulative_segment_distance = t * self.current_segment_distance_nm
        self.cumulative_distance_travelled = \
            (self.partial_cumulative_distance_travelled + self.cumulative_segment_distance) - \
            self.cumulative_distance_to_last_descent
        self.altitude = \
            self.calculate_altitude(self.cumulative_distance_travelled, self.start_altitude, self.desired_altitude)

        if t >= 1:
            self.partial_cumulative_distance_travelled += self.current_segment_distance_nm
            self.current_segment += 1
            self.start_segment_time = time.time()
            if self.current_segment >= len(ROUTES[self.route_name]["pixel_points"]) - 1:
                if self.in_holding_pattern and self.finish_holding_pattern:
                    self.kill()
                elif not self.in_holding_pattern and self.pending_holding_pattern:
                    self.in_holding_pattern = True
                    self.current_segment = 0
                    self.route_name = "HOLDING"
                elif not self.in_holding_pattern and not self.pending_holding_pattern:
                    self.kill()
                elif self.in_holding_pattern:
                    self.current_segment = 0
        
        self.draw_label(self.screen, pygame.font.Font(None, 24))
        
