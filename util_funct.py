from settings import *  



def latlon_to_pixel(lat, lon):
    x = int((lon - LON_MIN) / (LON_MAX - LON_MIN) * SCREEN_WIDTH)
    y = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * SCREEN_HEIGHT)
    return x, y

geod = Geod(ellps="WGS84")

for route_name, route_data in ROUTES.items():
    # Convertir listas de coordenadas de JSON de nuevo a tuplas si es necesario por pyproj
    # (pyproj usualmente maneja bien las listas para coordenadas, pero es bueno estar atento)
    coordinates_as_tuples = [tuple(coord) for coord in route_data["coordinates"]]
    route_data["coordinates"] = coordinates_as_tuples # Actualizar con tuplas si es necesario

    pixel_points = [latlon_to_pixel(lat, lon) for lat, lon in route_data["coordinates"]]
    distances = [
        geod.inv(wp1[1], wp1[0], wp2[1], wp2[0])[2] / 1852
        for wp1, wp2 in zip(route_data["coordinates"][:-1], route_data["coordinates"][1:])
    ]
    ROUTES[route_name].update({"pixel_points": pixel_points, "distances": distances})


def pixel_distance_to_nm(pos1, pos2):
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


def check_separations(aircraft_sprites_list): # Recibe la lista de AircraftSprite
    conflicts = []
    # Convertir a lista si es un grupo, o asegurar que sea una lista de sprites
    # que tengan 'model' y 'rect'

    for i in range(len(aircraft_sprites_list)):
        for j in range(i + 1, len(aircraft_sprites_list)):
            acft_sprite1 = aircraft_sprites_list[i]
            acft_sprite2 = aircraft_sprites_list[j]

            # Acceder al modelo a través del sprite para obtener la altitud
            # y asegurar que ambos modelos estén vivos
            if not acft_sprite1.model.alive or not acft_sprite2.model.alive:
                continue

            alt1 = acft_sprite1.model.altitude
            alt2 = acft_sprite2.model.altitude

            if abs(alt1 - alt2) < 1000: # Separación vertical menor a 1000ft
                # Usar los rect.center de los sprites para la distancia en píxeles
                separation_nm = pixel_distance_to_nm(acft_sprite1.rect.center, acft_sprite2.rect.center)

                if separation_nm < 10:
                    severity = "critical" if separation_nm < 5 else "warning"
                    conflicts.append({
                        'sprite1': acft_sprite1,
                        'sprite2': acft_sprite2,
                        'severity': severity,
                        'separation_nm': separation_nm
                    })
                    # print(f"Separation between {acft_sprite1.model.label} and {acft_sprite2.model.label}: {separation_nm:.2f} NM - {severity.upper()}")
    return conflicts

# La función collision_check original que dibujaba directamente puede ser eliminada o comentada.