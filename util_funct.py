from settings import *  

def latlon_to_pixel(lat, lon):
    x = int((lon - LON_MIN) / (LON_MAX - LON_MIN) * SCREEN_WIDTH)
    y = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * SCREEN_HEIGHT)
    return x, y

geod = Geod(ellps="WGS84")




for route_name, route_data in ROUTES.items():
    pixel_points = [latlon_to_pixel(lat, lon) for lat, lon in route_data["coordinates"]]
    distances = [
        geod.inv(wp1[1], wp1[0], wp2[1], wp2[0])[2] / 1852
        for wp1, wp2 in zip(route_data["coordinates"][:-1], route_data["coordinates"][1:])
    ]
    ROUTES[route_name].update({"pixel_points": pixel_points, "distances": distances})

def pixel_distance_to_nm(pos1, pos2):
    """
    Calculate the distance in nautical miles between two positions in pixels.

    Args:
        pos1 (tuple): (x, y) coordinates of the first aircraft in pixels.
        pos2 (tuple): (x, y) coordinates of the second aircraft in pixels.

    Returns:
        float: The distance between the two positions in nautical miles.
    """
    # Convert pixels back to lat/lon
    lon1 = LON_MIN + (pos1[0] / SCREEN_WIDTH) * (LON_MAX - LON_MIN)
    lat1 = LAT_MAX - (pos1[1] / SCREEN_HEIGHT) * (LAT_MAX - LAT_MIN)
    lon2 = LON_MIN + (pos2[0] / SCREEN_WIDTH) * (LON_MAX - LON_MIN)
    lat2 = LAT_MAX - (pos2[1] / SCREEN_HEIGHT) * (LAT_MAX - LAT_MIN)

    # Use pyproj.Geod to calculate distance
    geod = Geod(ellps="WGS84")
    _, _, distance_meters = geod.inv(lon1, lat1, lon2, lat2)

    # Convert meters to nautical miles
    distance_nm = distance_meters / 1852
    return distance_nm


    screen = screen
    all_sprites = sprite_group
    for acft1 in all_sprites:
        for acft2 in all_sprites:
            if acft1 != acft2:
                if abs(acft1.altitude - acft2.altitude) < 1000:
                    separation = pixel_distance_to_nm(acft1.rect.center, acft2.rect.center)
                    if separation < 10:
                        if separation < 5:
                            pygame.draw.aaline(screen, (255, 0, 0), acft1.rect.center, acft2.rect.center, 1)
                        else:
                            pygame.draw.aaline(screen, (255, 255, 0), acft1.rect.center, acft2.rect.center, 1)
                        
                        print(f"Separation: {separation:.2f} nautical miles")


def collision_check(sprite_group, screen):
    """
    Check for potential conflicts between aircraft and visualize separations on the radar.

    Args:
        sprite_group (pygame.sprite.Group): Group containing all aircraft sprites.
        screen (pygame.Surface): Pygame surface to draw conflict lines.
    """
    all_sprites = list(sprite_group)  # Convert group to list for indexed iteration
    for i, acft1 in enumerate(all_sprites):
        for j, acft2 in enumerate(all_sprites):
            if j <= i:  # Avoid duplicate comparisons
                continue
            
            # Altitude and horizontal separation check
            if abs(acft1.altitude - acft2.altitude) < 1000:
                separation = pixel_distance_to_nm(acft1.rect.center, acft2.rect.center)
                if separation < 10:
                    # Red for critical separation, yellow for warning
                    color = (255, 0, 0) if separation < 5 else (255, 255, 0)
                    pygame.draw.aaline(screen, color, acft1.rect.center, acft2.rect.center, 1)
                    print(f"Separation between {acft1.label} and {acft2.label}: {separation:.2f} NM")
