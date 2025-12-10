"""
Utility functions for coordinate conversion and collision detection.

This module provides:
- latlon_to_pixel(): Convert geographic coordinates to screen pixels
- pixel_distance_to_nm(): Calculate distance in nautical miles between pixel points
- check_separations(): Detect conflicts between aircraft

When this module is imported, it also processes the ROUTES dictionary:
- Converts route coordinates to pixel points
- Calculates distances between waypoints in nautical miles
- Updates ROUTES with 'pixel_points' and 'distances' fields
"""

from settings import *


def latlon_to_pixel(lat, lon):
    """
    Convert geographic coordinates (latitude/longitude) to screen pixel coordinates.
    
    Uses linear interpolation based on geographic bounds defined in settings.py.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Tuple (x, y) of pixel coordinates
    """
    # Convert longitude to x coordinate (0 to SCREEN_WIDTH)
    x = int((lon - LON_MIN) / (LON_MAX - LON_MIN) * SCREEN_WIDTH)
    # Convert latitude to y coordinate (0 to SCREEN_HEIGHT)
    # Note: Y is inverted (latitude increases upward, screen Y increases downward)
    y = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * SCREEN_HEIGHT)
    return x, y


# Initialize geodetic calculator for distance calculations
geod = Geod(ellps="WGS84")

# Process all routes: convert coordinates to pixels and calculate distances
# This runs when the module is imported
for route_name, route_data in ROUTES.items():
    # Convert coordinate lists to tuples (for pyproj compatibility)
    # pyproj usually handles lists fine, but tuples are safer
    coordinates_as_tuples = [tuple(coord) for coord in route_data["coordinates"]]
    route_data["coordinates"] = coordinates_as_tuples

    # Convert all waypoints to pixel coordinates
    pixel_points = [latlon_to_pixel(lat, lon) for lat, lon in route_data["coordinates"]]
    
    # Calculate distances between consecutive waypoints in nautical miles
    # geod.inv() returns (forward_azimuth, backward_azimuth, distance_in_meters)
    # We use index [2] to get distance, then convert meters to nautical miles (divide by 1852)
    distances = [
        geod.inv(wp1[1], wp1[0], wp2[1], wp2[0])[2] / 1852
        for wp1, wp2 in zip(route_data["coordinates"][:-1], route_data["coordinates"][1:])
    ]
    
    # Update route data with pixel points and distances
    ROUTES[route_name].update({"pixel_points": pixel_points, "distances": distances})


def pixel_distance_to_nm(pos1, pos2):
    """
    Calculate distance in nautical miles between two pixel points.
    
    This function:
    1. Converts pixel coordinates back to lat/lon
    2. Uses geodetic calculation (pyproj.Geod) for accurate distance
    3. Returns distance in nautical miles
    
    Args:
        pos1: First pixel position (x, y)
        pos2: Second pixel position (x, y)
        
    Returns:
        Distance in nautical miles
    """
    # Convert pixels back to lat/lon for accurate distance calculation
    lon1 = LON_MIN + (pos1[0] / SCREEN_WIDTH) * (LON_MAX - LON_MIN)
    lat1 = LAT_MAX - (pos1[1] / SCREEN_HEIGHT) * (LAT_MAX - LAT_MIN)
    lon2 = LON_MIN + (pos2[0] / SCREEN_WIDTH) * (LON_MAX - LON_MIN)
    lat2 = LAT_MAX - (pos2[1] / SCREEN_HEIGHT) * (LAT_MAX - LAT_MIN)

    # Use pyproj.Geod for accurate geodetic distance calculation
    geod = Geod(ellps="WGS84")
    # geod.inv() returns (forward_azimuth, backward_azimuth, distance_in_meters)
    _, _, distance_meters = geod.inv(lon1, lat1, lon2, lat2)

    # Convert meters to nautical miles (1 nautical mile = 1852 meters)
    distance_nm = distance_meters / 1852
    return distance_nm


def check_separations(aircraft_sprites_list):
    """
    Check separation between all aircraft and detect conflicts.
    
    Separation requirements:
    - Vertical: Aircraft must maintain >= 1000 ft altitude separation
    - Horizontal: Aircraft must maintain >= 10 nautical miles separation
    
    Conflict severity:
    - Critical: < 5 nautical miles horizontal separation
    - Warning: 5-10 nautical miles horizontal separation
    
    Args:
        aircraft_sprites_list: List of AircraftSprite objects (or pygame sprite group)
        
    Returns:
        List of conflict dictionaries, each containing:
        - sprite1: First aircraft sprite
        - sprite2: Second aircraft sprite
        - severity: "critical" or "warning"
        - separation_nm: Horizontal separation in nautical miles
    """
    conflicts = []
    
    # Compare all pairs of aircraft
    for i in range(len(aircraft_sprites_list)):
        for j in range(i + 1, len(aircraft_sprites_list)):
            acft_sprite1 = aircraft_sprites_list[i]
            acft_sprite2 = aircraft_sprites_list[j]

            # Skip if either aircraft is dead
            if not acft_sprite1.model.alive or not acft_sprite2.model.alive:
                continue

            # Get altitudes
            alt1 = acft_sprite1.model.altitude
            alt2 = acft_sprite2.model.altitude

            # Check vertical separation (must be >= 1000 ft)
            if abs(alt1 - alt2) < 1000:
                # Vertical separation insufficient - check horizontal separation
                # Calculate horizontal distance in nautical miles
                separation_nm = pixel_distance_to_nm(acft_sprite1.rect.center, acft_sprite2.rect.center)

                # Check if horizontal separation is insufficient (< 10 NM)
                if separation_nm < 10:
                    # Determine severity
                    severity = "critical" if separation_nm < 5 else "warning"
                    
                    # Add conflict to list
                    conflicts.append({
                        'sprite1': acft_sprite1,
                        'sprite2': acft_sprite2,
                        'severity': severity,
                        'separation_nm': separation_nm
                    })
    
    return conflicts
