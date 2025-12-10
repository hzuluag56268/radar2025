"""
Context menu UI system for aircraft commands.

This module provides the ui class which handles:
- Right-click context menu for aircraft commands
- Different menu options for STAR (arrival) vs SID (departure) aircraft
- Altitude input window for altitude change commands
- Keyboard input processing for altitude entry

The menu is displayed when an aircraft is right-clicked, and commands
are sent back to the Game class for processing.
"""

from settings import *


class ui():
    """
    Context menu and altitude input UI handler.
    
    This class manages:
    - Context menu display (right-click menu with aircraft commands)
    - Menu option selection
    - Altitude input window (for altitude change commands)
    - Keyboard input for altitude entry
    
    The menu shows different options depending on aircraft type:
    - STAR (arrival): Join/Finish holding, stop/continue descent
    - SID (departure): Stop/continue climb
    """
    
    def __init__(self):
        """Initialize UI manager with default settings."""
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 30)  # Font for menu text
        
        # Menu position and layout
        self.left = 0  # X position of menu
        self.top = 0  # Y position of menu
        self.cols = 1  # Number of columns (currently always 1)
        self.route_name = None  # Currently unused
        self.option_height = 25  # Height of each menu option
        
        # Menu state
        self.show_menu = False  # Whether menu is currently visible
        self.level_window_active = False  # Whether altitude input window is active
        self.string_level = ""  # Current altitude input text
        self.update_level = False  # Currently unused
        self.is_continue_descent = False  # Flag: is current command a "continue" command?
        
        # Aircraft type tracking
        self.active_aircraft_type = None  # Type of selected aircraft (star/sid)
        self.is_star = None  # Currently unused
        
        # Menu options for different aircraft types
        self.star_options = [
            "Join Holding Pattern",
            "Finish Holding Pattern",
            "Stop descent at",
            "Continue descent to",
            "disregard"
        ]
        self.sid_options = [
            "Stop climb at",
            "continue climb to",
            "disregard"
        ]

        # Current menu configuration
        self.menu_options = None  # Current menu options (set when menu displayed)
        self.rows = None  # Number of menu rows (set when menu displayed)

    def process_menu_click(self, pos):
        """
        Process a click on the context menu.
        
        Determines which menu option was clicked (if any) and returns
        the action string. Returns "close_menu" if click was outside menu.
        
        Args:
            pos: Mouse position (x, y) tuple
            
        Returns:
            Action string (e.g., "Join Holding Pattern") or "close_menu" or None
        """
        if not self.show_menu:
            return None

        # Reconstruct menu rectangle for collision detection
        menu_rect = pygame.Rect(self.left + 10, self.top + 10, 
                               self.cols * 400, self.rows * self.option_height)
        
        # Check if click was outside menu
        if not menu_rect.collidepoint(pos):
            return "close_menu"  # Special identifier for outside click

        # Calculate which option was clicked
        for col in range(self.cols):
            for row in range(self.rows):
                # Calculate center of option
                x = menu_rect.left + menu_rect.width / (self.cols * 2) + (menu_rect.width / self.cols) * col
                y = menu_rect.top + menu_rect.height / (self.rows * 2) + (menu_rect.height / self.rows) * row
                i = row  # Assuming single column

                # Create text surface to get bounding rect
                option_text_surf = self.font.render(self.menu_options[i], True, (0, 255, 0))
                option_text_rect = option_text_surf.get_rect(center=(x, y))

                # Check if click was on this option
                if option_text_rect.collidepoint(pos):
                    selected_action = self.menu_options[i]
                    print(f"UI: Acción seleccionada '{selected_action}'")

                    # Check if this is a "continue" command
                    self.is_continue_descent = "Continue" in selected_action or "continue" in selected_action

                    return selected_action
        
        return None  # No option clicked

    def show_level(self):
        """
        Draw the altitude input window.
        
        Displays a text input box showing the current altitude value being entered.
        Called from draw() when level_window_active is True.
        """
        if self.level_window_active:
            # Input box rectangle
            rect2 = pygame.Rect(0, 0, 400, 25)
            # Draw background
            pygame.draw.rect(self.display_surface, (0, 0, 0), rect2, 0, 4)
            # Draw border
            pygame.draw.rect(self.display_surface, (0, 0, 80), rect2, 4, 4)

            # Render current input text
            text_surf2 = self.font.render(f"level: {self.string_level}", True, (0, 255, 0))
            text_rect2 = text_surf2.get_rect(center=(rect2.centerx, rect2.centery))
            self.display_surface.blit(text_surf2, text_rect2)

    def display_menu(self, position, aircraft_route_type):
        """
        Display context menu at specified position.
        
        Menu options are determined by aircraft route type (STAR or SID).
        
        Args:
            position: Menu position (x, y) tuple (usually mouse position)
            aircraft_route_type: "star" or "sid" to determine menu options
        """
        self.left, self.top = position
        self.active_aircraft_type = aircraft_route_type  # Save for reference

        # Determine menu options based on route type
        is_star = aircraft_route_type == "star"
        self.menu_options = self.star_options if is_star else self.sid_options
        self.rows = len(self.menu_options)
        self.show_menu = True
        self.level_window_active = False  # Close altitude input if open

    def hide_menu(self):
        """Hide the context menu."""
        self.show_menu = False

    def display_level_input(self, position):
        """
        Show altitude input window.
        
        Called when user selects an altitude command from menu.
        User can then type altitude value and press Enter.
        
        Args:
            position: Position for input window (currently unused, window is at fixed position)
        """
        self.string_level = ""  # Reset input text
        self.level_window_active = True
        self.show_menu = False  # Hide menu when showing input

    def hide_level_input(self):
        """
        Hide altitude input window and return entered value.
        
        Returns:
            Entered altitude as string (empty if nothing entered)
        """
        self.level_window_active = False
        entered_level = self.string_level
        self.string_level = ""  # Clear for next time
        return entered_level

    def handle_level_input_keypress(self, event):
        """
        Process keyboard input for altitude entry.
        
        Handles:
        - Enter: Complete input (returns True)
        - Backspace: Delete last character
        - Digits: Add to input string
        
        Args:
            event: Pygame keyboard event
            
        Returns:
            True if Enter was pressed (input complete), False otherwise
        """
        if not self.level_window_active:
            return False

        if event.key == pygame.K_RETURN:  # Enter key
            print("UI: Enter presionado en Level Input")
            # Game will call hide_level_input() to get the value
            return True  # Input complete
        elif event.key == pygame.K_BACKSPACE:  # Backspace
            self.string_level = self.string_level[:-1]  # Remove last character
        elif event.unicode.isdigit():  # Digit key
            self.string_level += event.unicode  # Add digit to input
        
        return False  # Input not complete yet

    def draw(self):
        """
        Draw UI elements (menu and/or altitude input window).
        
        Called each frame by Game class. Only draws if menu or input window is active.
        """
        # Draw altitude input window if active
        if self.level_window_active:
            self.show_level()
        
        # Don't draw menu if not visible
        if not self.show_menu:
            return

        # Ensure menu stays within screen bounds
        menu_width = self.cols * 400 + 20
        if self.left + menu_width > self.display_surface.get_width() - PANEL_WIDTH:
            self.left = self.display_surface.get_width() - PANEL_WIDTH - menu_width
        if self.left < 0:
            self.left = 0
        if self.top + 10 + self.rows * self.option_height > self.display_surface.get_height():
            self.top -= 10 + self.rows * self.option_height
        

        
        # Menu rectangle
        rect = pygame.Rect(self.left + 10, self.top + 10,
                          self.cols * 400, self.rows * self.option_height)
        
        # Draw menu background
        pygame.draw.rect(self.display_surface, (0, 0, 0), rect, 0, 4)
        # Draw menu border
        pygame.draw.rect(self.display_surface, (0, 80, 0), rect, 4, 4)
        
        # Draw menu options
        for col in range(self.cols):
            for row in range(self.rows):
                # Calculate option center position
                x = rect.left + rect.width / (self.cols * 2) + (rect.width / self.cols) * col
                y = rect.top + rect.height / (self.rows * 2) + (rect.height / self.rows) * row
                i = row
                
                # Render option text if valid
                if self.menu_options and i < len(self.menu_options):
                    text_surf = self.font.render(self.menu_options[i], True, (0, 255, 0))
                    text_rect = text_surf.get_rect(center=(x, y))
                    self.display_surface.blit(text_surf, text_rect)
