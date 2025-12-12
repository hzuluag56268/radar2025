"""
TUTORIAL: Adding Buttons to Flight Strips
==========================================

This tutorial will guide you through adding a third column with four buttons
(Pushback, Taxi, Hold Short, Takeoff) to the right of each flight strip.

We'll work step by step, explaining each concept as we go.

TABLE OF CONTENTS:
------------------
1. Understanding the Current Layout
2. Planning the New Column Structure
3. Step 1: Add Button Color Constants
4. Step 2: Adjust Column Widths
5. Step 3: Create Column 3 with Four Rows
6. Step 4: Draw Grid Lines for Column 3
7. Step 5: Create Button Drawing Function
8. Step 6: Add Button State Tracking
9. Step 7: Draw the Buttons
10. Step 8: Handle Button Clicks
11. Step 9: Add Hover Effects (Optional)

Let's begin!
"""

# ============================================================================
# SECTION 1: UNDERSTANDING THE CURRENT LAYOUT
# ============================================================================
"""
CURRENT LAYOUT:
---------------
Each flight strip currently has:
- Column 1 (60% width): 
  - Row 1: Callsign
  - Row 2: Aircraft Type (left) | Speed (right)
  
- Column 2 (40% width):
  - Row 1: Status (time until event, taxiing, etc.)
  - Row 2: Route name

WHAT WE'LL ADD:
---------------
- Column 3 (new, to the right):
  - Row 1: Pushback button
  - Row 2: Taxi button
  - Row 3: Hold Short button
  - Row 4: Takeoff button

Each button will be clickable and can show different states (normal, hovered, active).
"""

# ============================================================================
# SECTION 2: PLANNING THE NEW COLUMN STRUCTURE
# ============================================================================
"""
NEW COLUMN WIDTHS:
------------------
We need to adjust the column widths to make room for Column 3:

Current:
- Column 1: 60%
- Column 2: 40%

New:
- Column 1: 50% (reduced from 60%)
- Column 2: 30% (reduced from 40%)
- Column 3: 20% (new - for buttons)

This gives us enough space for the buttons while keeping the main information readable.
"""

# ============================================================================
# STEP 1: ADD BUTTON COLOR CONSTANTS
# ============================================================================
"""
LOCATION: At the top of panel_ui.py, after the existing color constants
(around line 28)

Add these color constants for buttons:
"""

BUTTON_COLORS_EXAMPLE = """
# Button colors
BUTTON_BG_COLOR = (30, 50, 70)  # Darker background for buttons
BUTTON_HOVER_COLOR = (50, 70, 90)  # Lighter when hovering
BUTTON_TEXT_COLOR = (200, 200, 200)  # Light gray text
BUTTON_BORDER_COLOR = (80, 100, 120)  # Border for buttons
BUTTON_ACTIVE_COLOR = (0, 150, 0)  # Green when button is active/clicked
"""

"""
EXPLANATION:
- BUTTON_BG_COLOR: Default button background (darker than strip background)
- BUTTON_HOVER_COLOR: Color when mouse hovers over button
- BUTTON_TEXT_COLOR: Text color for button labels
- BUTTON_BORDER_COLOR: Border around each button
- BUTTON_ACTIVE_COLOR: Color when button is pressed/active (green)
"""

# ============================================================================
# STEP 2: ADJUST COLUMN WIDTHS
# ============================================================================
"""
LOCATION: In FlightStripView._draw_detailed_format() method
Around line 138-142

CURRENT CODE:
-------------
col1_width_ratio = 0.60  # Column 1 is 60% of strip width
col1_width = int(self.rect.width * col1_width_ratio)
col2_width = self.rect.width - col1_width

NEW CODE:
---------
col1_width_ratio = 0.50  # Column 1 is now 50% (reduced from 60%)
col1_width = int(self.rect.width * col1_width_ratio)
col2_width_ratio = 0.30  # Column 2 is now 30% (reduced from 40%)
col2_width = int(self.rect.width * col2_width_ratio)
col3_width = self.rect.width - col1_width - col2_width  # Column 3 gets remaining space (~20%)
"""

COLUMN_WIDTH_CODE = """
# --- Calculate cell geometry ---
# Column widths
col1_width_ratio = 0.50  # Column 1 is now 50% (reduced from 60%)
col1_width = int(self.rect.width * col1_width_ratio)
col2_width_ratio = 0.30  # Column 2 is now 30% (reduced from 40%)
col2_width = int(self.rect.width * col2_width_ratio)
col3_width = self.rect.width - col1_width - col2_width  # Column 3 gets remaining space
"""

"""
EXPLANATION:
- We calculate each column width as a percentage of the total strip width
- Column 3 gets whatever space is left after Column 1 and Column 2
- Using int() ensures we get whole pixel values
"""

# ============================================================================
# STEP 3: CREATE COLUMN 3 WITH FOUR ROWS
# ============================================================================
"""
LOCATION: In FlightStripView._draw_detailed_format() method
After Column 2 definitions (around line 163)

Add this code to create four button rows:
"""

COLUMN_3_CODE = """
# Column 3: Four rows (buttons)
c3_base_rect = pygame.Rect(self.rect.left + col1_width + col2_width, self.rect.top, 
                          col3_width, self.rect.height)
c3_row_height = self.rect.height // 4  # Each button row is 1/4 of height

c3_r1_rect = pygame.Rect(c3_base_rect.left, c3_base_rect.top, 
                         c3_base_rect.width, c3_row_height)
c3_r2_rect = pygame.Rect(c3_base_rect.left, c3_base_rect.top + c3_row_height,
                         c3_base_rect.width, c3_row_height)
c3_r3_rect = pygame.Rect(c3_base_rect.left, c3_base_rect.top + (2 * c3_row_height),
                         c3_base_rect.width, c3_row_height)
c3_r4_rect = pygame.Rect(c3_base_rect.left, c3_base_rect.top + (3 * c3_row_height),
                         c3_base_rect.width, self.rect.height - (3 * c3_row_height))
"""

"""
EXPLANATION:
- c3_base_rect: The entire Column 3 rectangle
  - Starts at: left edge of Column 1 + Column 2 widths
  - Width: col3_width
  - Height: Full strip height

- c3_row_height: Height of each button row (1/4 of strip height)
  - Using // (integer division) ensures whole pixels

- c3_r1_rect through c3_r4_rect: Four rectangles, one for each button
  - Each row is positioned vertically:
    - Row 1: At the top (c3_base_rect.top)
    - Row 2: One row_height down
    - Row 3: Two row_heights down
    - Row 4: Three row_heights down, with remaining height
"""

# ============================================================================
# STEP 4: DRAW GRID LINES FOR COLUMN 3
# ============================================================================
"""
LOCATION: In FlightStripView._draw_detailed_format() method
After existing grid lines (around line 180)

Add these lines to separate Column 3 visually:
"""

GRID_LINES_CODE = """
# Vertical line between Column 2 and Column 3
pygame.draw.line(surface, LINE_COLOR, (c2_base_rect.right, self.rect.top),
                (c2_base_rect.right, self.rect.bottom), 1)

# Horizontal lines in Column 3 (between button rows)
for i in range(1, 4):
    y_pos = c3_base_rect.top + (i * c3_row_height)
    pygame.draw.line(surface, LINE_COLOR, (c3_base_rect.left, y_pos),
                    (c3_base_rect.right, y_pos), 1)
"""

"""
EXPLANATION:
- First line: Vertical separator between Column 2 and Column 3
  - Starts at right edge of Column 2
  - Goes from top to bottom of strip

- Loop: Draws three horizontal lines separating the four button rows
  - i ranges from 1 to 3 (creating lines after rows 1, 2, and 3)
  - Each line is positioned at: top + (row_number * row_height)
"""

# ============================================================================
# STEP 5: CREATE BUTTON DRAWING FUNCTION
# ============================================================================
"""
LOCATION: In FlightStripView class, after _render_text_in_cell() method
Around line 99

Add this method to draw individual buttons:
"""

BUTTON_DRAWING_METHOD = """
def _draw_button(self, surface, button_rect, text, is_active=False, is_hovered=False):
    \"\"\"
    Draw a button in the flight strip.
    
    Args:
        surface: Pygame surface to draw on
        button_rect: Rectangle defining button bounds
        text: Button label text
        is_active: If True, button is in active/pressed state
        is_hovered: If True, button is being hovered over
    \"\"\"
    # Choose button color based on state
    if is_active:
        bg_color = BUTTON_ACTIVE_COLOR
    elif is_hovered:
        bg_color = BUTTON_HOVER_COLOR
    else:
        bg_color = BUTTON_BG_COLOR
    
    # Draw button background
    pygame.draw.rect(surface, bg_color, button_rect)
    # Draw button border
    pygame.draw.rect(surface, BUTTON_BORDER_COLOR, button_rect, 1)
    
    # Draw button text (centered)
    text_surface = self.font.render(text, True, BUTTON_TEXT_COLOR)
    text_rect = text_surface.get_rect()
    text_rect.center = button_rect.center
    surface.blit(text_surface, text_rect)
"""

"""
EXPLANATION:
- This method draws a single button with:
  1. Background color (changes based on state)
  2. Border around the button
  3. Centered text label

- State priority:
  1. If active (pressed): Green color
  2. Else if hovered: Lighter gray
  3. Else: Default dark gray

- Text centering:
  - text_rect.center = button_rect.center centers the text
  - This makes the button label appear in the middle of the button
"""

# ============================================================================
# STEP 6: ADD BUTTON STATE TRACKING
# ============================================================================
"""
LOCATION: In FlightStripView.__init__() method
Around line 66, after self.strip_width assignment

Add button state tracking:
"""

BUTTON_STATE_INIT = """
# Button states - track which buttons are active
self.button_states = {
    'pushback': False,
    'taxi': False,
    'hold_short': False,
    'takeoff': False
}
self.hovered_button = None  # Track which button is currently hovered
"""

"""
EXPLANATION:
- button_states: Dictionary storing True/False for each button
  - False = button not pressed
  - True = button is active/pressed

- hovered_button: String name of button being hovered, or None
  - Used to highlight button when mouse is over it
"""

# ============================================================================
# STEP 7: DRAW THE BUTTONS
# ============================================================================
"""
LOCATION: In FlightStripView._draw_detailed_format() method
At the end, after rendering existing text (around line 253)

Add button drawing calls:
"""

DRAW_BUTTONS_CODE = """
# Draw buttons in Column 3
self._draw_button(surface, c3_r1_rect, "Pushback", 
                 is_active=self.button_states['pushback'],
                 is_hovered=(self.hovered_button == 'pushback'))
self._draw_button(surface, c3_r2_rect, "Taxi", 
                 is_active=self.button_states['taxi'],
                 is_hovered=(self.hovered_button == 'taxi'))
self._draw_button(surface, c3_r3_rect, "Hold Short", 
                 is_active=self.button_states['hold_short'],
                 is_hovered=(self.hovered_button == 'hold_short'))
self._draw_button(surface, c3_r4_rect, "Takeoff", 
                 is_active=self.button_states['takeoff'],
                 is_hovered=(self.hovered_button == 'takeoff'))
"""

"""
EXPLANATION:
- We call _draw_button() for each of the four buttons
- Each button:
  - Uses its corresponding rectangle (c3_r1_rect, etc.)
  - Has its label text
  - Checks if it's active from button_states
  - Checks if it's hovered by comparing hovered_button

- The buttons will appear in order from top to bottom:
  1. Pushback
  2. Taxi
  3. Hold Short
  4. Takeoff
"""

# ============================================================================
# STEP 8: HANDLE BUTTON CLICKS
# ============================================================================
"""
LOCATION: In FlightStripView class, after is_clicked() method
Around line 265

Add method to detect which button was clicked:
"""

GET_CLICKED_BUTTON_METHOD = """
def get_clicked_button(self, pos):
    \"\"\"
    Check which button (if any) was clicked.
    
    Args:
        pos: Mouse position (x, y)
        
    Returns:
        Button name string ('pushback', 'taxi', 'hold_short', 'takeoff') or None
    \"\"\"
    # Recalculate button rectangles (same as in _draw_detailed_format)
    col1_width_ratio = 0.50
    col1_width = int(self.rect.width * col1_width_ratio)
    col2_width_ratio = 0.30
    col2_width = int(self.rect.width * col2_width_ratio)
    col3_width = self.rect.width - col1_width - col2_width
    
    c3_base_rect = pygame.Rect(self.rect.left + col1_width + col2_width, self.rect.top, 
                              col3_width, self.rect.height)
    c3_row_height = self.rect.height // 4
    
    # Define all button rectangles
    buttons = [
        ('pushback', pygame.Rect(c3_base_rect.left, c3_base_rect.top, 
                                 c3_base_rect.width, c3_row_height)),
        ('taxi', pygame.Rect(c3_base_rect.left, c3_base_rect.top + c3_row_height, 
                            c3_base_rect.width, c3_row_height)),
        ('hold_short', pygame.Rect(c3_base_rect.left, c3_base_rect.top + (2 * c3_row_height), 
                                   c3_base_rect.width, c3_row_height)),
        ('takeoff', pygame.Rect(c3_base_rect.left, c3_base_rect.top + (3 * c3_row_height), 
                                c3_base_rect.width, self.rect.height - (3 * c3_row_height)))
    ]
    
    # Check which button contains the click position
    for button_name, button_rect in buttons:
        if button_rect.collidepoint(pos):
            return button_name
    return None
"""

"""
EXPLANATION:
- This method recalculates button positions (same as drawing)
- Creates a list of tuples: (button_name, button_rect)
- Loops through buttons checking if pos is inside each rectangle
- Returns button name if found, None if no button clicked

- Why recalculate? Because button positions depend on self.rect, which
  might change when strips are repositioned
"""

"""
Now update handle_click() method to handle button clicks:
"""

HANDLE_CLICK_UPDATE = """
def handle_click(self, game_ref, mouse_pos):
    \"\"\"
    Handle click on this strip.
    
    For SID (departure) strips, clicking authorizes early departure.
    Button clicks toggle button states.
    
    Args:
        game_ref: Reference to Game instance
        mouse_pos: Mouse position (x, y)
    \"\"\"
    # Check if a button was clicked
    clicked_button = self.get_clicked_button(mouse_pos)
    if clicked_button:
        # Toggle button state
        self.button_states[clicked_button] = not self.button_states[clicked_button]
        # Here you can add logic to trigger actions based on button state
        # For example: game_ref.handle_departure_action(self.data['label'], clicked_button)
        return True
    
    # Original click handling for early departure authorization
    if self.strip_type == "sid":
        if not self.data.get('_is_authorized_early', False):
            game_ref.request_early_departure(self.data['label'])
        return True
    
    return False
"""

"""
EXPLANATION:
- First checks if a button was clicked
- If yes: Toggles button state (False -> True, True -> False)
- If no button clicked: Falls back to original behavior (early departure)
- Returns True if event was handled

- Toggle logic: not self.button_states[clicked_button]
  - If False, becomes True
  - If True, becomes False
"""

"""
Update SidePanel.handle_panel_input() to pass mouse position:
"""

SIDEPANEL_UPDATE = """
# In SidePanel.handle_panel_input(), around line 442:
if strip.is_clicked(mouse_pos):
    if strip.strip_type == "sid":
        strip.handle_click(self.game_ref, mouse_pos)  # Pass mouse_pos
        return True
"""

# ============================================================================
# STEP 9: ADD HOVER EFFECTS (OPTIONAL BUT RECOMMENDED)
# ============================================================================
"""
LOCATION: In SidePanel class, after handle_panel_input() method
Around line 445

Add method to update hover state:
"""

HOVER_METHOD = """
def update_hover(self, mouse_pos):
    \"\"\"
    Update hover state for buttons in strips.
    
    Args:
        mouse_pos: Mouse position (x, y)
    \"\"\"
    for strip in self.arrival_strips + self.departure_strips:
        if strip.is_clicked(mouse_pos):
            # Strip is clicked, check which button
            strip.hovered_button = strip.get_clicked_button(mouse_pos)
        else:
            # Mouse not over this strip
            strip.hovered_button = None
"""

"""
EXPLANATION:
- Loops through all strips (arrivals + departures)
- If mouse is over a strip: Check which button is hovered
- If mouse not over strip: Clear hover state

- Call this method in your main game loop when handling pygame.MOUSEMOTION events
"""

"""
In your main game loop (radar.py), add:
"""

MAIN_LOOP_UPDATE = """
# In your event handling loop:
for event in pygame.event.get():
    if event.type == pygame.MOUSEMOTION:
        # Update button hover states
        self.side_panel.update_hover(event.pos)
    # ... rest of your event handling
"""

# ============================================================================
# SUMMARY: COMPLETE CODE CHANGES CHECKLIST
# ============================================================================
"""
QUICK REFERENCE CHECKLIST:
---------------------------

□ 1. Add button color constants at top of file
□ 2. Adjust column width ratios (50%, 30%, 20%)
□ 3. Create Column 3 rectangle and four button rectangles
□ 4. Draw grid lines for Column 3
□ 5. Add _draw_button() method
□ 6. Add button_states and hovered_button to __init__
□ 7. Call _draw_button() for each button in _draw_detailed_format()
□ 8. Add get_clicked_button() method
□ 9. Update handle_click() to handle button clicks
□ 10. Update SidePanel.handle_panel_input() to pass mouse_pos
□ 11. (Optional) Add update_hover() method and call in main loop

TESTING TIPS:
-------------
1. Run your program and check that Column 3 appears
2. Click each button - it should toggle between normal and green (active)
3. Move mouse over buttons - they should highlight
4. Click outside buttons but on strip - should still work for early departure
"""

# ============================================================================
# ADVANCED: ADDING FUNCTIONALITY TO BUTTONS
# ============================================================================
"""
Once buttons are working, you can add game logic:

EXAMPLE: Trigger actions when buttons are clicked
--------------------------------------------------
In handle_click(), after toggling button state:

if clicked_button == 'pushback':
    game_ref.start_pushback(self.data['label'])
elif clicked_button == 'taxi':
    game_ref.start_taxi(self.data['label'])
elif clicked_button == 'hold_short':
    game_ref.hold_short(self.data['label'])
elif clicked_button == 'takeoff':
    game_ref.authorize_takeoff(self.data['label'])

EXAMPLE: Auto-activate buttons based on aircraft state
-------------------------------------------------------
In update() or draw(), check aircraft status:

if aircraft_is_taxiing:
    self.button_states['taxi'] = True
if aircraft_at_hold_short:
    self.button_states['hold_short'] = True
"""

print("Tutorial loaded! Read through each section to learn how to add buttons.")
print("Each section includes code examples and explanations.")
print("\nStart with Step 1 and work through each step in order.")

