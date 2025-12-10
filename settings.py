"""
Settings and configuration constants.

This module contains:
- Screen dimensions and panel width
- Geographic bounds for coordinate conversion
- Route loading from JSON
- Global ROUTES dictionary with all route definitions

The ROUTES dictionary is populated at module import time by loading
routes_config.json and converting coordinates to pixel points.
"""

import pygame
import time
from pyproj import Geod
import json

# Screen dimensions
PANEL_WIDTH = 350  # Width of side panel for flight strips
SCREEN_WIDTH = 650  # Width of main radar screen
SCREEN_HEIGHT = 700  # Height of screen

# Geographic bounds for coordinate conversion
# These define the lat/lon area displayed on the radar screen
LAT_MIN = 7.3  # Minimum latitude
LAT_MAX = 8.61  # Maximum latitude
LON_MIN = -73.08  # Minimum longitude
LON_MAX = -72.35  # Maximum longitude

# Taxiing duration constant (also defined in radar.py for consistency)
# Duration in seconds for aircraft to taxi before takeoff when early departure is authorized
TAXIING_DURATION = 180  # 3 minutes in seconds


def load_routes_from_json(file_path):
    """
    Load route definitions from JSON file.
    
    Routes are defined in routes_config.json with:
    - coordinates: Array of [latitude, longitude] waypoints
    - color: RGB color tuple for drawing route
    - altitude: Initial altitude for aircraft on this route
    - type: "star" (arrival), "sid" (departure), or "holding"
    
    Args:
        file_path: Path to routes_config.json
        
    Returns:
        Dictionary of route definitions
    """
    with open(file_path, 'r') as f:
        routes_data = json.load(f)
    
    # Convert color lists from JSON to tuples (Pygame needs tuples)
    for route_name, route_info in routes_data.items():
        if "color" in route_info and isinstance(route_info["color"], list):
            route_info["color"] = tuple(route_info["color"])
    
    return routes_data


# Load routes from JSON file
# This is executed at module import time
ROUTES = load_routes_from_json('data/routes_config.json')

# Note: Route coordinates are converted to pixel points and distances are calculated
# in util_funct.py when that module is imported. The ROUTES dictionary is then
# updated with 'pixel_points' and 'distances' fields.
