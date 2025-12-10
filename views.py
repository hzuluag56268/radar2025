"""
Aircraft views - visual representation of aircraft.

This module contains classes for rendering aircraft on screen:
- AircraftSprite: Pygame sprite representing aircraft as a colored circle
- AircraftLabelView: Displays aircraft information (label, altitude, speed, type) with drag-and-drop

These views read data from AircraftModel but don't modify it (separation of concerns).
"""

from settings import *


class AircraftSprite(pygame.sprite.Sprite):
    """
    Pygame sprite representing an aircraft as a colored circle.
    
    The sprite's position is automatically updated from the aircraft model each frame.
    The sprite is automatically removed when the aircraft model is marked as not alive.
    """
    
    def __init__(self, aircraft_model, color, screen):
        """
        Initialize aircraft sprite.
        
        Args:
            aircraft_model: AircraftModel instance to represent
            color: RGB tuple for sprite color (green for STAR, yellow for SID)
            screen: Pygame surface for rendering (currently unused but kept for compatibility)
        """
        super().__init__()
        self.model = aircraft_model  # Reference to model for position updates
        self.color = color  # Sprite color (could come from model or be view-specific)
        self.screen = screen  # Screen reference (kept for compatibility)

        self.radius = 6  # Visual radius of the circle

        # Create sprite image (circle on transparent surface)
        # Image is created once, but position (rect) is updated each frame
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)

        # Initialize rect at aircraft's starting position
        # Rect center will be updated in update() based on model.moving_point
        self.rect = self.image.get_rect(center=self.model.moving_point)

    def update(self):
        """
        Update sprite position from aircraft model.
        
        Called automatically by pygame.sprite.Group.update().
        If aircraft is no longer alive, removes sprite from group.
        """
        if self.model.alive:
            # Update position from model
            self.rect.center = self.model.moving_point
        else:
            # Remove sprite if aircraft is dead
            self.kill()


class AircraftLabelView:
    """
    Displays aircraft information label with drag-and-drop functionality.
    
    The label shows:
    - Aircraft callsign
    - Flight level (altitude / 100)
    - Speed in knots
    - Aircraft type
    
    The label can be dragged by the user and maintains its relative position
    to the aircraft. A connecting line is drawn from the aircraft to the label.
    """
    
    def __init__(self, aircraft_model, font, screen):
        """
        Initialize aircraft label view.
        
        Args:
            aircraft_model: AircraftModel instance to display
            font: Pygame font for rendering text
            screen: Pygame surface for drawing
        """
        self.aircraft_model = aircraft_model  # Reference to model for data
        self.font = font  # Font for text rendering
        self.screen = screen  # Screen surface for drawing

        # Label rectangle (calculated in draw() method)
        self.label_rect = pygame.Rect(0, 0, 0, 0)
        
        # Relative offset from aircraft center to label top-left
        # This maintains label position relative to aircraft during movement
        self.relative_offset_from_aircraft = pygame.math.Vector2(15, -20)

        # Drag state
        self.dragging_label = False  # Whether label is currently being dragged
        # Mouse position when drag started (for calculating drag delta)
        self.drag_start_mouse_pos = pygame.math.Vector2(0, 0)
        # Label position when drag started (for calculating new position)
        self.drag_start_label_topleft = pygame.math.Vector2(0, 0)

    def draw(self):
        """
        Draw the aircraft label with connecting line to aircraft.
        
        The label displays:
        - Callsign (e.g., "JEC5768")
        - Flight level (e.g., "17000 ft" -> "17000 ft")
        - Speed (e.g., "250kts")
        - Aircraft type (e.g., "A320")
        
        The label position is calculated relative to the aircraft's current position,
        and a connecting line is drawn from the aircraft center to the nearest edge of the label.
        """
        # Don't draw if aircraft is dead
        if not self.aircraft_model.alive:
            return

        # Get current aircraft data from model
        model_data = self.aircraft_model.get_info_for_label()

        # Colors
        radar_green = (0, 255, 0)  # Text and border color
        background_color = (0, 50, 0)  # Dark green background

        # Prepare label text lines
        label_lines_text = [
            f"{model_data['label']}",  # Callsign
            f"{model_data['altitude']/100:.0f}00 ft",  # Flight level (altitude / 100)
            f"{model_data['current_speed']:.0f}kts",  # Speed
            f"{model_data['acft_type']}"  # Aircraft type
        ]
        
        # Render each line as a surface
        rendered_lines = [self.font.render(line, True, radar_green) for line in label_lines_text]

        # Calculate label rectangle size
        line_height = rendered_lines[0].get_height() if rendered_lines else 10
        padding_internal = 3  # Space between text lines
        padding_external = 5  # Space around text inside rectangle border
        
        # Width based on widest text line
        text_widths = [surf.get_width() for surf in rendered_lines]
        max_text_width = max(text_widths) if text_widths else 50
        
        # Rectangle dimensions
        rect_width = max_text_width + 2 * padding_external
        rect_height = (len(rendered_lines) * line_height) + \
                     ((len(rendered_lines) - 1) * padding_internal if len(rendered_lines) > 1 else 0) + \
                     2 * padding_external

        # Calculate label position relative to aircraft
        aircraft_center_pos = pygame.math.Vector2(model_data['moving_point'])
        
        # Label top-left position = aircraft center + relative offset
        current_label_topleft = aircraft_center_pos + self.relative_offset_from_aircraft

        # Keep label on screen (clamp to screen bounds)
        current_label_topleft.x = max(0, min(current_label_topleft.x, self.screen.get_width() - rect_width))
        current_label_topleft.y = max(0, min(current_label_topleft.y, self.screen.get_height() - rect_height))
        
        # Update label rectangle
        self.label_rect.topleft = (current_label_topleft.x, current_label_topleft.y)
        self.label_rect.size = (rect_width, rect_height)

        # Draw connecting line from aircraft to label
        # Line goes to nearest edge of label (left if aircraft is to the right, right if to the left)
        connector_target_x = self.label_rect.left if aircraft_center_pos.x > self.label_rect.centerx else self.label_rect.right
        connector_target_y = self.label_rect.centery
        pygame.draw.line(self.screen, radar_green, aircraft_center_pos, 
                        (connector_target_x, connector_target_y), 1)

        # Draw label background rectangle
        pygame.draw.rect(self.screen, background_color, self.label_rect, border_radius=5)
        pygame.draw.rect(self.screen, radar_green, self.label_rect, width=1, border_radius=5)

        # Draw text lines
        current_y = self.label_rect.top + padding_external
        for i, line_surface in enumerate(rendered_lines):
            self.screen.blit(line_surface, (self.label_rect.left + padding_external, current_y))
            current_y += line_height + padding_internal

    def handle_input_for_drag(self, event, mouse_pos_tuple, mouse_pressed):
        """
        Handle mouse input for dragging the label.
        
        This method is called by Game class for mouse events.
        It handles:
        - Mouse button down: Start drag if clicking on label
        - Mouse motion: Update label position while dragging
        - Mouse button up: End drag and save new relative offset
        
        Args:
            event: Pygame event object
            mouse_pos_tuple: Current mouse position (x, y)
            mouse_pressed: Tuple of mouse button states (unused but kept for compatibility)
            
        Returns:
            True if event was consumed (handled), False otherwise
        """
        mouse_pos = pygame.math.Vector2(mouse_pos_tuple)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            if self.label_rect.collidepoint(mouse_pos):
                # Start dragging
                self.dragging_label = True
                self.drag_start_mouse_pos = mouse_pos
                # Save label position at drag start
                self.drag_start_label_topleft = pygame.math.Vector2(self.label_rect.topleft)
                return True  # Event consumed

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left release
            if self.dragging_label:
                # End dragging
                self.dragging_label = False
                # Update relative offset to maintain new position
                aircraft_center_pos = pygame.math.Vector2(self.aircraft_model.moving_point)
                self.relative_offset_from_aircraft = pygame.math.Vector2(self.label_rect.topleft) - aircraft_center_pos
                return True  # Event consumed

        elif event.type == pygame.MOUSEMOTION:  # Mouse movement
            if self.dragging_label:
                # Calculate new label position based on mouse movement
                current_label_topleft = self.drag_start_label_topleft + (mouse_pos - self.drag_start_mouse_pos)
                
                # Update relative offset while dragging
                aircraft_center_pos = pygame.math.Vector2(self.aircraft_model.moving_point)
                self.relative_offset_from_aircraft = current_label_topleft - aircraft_center_pos
                return True  # Event consumed
        
        return False  # Event not consumed

    def is_clicked(self, pos_tuple):
        """
        Check if label was clicked.
        
        Used by Game class to detect right-clicks on labels for context menu.
        
        Args:
            pos_tuple: Mouse position (x, y)
            
        Returns:
            True if position is within label rectangle, False otherwise
        """
        return self.label_rect.collidepoint(pos_tuple)
