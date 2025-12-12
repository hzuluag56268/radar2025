# Troubleshooting Guide: Button Hover Effect Not Working

## Problem Description
When you move your mouse over the buttons (Pushback, Taxi, Hold Short, Takeoff), the buttons should change color to show a hover effect, but they're not changing color.

---

## Root Cause Analysis

### Issue #1: Strips Are Recreated Every Frame
**The Problem:**
- In `SidePanel.update()`, the code does `self.arrival_strips.clear()` and `self.departure_strips.clear()`
- Then it creates **new** `FlightStripView` objects each frame
- When a new strip is created, its `hovered_button` attribute is reset to `None`
- So even if `update_hover()` sets the hover state, it gets lost on the next frame!

**Why This Happens:**
```python
# In update() method - this runs every frame
self.arrival_strips.clear()  # Deletes all existing strips
self.departure_strips.clear()  # Deletes all existing strips
# ... then creates new strips
strip = FlightStripView(...)  # New object = hovered_button = None
```

**The Fix:**
We need to position strips **before** `update_hover()` is called, so the rectangles are available for collision detection.

---

### Issue #2: Strips Are Positioned Too Late
**The Problem:**
- Strips are positioned in the `draw()` method
- But `update_hover()` is called in the event loop **before** `draw()` runs
- When `update_hover()` tries to check `strip.is_clicked(mouse_pos)`, the strip's `rect` hasn't been positioned yet!
- So `collidepoint()` always returns `False` because the rectangle is at (0, 0)

**Why This Happens:**
```python
# Event loop order:
for event in pygame.event.get():
    if event.type == pygame.MOUSEMOTION:
        self.side_panel.update_hover(event.pos)  # ← Called here
        # But strips aren't positioned yet!

# Later in the loop:
self.side_panel.update(...)  # Creates strips
# ... other code ...
self.side_panel.draw()  # Positions strips ← Too late!
```

**The Fix:**
Position strips immediately after creating them in `update()`, not in `draw()`.

---

### Issue #3: Hover Only Updates on Mouse Movement
**The Problem:**
- `update_hover()` is only called when `pygame.MOUSEMOTION` events occur
- If the mouse stops moving, hover state stops updating
- When strips are recreated, the hover state is lost

**The Fix:**
Call `update_hover()` after `update()` in the main loop, using the current mouse position.

---

## Step-by-Step Fix Instructions

### Step 1: Position Strips in `update()` Instead of `draw()`

**Location:** `panel_ui.py`, in the `SidePanel` class

**Current Code (in `update()` method):**
```python
def update(self, active_aircraft_models, full_aircraft_creation_data, elapsed_time):
    # ... creates strips ...
    if show_in_panel:
        strip = FlightStripView(...)
        if route_type == "star":
            self.arrival_strips.append(strip)
        elif route_type == "sid":
            self.departure_strips.append(strip)
    # ← Strips are created but NOT positioned here
```

**Add this at the end of `update()` method:**
```python
def update(self, active_aircraft_models, full_aircraft_creation_data, elapsed_time):
    # ... existing code that creates strips ...
    
    # ADD THIS: Position all strips so hover detection works correctly
    self._position_strips()
```

**Now add the `_position_strips()` method (add it right before the `draw()` method):**
```python
def _position_strips(self):
    """
    Position all flight strips so their rectangles are set correctly.
    This must be called before hover detection or drawing.
    """
    # Position arrival strips (top half)
    current_y = self.arrivals_rect.top + STRIP_PADDING_VERTICAL
    for strip in self.arrival_strips:
        # Stop if we've run out of space
        if current_y + STRIP_HEIGHT > self.arrivals_rect.bottom:
            break
        # Position strip
        strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
        # Move to next position
        current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL

    # Position departure strips (bottom half)
    current_y = self.departures_rect.top + STRIP_PADDING_VERTICAL
    for strip in self.departure_strips:
        # Stop if we've run out of space
        if current_y + STRIP_HEIGHT > self.departures_rect.bottom:
            break
        # Position strip
        strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)
        # Move to next position
        current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL
```

**Why This Works:**
- Strips are positioned immediately after creation
- When `update_hover()` is called, the rectangles are already positioned
- `collidepoint()` can now correctly detect if the mouse is over a strip

---

### Step 2: Update `draw()` to Use Already-Positioned Strips

**Location:** `panel_ui.py`, in the `SidePanel.draw()` method

**Current Code:**
```python
def draw(self):
    # ... background and separator ...
    
    # Draw arrival strips (top half)
    current_y = self.arrivals_rect.top + STRIP_PADDING_VERTICAL
    for strip in self.arrival_strips:
        if current_y + STRIP_HEIGHT > self.arrivals_rect.bottom:
            break
        strip.rect.topleft = (self.panel_x + STRIP_PADDING_HORIZONTAL, current_y)  # ← Remove this
        strip.draw(self.screen, self.game_ref.elapsed_time)
        current_y += STRIP_HEIGHT + STRIP_PADDING_VERTICAL
    
    # Similar for departure strips...
```

**Change to:**
```python
def draw(self):
    # ... background and separator ...
    
    # Draw arrival strips (top half)
    for strip in self.arrival_strips:
        # Only draw if strip is positioned (within visible area)
        if strip.rect.top < self.arrivals_rect.bottom:
            strip.draw(self.screen, self.game_ref.elapsed_time)

    # Draw departure strips (bottom half)
    for strip in self.departure_strips:
        # Only draw if strip is positioned (within visible area)
        if strip.rect.top < self.departures_rect.bottom:
            strip.draw(self.screen, self.game_ref.elapsed_time)
```

**Why This Works:**
- Strips are already positioned by `_position_strips()` in `update()`
- We just need to draw them, not position them again
- This avoids duplicate positioning code

---

### Step 3: Call `update_hover()` After `update()` in Main Loop

**Location:** `radar.py`, in the `Game.run()` method

**Find this code (around line 336):**
```python
# Update side panel with current aircraft data
self.side_panel.update(self.aircraft_models, self.aircraft_creation_data, self.elapsed_time)
```

**Change to:**
```python
# Update side panel with current aircraft data
self.side_panel.update(self.aircraft_models, self.aircraft_creation_data, self.elapsed_time)
# Update hover states (so hover works even when mouse isn't moving)
self.side_panel.update_hover(mouse_pos_tuple)
```

**Why This Works:**
- `update()` creates and positions strips
- Immediately after, we check hover state using current mouse position
- This ensures hover works continuously, not just on mouse movement events
- `mouse_pos_tuple` is already available (it's set earlier in the loop)

---

### Step 4: Improve `update_hover()` Method (Optional but Recommended)

**Location:** `panel_ui.py`, in the `SidePanel` class

**Current Code:**
```python
def update_hover(self, mouse_pos):
    for strip in self.arrival_strips + self.departure_strips:
        if strip.is_clicked(mouse_pos):
            button = strip.get_clicked_button(mouse_pos)
            strip.hovered_button = button
            break
        else:
            strip.hovered_button = None
```

**Change to:**
```python
def update_hover(self, mouse_pos):
    """
    Update hover state for buttons in strips.
    
    Args:
        mouse_pos: Mouse position (x, y)
    """
    # First, clear all hover states
    for strip in self.arrival_strips + self.departure_strips:
        strip.hovered_button = None
    
    # Then, find which strip (if any) the mouse is over
    for strip in self.departure_strips:  # Only check departure strips (they have buttons)
        if strip.is_clicked(mouse_pos):
            # Mouse is over this strip, check which button
            strip.hovered_button = strip.get_clicked_button(mouse_pos)
            break  # Only one strip can be hovered at a time
```

**Why This Works:**
- **Clear first, then set**: Ensures no "stuck" hover states
- **Only check departure strips**: Arrival strips don't have buttons, so skip them
- **Break after finding**: Only one strip can be hovered at a time

---

## Summary: Why These Changes Are Necessary

### The Core Problem
Pygame's event-driven system means:
1. Events are processed **before** drawing
2. Strips are recreated every frame
3. Hover state needs to be calculated **after** strips are positioned

### The Solution Flow
```
Frame Start
  ↓
Update() → Creates strips → Positions strips
  ↓
update_hover() → Checks mouse position → Sets hover state
  ↓
Draw() → Draws strips with hover state
  ↓
Frame End
```

### Key Concepts

1. **Timing Matters**: The order of operations is critical. Strips must be positioned before hover detection.

2. **State Persistence**: Since strips are recreated each frame, hover state must be recalculated each frame too.

3. **Coordinate Systems**: Rectangle positions must be set before collision detection can work.

---

## Testing Your Fix

After making these changes:

1. **Run your program**
2. **Move mouse over a departure strip** (bottom half of panel)
3. **Move mouse over a button** (Pushback, Taxi, Hold Short, or Takeoff)
4. **Button should change color** to the hover color (lighter gray/blue)

If it still doesn't work:
- Check that `_position_strips()` is being called in `update()`
- Check that `update_hover()` is being called after `update()` in the main loop
- Verify that `update_hover()` is checking `departure_strips` (not arrival strips)
- Make sure button rectangles are calculated the same way in both `_draw_detailed_format()` and `get_clicked_button()`

---

## Additional Notes

### Why Strips Are Recreated Every Frame
This is actually necessary because:
- Aircraft schedule changes over time
- Strips need to show current status (time until departure, etc.)
- Some aircraft disappear from the panel when they're created

The solution isn't to stop recreating strips, but to ensure hover state is recalculated each frame.

### Performance Consideration
Calling `update_hover()` every frame is fine because:
- It's a simple collision check (very fast)
- There are typically only a few strips visible
- Modern computers handle this easily at 60 FPS

---

## Quick Reference Checklist

- [ ] Added `self._position_strips()` call at end of `update()` method
- [ ] Created `_position_strips()` method that positions all strips
- [ ] Updated `draw()` method to not position strips (they're already positioned)
- [ ] Added `update_hover()` call after `update()` in main loop (`radar.py`)
- [ ] Improved `update_hover()` to clear states first, then set hover
- [ ] Tested hover effect on buttons

Good luck! 🚀

