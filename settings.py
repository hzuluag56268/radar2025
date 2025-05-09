import pygame
import time
from pyproj import Geod
import json 

# settings.py
PANEL_WIDTH = 250
SCREEN_WIDTH = 650
SCREEN_HEIGHT = 700
LAT_MIN = 7.3
LAT_MAX = 8.61
LON_MIN = -73.08
LON_MAX = -72.35

# settings.py

def load_routes_from_json(file_path):
    with open(file_path, 'r') as f:
        routes_data = json.load(f)
    # Convertir listas de colores de JSON de nuevo a tuplas si Pygame las necesita así
    for route_name, route_info in routes_data.items():
        if "color" in route_info and isinstance(route_info["color"], list):
            route_info["color"] = tuple(route_info["color"])
    return routes_data
ROUTES = load_routes_from_json('data/routes_config.json') # <<<--- Cargar desde JSON
