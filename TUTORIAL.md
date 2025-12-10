# Radar Simulation - Code Structure Tutorial

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Concepts](#core-concepts)
3. [File Structure & Responsibilities](#file-structure--responsibilities)
4. [Data Flow](#data-flow)
5. [Key Interactions](#key-interactions)
6. [JSON Data Structures](#json-data-structures)
7. [How to Extend the Code](#how-to-extend-the-code)

---

## Architecture Overview

This radar simulation follows a **Model-View-Controller (MVC)** pattern with some variations:

- **Model** (`models.py`): Contains the business logic and state of aircraft
- **View** (`views.py`, `ui.py`, `panel_ui.py`): Handles rendering and visual representation
- **Controller** (`radar.py`): Orchestrates the game loop, event handling, and coordinates between models and views

```
┌─────────────────────────────────────────────────────────┐
│                    radar.py (Game)                      │
│              Main Controller & Game Loop                │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
       ┌───────▼────────┐        ┌───────▼────────┐
       │  models.py     │        │   views.py     │
       │  AircraftModel │        │ AircraftSprite │
       │  (State/Logic) │        │ AircraftLabel  │
       └───────┬────────┘        └───────┬────────┘
               │                          │
       ┌───────▼────────┐        ┌───────▼────────┐
       │   ui.py        │        │  panel_ui.py   │
       │  Context Menu  │        │  Flight Strips  │
       └────────────────┘        └────────────────┘
```

---

## Core Concepts

### 1. **Aircraft Lifecycle**

An aircraft goes through several states:

1. **Scheduled** → Defined in `exercises_config.json`, waiting to be created
2. **Created** → `AircraftModel` instance created when `elapsed_time >= aircraft['time']`
3. **Active** → Moving along route, responding to commands
4. **Holding** → In holding pattern (optional)
5. **Completed** → Reached end of route, `alive = False`

### 2. **Route Types**

- **STAR** (Standard Terminal Arrival Route): Aircraft arriving at airport (descending)
- **SID** (Standard Instrument Departure): Aircraft departing from airport (climbing)
- **HOLDING**: Circular holding pattern

### 3. **Coordinate Systems**

- **Geographic**: Lat/Lon coordinates (from JSON config)
- **Pixel**: Screen coordinates (converted via `latlon_to_pixel()`)
- **Distance**: Nautical miles (calculated using `pyproj.Geod`)

### 4. **Time Management**

- `elapsed_time`: Real-time clock since simulation start
- `time` (in aircraft data): Scheduled creation/departure time
- `TAXIING_DURATION`: 180 seconds (3 minutes) for early departure authorization

---

## File Structure & Responsibilities

### `radar.py` - Main Game Controller

**Purpose**: Central orchestrator that manages the game loop, events, and coordinates all components.

**Key Responsibilities**:
- Initialize pygame and create game window
- Load exercise configuration from JSON
- Manage game loop (60 FPS)
- Handle user input (mouse clicks, keyboard)
- Create aircraft when scheduled time arrives
- Update all models and views each frame
- Render everything to screen

**Key Attributes**:
- `aircraft_models`: List of active `AircraftModel` instances
- `all_sprites`: Pygame sprite group for visual aircraft
- `label_views`: List of `AircraftLabelView` for aircraft labels
- `ui_manager`: Context menu handler
- `side_panel`: Flight strip panel handler
- `elapsed_time`: Current simulation time

**Key Methods**:
- `run()`: Main game loop
- `request_early_departure()`: Authorize early departure for SID aircraft
- `load_exercise_data()`: Load aircraft schedule from JSON

---

### `models.py` - Aircraft State & Logic

**Purpose**: Contains the `AircraftModel` class that represents aircraft state and movement logic.

**Key Responsibilities**:
- Track aircraft position, altitude, speed
- Calculate movement along route segments
- Handle altitude changes (descent/climb)
- Manage holding patterns
- Process commands (altitude changes, holding)

**Key Attributes**:
- `moving_point`: Current pixel position `[x, y]`
- `altitude`: Current altitude in feet
- `desired_altitude`: Target altitude
- `current_speed`: Current speed in knots
- `route_name`: Name of current route
- `current_segment_index`: Which segment of route aircraft is on
- `in_holding_pattern`: Boolean flag
- `alive`: Whether aircraft should be removed

**Key Methods**:
- `update(dt)`: Main update method called each frame
  - Updates speed and distance
  - Updates position along route
  - Updates altitude
  - Handles segment transitions
- `set_desired_altitude()`: Change target altitude
- `set_pending_holding()`: Enter holding pattern
- `set_finish_holding()`: Exit holding pattern
- `get_info_for_label()`: Returns data for label display

**Movement Logic**:
1. Calculate distance traveled this frame: `speed * dt / 3600` (convert to nautical miles)
2. Interpolate position along current segment using `t_distance` (0.0 to 1.0)
3. When `t_distance >= 1.0`, move to next segment
4. Calculate altitude based on distance from descent/climb start point

---

### `views.py` - Visual Representation

**Purpose**: Handles rendering of aircraft and labels on screen.

#### `AircraftSprite`
- Pygame sprite representing aircraft as a colored circle
- Updates position from `model.moving_point` each frame
- Automatically removed when `model.alive = False`

#### `AircraftLabelView`
- Displays aircraft information (label, altitude, speed, type)
- Handles drag-and-drop interaction
- Maintains relative offset from aircraft position
- Draws connecting line from aircraft to label

**Key Methods**:
- `draw()`: Renders label with aircraft info
- `handle_input_for_drag()`: Manages mouse drag interaction
- `is_clicked()`: Checks if label was clicked

---

### `ui.py` - Context Menu System

**Purpose**: Manages the right-click context menu for aircraft commands.

**Key Responsibilities**:
- Display menu when aircraft is right-clicked
- Show different options for STAR vs SID aircraft
- Handle level input window for altitude commands
- Process keyboard input for altitude entry

**Menu Options**:
- **STAR**: "Join Holding Pattern", "Finish Holding Pattern", "Stop descent at", "Continue descent to", "disregard"
- **SID**: "Stop climb at", "continue climb to", "disregard"

**Key Methods**:
- `display_menu()`: Show context menu at position
- `process_menu_click()`: Handle menu option selection
- `display_level_input()`: Show altitude input window
- `handle_level_input_keypress()`: Process keyboard for altitude entry

---

### `panel_ui.py` - Flight Strip Panel

**Purpose**: Displays flight strips (arrival/departure information) in side panel.

**Key Components**:
- `SidePanel`: Main panel container
- `FlightStripView`: Individual flight strip display

**Key Responsibilities**:
- Show scheduled arrivals (STAR) in top half
- Show scheduled departures (SID) in bottom half
- Display status (time until arrival/departure, taxiing status)
- Handle clicks on departure strips to authorize early departure

**Strip Information**:
- Callsign (aircraft label)
- Aircraft type
- Speed
- Route name
- Status (time until event, taxiing, ready)

**Key Methods**:
- `update()`: Refresh strips based on current time and aircraft data
- `draw()`: Render all flight strips
- `handle_panel_input()`: Process clicks on strips

---

### `settings.py` - Configuration & Constants

**Purpose**: Central location for all configuration values and route data.

**Key Constants**:
- `SCREEN_WIDTH`, `SCREEN_HEIGHT`: Main radar screen dimensions
- `PANEL_WIDTH`: Side panel width
- `LAT_MIN/MAX`, `LON_MIN/MAX`: Geographic bounds for coordinate conversion
- `TAXIING_DURATION`: Time for aircraft to taxi before takeoff

**Key Functions**:
- `load_routes_from_json()`: Loads route definitions from JSON
- Converts route coordinates to pixel points
- Calculates distances between waypoints in nautical miles

**Global Variable**:
- `ROUTES`: Dictionary containing all route definitions with:
  - `coordinates`: Lat/lon waypoints
  - `pixel_points`: Converted screen coordinates
  - `distances`: Segment distances in nautical miles
  - `type`: "star" or "sid"
  - `color`: Route color for drawing
  - `altitude`: Initial altitude for route

---

### `util_funct.py` - Utility Functions

**Purpose**: Helper functions for coordinate conversion and collision detection.

**Key Functions**:
- `latlon_to_pixel()`: Convert geographic coordinates to screen pixels
- `pixel_distance_to_nm()`: Calculate distance in nautical miles between two pixel points
- `check_separations()`: Detect conflicts between aircraft (vertical and horizontal separation)

**Separation Rules**:
- Vertical: Must maintain 1000 ft separation
- Horizontal: Must maintain 10 nautical miles separation
- Critical: < 5 NM separation
- Warning: 5-10 NM separation

---

### `other_funct.py` - Additional Utilities

**Purpose**: Contains `get_exercise_input()` function for exercise selection (currently unused in main flow).

---

## Data Flow

### 1. **Initialization Flow**

```
radar.py (Game.__init__)
  ├─> Load settings.py (ROUTES, constants)
  ├─> Load exercises_config.json (aircraft schedule)
  ├─> Initialize ui_manager (ui.py)
  ├─> Initialize side_panel (panel_ui.py)
  └─> Create empty lists for models, sprites, labels
```

### 2. **Aircraft Creation Flow**

```
Game.run() loop
  ├─> Check elapsed_time >= aircraft['time']
  ├─> Create AircraftModel (models.py)
  ├─> Create AircraftSprite (views.py)
  ├─> Create AircraftLabelView (views.py)
  └─> Mark aircraft as _processed_and_killed
```

### 3. **Update Loop (Each Frame)**

```
Game.run() - 60 FPS
  │
  ├─> Process Events
  │   ├─> Mouse clicks → Select aircraft / Menu / Panel
  │   ├─> Keyboard → Altitude input
  │   └─> Label dragging
  │
  ├─> Update Models
  │   └─> For each AircraftModel:
  │       ├─> update_speed_and_distance()
  │       ├─> update_position()
  │       ├─> update_altitude_state()
  │       └─> update_segment_or_holding_logic()
  │
  ├─> Update Views
  │   ├─> all_sprites.update() (updates sprite positions)
  │   └─> side_panel.update() (refreshes flight strips)
  │
  └─> Render
      ├─> Draw routes
      ├─> Draw sprites (aircraft)
      ├─> Draw labels
      ├─> Draw UI menu
      ├─> Draw side panel
      ├─> Draw collision lines
      └─> Display time
```

### 4. **Command Flow (User Interaction)**

```
Right-click aircraft
  ├─> Game detects click on label or sprite
  ├─> Sets selected_aircraft_model
  ├─> ui_manager.display_menu()
  │
User clicks menu option
  ├─> ui_manager.process_menu_click()
  ├─> Returns action string
  │
Game processes action
  ├─> "Stop descent at" → display_level_input()
  ├─> User types altitude → Enter key
  ├─> model.set_desired_altitude(altitude)
  └─> Model calculates new descent/climb profile
```

### 5. **Early Departure Authorization Flow**

```
User clicks departure strip in panel
  ├─> panel_ui.handle_panel_input()
  ├─> FlightStripView.handle_click()
  ├─> game.request_early_departure(label)
  │
Game.request_early_departure()
  ├─> Find aircraft in aircraft_creation_data
  ├─> Check not already authorized
  ├─> Calculate new takeoff time: current_time + TAXIING_DURATION
  ├─> Update aircraft['time'] = new_takeoff_time
  ├─> Set _is_authorized_early = True
  └─> Aircraft will be created earlier than originally scheduled
```

---

## Key Interactions

### Model ↔ View Communication

**Model → View**:
- `AircraftModel.get_info_for_label()` provides data to `AircraftLabelView`
- `AircraftModel.moving_point` updates `AircraftSprite.rect.center`
- `AircraftModel.alive` determines if sprite/label should be removed

**View → Model**:
- User interactions in views trigger commands that modify model state
- Example: Right-click → menu → altitude command → `model.set_desired_altitude()`

### Game ↔ Model Communication

**Game → Model**:
- `model.update(dt)` called each frame
- Commands: `set_desired_altitude()`, `set_pending_holding()`, etc.

**Model → Game**:
- `model.alive` flag tells Game when to remove aircraft
- Model state accessed for rendering and UI display

### Game ↔ View Communication

**Game → View**:
- Creates sprites and labels from models
- Passes events for drag interaction
- Calls `draw()` methods each frame

**View → Game**:
- `label_view.is_clicked()` tells Game if label was clicked
- Drag events consumed by views prevent other interactions

### Game ↔ UI Communication

**Game → UI**:
- `ui_manager.display_menu()` when aircraft selected
- `ui_manager.display_level_input()` for altitude commands
- `ui_manager.handle_level_input_keypress()` for keyboard input

**UI → Game**:
- `ui_manager.process_menu_click()` returns action string
- `ui_manager.hide_level_input()` returns entered altitude
- `ui_manager.is_continue_descent` flag for command type

### Game ↔ Panel Communication

**Game → Panel**:
- `side_panel.update()` with current aircraft data and time
- `side_panel.draw()` to render flight strips

**Panel → Game**:
- `side_panel.handle_panel_input()` processes clicks
- `game.request_early_departure()` called from panel

---

## JSON Data Structures

### `data/routes_config.json` - Route Definitions

This file defines all available flight routes (STAR, SID, and HOLDING patterns).

**Structure**:
```json
{
  "ROUTE_NAME": {
    "coordinates": [[lat1, lon1], [lat2, lon2], ...],
    "color": [R, G, B],
    "altitude": 17000,
    "type": "star"  // or "sid" or "holding"
  }
}
```

**Fields**:
- `coordinates`: Array of `[latitude, longitude]` waypoints defining the route path
- `color`: RGB color tuple for drawing the route on screen
- `altitude`: Initial altitude for aircraft on this route (in feet)
- `type`: Route type - determines behavior:
  - `"star"`: Arrival route (aircraft descends)
  - `"sid"`: Departure route (aircraft climbs)
  - `"holding"`: Circular holding pattern

**Processing**:
- Loaded in `settings.py` via `load_routes_from_json()`
- Coordinates converted to pixel points in `util_funct.py`
- Distances between waypoints calculated using `pyproj.Geod`
- Results stored in `ROUTES` global dictionary with additional fields:
  - `pixel_points`: Screen coordinates for each waypoint
  - `distances`: Array of segment distances in nautical miles

**Example**:
```json
{
  "ESNUT2A": {
    "coordinates": [
      [7.541572011416707, -72.80482542913134],
      [7.92742, -72.51161]
    ],
    "color": [178, 190, 181],
    "altitude": 17000,
    "type": "star"
  }
}
```

---

### `data/exercises_config.json` - Exercise Scenarios

This file defines aircraft schedules for each exercise/scenario.

**Structure**:
```json
{
  "EXERCISE_NUMBER": [
    {
      "name": "ROUTE_NAME",
      "time": 0.0,
      "speed": 250,
      "label": "ABC123",
      "acft_type": "A320"
    },
    ...
  ]
}
```

**Fields**:
- `name`: Must match a route name from `routes_config.json`
- `time`: Scheduled creation time in seconds (relative to simulation start)
- `speed`: Initial speed in knots
- `label`: Aircraft callsign/identifier (displayed on label)
- `acft_type`: Aircraft type code (e.g., "A320", "B737", "ATR45")

**Internal Fields** (added by code, not in JSON):
- `_is_authorized_early`: Boolean - true if early departure authorized
- `_processed_and_killed`: Boolean - true if aircraft already created
- `_authorization_time`: Float - time when early departure was authorized

**Example**:
```json
{
  "1": [
    {
      "name": "DIMIL_star",
      "time": 0,
      "speed": 200,
      "label": "JEC5768",
      "acft_type": "A320"
    },
    {
      "name": "TORAT2A",
      "time": 300,
      "speed": 290,
      "label": "AVA9571",
      "acft_type": "A320"
    }
  ]
}
```

**Usage**:
- Exercise number selected in `radar.py` via `exercise_num_str`
- Aircraft created when `elapsed_time >= aircraft['time']`
- For SID aircraft, `time` can be modified for early departure authorization

---

## How to Extend the Code

### Adding a New Route

1. **Edit `data/routes_config.json`**:
   ```json
   {
     "NEW_ROUTE": {
       "coordinates": [[lat1, lon1], [lat2, lon2], ...],
       "type": "star",  // or "sid"
       "color": [0, 255, 0],
       "altitude": 24000
     }
   }
   ```

2. **Routes are automatically loaded** in `settings.py` and converted to pixel points

3. **Reference in `exercises_config.json`**:
   ```json
   {
     "1": [
       {
         "name": "NEW_ROUTE",
         "label": "ABC123",
         "speed": 250,
         "acft_type": "B737",
         "time": 10.0
       }
     ]
   }
   ```

### Adding a New Aircraft Command

1. **Add menu option** in `ui.py`:
   ```python
   self.star_options = [..., "New Command"]
   ```

2. **Handle in `radar.py`** (in menu click processing):
   ```python
   elif action == "New Command":
       self.selected_aircraft_model.do_new_command()
   ```

3. **Implement in `models.py`**:
   ```python
   def do_new_command(self):
       # Modify aircraft state
       pass
   ```

### Adding New Aircraft Data to Display

1. **Add to `AircraftModel.get_info_for_label()`**:
   ```python
   return {
       ...
       'new_field': self.new_attribute
   }
   ```

2. **Update `AircraftLabelView.draw()`**:
   ```python
   label_lines_text = [
       ...
       f"{model_data['new_field']}"
   ]
   ```

### Adding New Separation Rules

Edit `util_funct.py` → `check_separations()`:
- Modify vertical separation threshold (currently 1000 ft)
- Modify horizontal separation threshold (currently 10 NM)
- Add new conflict detection logic

### Adding New Exercise

1. **Edit `data/exercises_config.json`**:
   ```json
   {
     "7": [
       {
         "name": "ROUTE_NAME",
         "label": "AIRCRAFT1",
         "speed": 250,
         "acft_type": "B737",
         "time": 0.0
       }
     ]
   }
   ```

2. **Change exercise in `radar.py`**:
   ```python
   radar_game.exercise_num_str = "7"
   ```

---

## Important Notes

### Time Management
- `elapsed_time` is real-time since simulation start
- Aircraft `time` field is absolute time when aircraft should appear
- Early departure changes `time` to `current_time + TAXIING_DURATION`

### Coordinate Systems
- Routes defined in lat/lon (geographic)
- Converted to pixels at startup (stored in `pixel_points`)
- All rendering uses pixel coordinates
- Distance calculations convert back to lat/lon for accuracy

### Aircraft Removal
- Aircraft marked `alive = False` when route complete
- Game filters out dead aircraft each frame
- Sprites automatically removed via `kill()` method
- Labels check `alive` before drawing

### State Flags
- `_processed_and_killed`: Aircraft already created and removed
- `_is_authorized_early`: SID aircraft authorized for early departure
- `_authorization_time`: When early departure was authorized
- `in_holding_pattern`: Currently in holding
- `pending_holding_pattern`: Will enter holding at end of route
- `finish_holding_pattern`: Will exit holding at end of route

---

## Summary

This codebase follows a clean separation of concerns:
- **Models** handle logic and state
- **Views** handle rendering
- **Game** orchestrates everything
- **UI/Panel** handle user interaction

The key to understanding the code is following the data flow:
1. Configuration loaded → Models created → Views created
2. Each frame: Events → Model updates → View updates → Render
3. User interactions flow: View → Game → Model → View (updated display)

When adding features, identify which layer needs modification:
- **State changes** → `models.py`
- **Visual changes** → `views.py` or `ui.py` or `panel_ui.py`
- **New interactions** → `radar.py` (event handling)
- **Configuration** → JSON files or `settings.py`
