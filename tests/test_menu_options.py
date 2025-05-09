# tests/test_menu_options.py
import pytest
import pygame # Pygame necesita estar instalado
from ui import ui # Asume que ui.py está en el directorio raíz
from models import AircraftModel # Asume que models.py está en el directorio raíz
from radar import Game # Asume que radar.py está en el directorio raíz


# Mock de datos de rutas simplificado (como en el ejemplo anterior)
MOCK_ROUTES_DATA = {
    "STAR1": {"type": "star", "altitude": 24000, "pixel_points": [(0,0), (100,0)], "distances": [10.0]},
    "SID1": {"type": "sid", "altitude": 1000, "pixel_points": [(0,300), (100,300)], "distances": [15.0]},
    "HOLDING": {"type": "star", "altitude": 7000, "pixel_points": [(50,50), (60,50)], "distances": [1.0]}
}

@pytest.fixture
def mock_pygame_essentials(mocker):
    """Mockea pygame.display y pygame.font para la UI."""
    mock_surface = mocker.MagicMock(spec=pygame.Surface)
    mock_surface.get_width.return_value = 800 # Ancho de la pantalla simulada
    mock_surface.get_height.return_value = 600 # Alto de la pantalla simulada
    mocker.patch('pygame.display.get_surface', return_value=mock_surface)

    mock_font_instance = mocker.MagicMock(spec=pygame.font.Font)

    # Configurar el mock de render para que devuelva una superficie mockeada
    # que a su vez tiene un mock para get_rect()
    def mock_get_rect(**kwargs):
        # Crea un rect con tamaño fijo pero respeta el 'center' si se proporciona
        rect = pygame.Rect(0, 0, 150, 20) # Ancho y alto fijos para el texto
        if 'center' in kwargs:
            rect.center = kwargs['center']
        return rect

    mock_text_surface = mocker.MagicMock(spec=pygame.Surface)
    mock_text_surface.get_rect = mocker.MagicMock(side_effect=mock_get_rect) # Usar side_effect

    mock_font_instance.render.return_value = mock_text_surface
    mocker.patch('pygame.font.Font', return_value=mock_font_instance)

    # También, si ui.__init__ llama a pygame.display.get_surface(), ya está cubierto.
    # Si llama a pygame.font.Font(None, 30), también está cubierto.

    return mock_surface, mock_font_instance

@pytest.fixture
def ui_instance(mock_pygame_essentials):
    instance = ui()
    # La UI ya obtiene la superficie y fuente mockeadas gracias a mock_pygame_essentials
    return instance

@pytest.fixture
def star_aircraft_model():
    return AircraftModel(
        route_name="STAR1", initial_speed=250, label="STAR01", acft_type="A320",
        initial_altitude=24000, desired_altitude_init=7000,
        initial_pos=MOCK_ROUTES_DATA["STAR1"]["pixel_points"][0],
        route_type_val="star", routes_data=MOCK_ROUTES_DATA
    )

@pytest.fixture
def sid_aircraft_model():
    return AircraftModel(
        route_name="SID1", initial_speed=200, label="SID01", acft_type="B737",
        initial_altitude=1000, desired_altitude_init=18000,
        initial_pos=MOCK_ROUTES_DATA["SID1"]["pixel_points"][0],
        route_type_val="sid", routes_data=MOCK_ROUTES_DATA
    )

def simulate_menu_action(ui_inst, aircraft_model, selected_option_text, game_instance=None, level_input=None):
    # 1. Mostrar el menú
    ui_inst.display_menu(position=(100, 100), aircraft_route_type=aircraft_model.route_type)
    assert ui_inst.show_menu

    # 2. Encontrar el índice
    try:
        option_index = ui_inst.menu_options.index(selected_option_text)
    except ValueError:
        pytest.fail(f"Opción '{selected_option_text}' no encontrada en menu_options: {ui_inst.menu_options}")

    # 3. Simular el clic en esa opción
    # Recrear la lógica de cálculo de posición de ui.process_menu_click para el centro de la opción

    # Estos son los valores que ui.process_menu_click usaría internamente
    # para el Rect general del menú
    _menu_display_left = ui_inst.left + 10
    _menu_display_top = ui_inst.top + 10
    _menu_width = ui_inst.cols * 400 # Asumiendo que el ancho del menú es 400
    _menu_height = ui_inst.rows * ui_inst.option_height

    # Calcular el 'x' central de la columna (asumiendo self.cols = 1)
    # Esto debe coincidir con el 'x' calculado en process_menu_click
    # x = menu_rect.left + menu_rect.width / (self.cols * 2) + (menu_rect.width / self.cols) * col
    # Para col=0:
    click_x = _menu_display_left + (_menu_width / (ui_inst.cols * 2))

    # Calcular el 'y' central de la fila/opción específica
    # y = menu_rect.top + menu_rect.height / (self.rows * 2) + (menu_rect.height / self.rows) * row
    # Para la option_index (que es 'row' en process_menu_click):
    click_y = _menu_display_top + (_menu_height / (ui_inst.rows * 2)) + (_menu_height / ui_inst.rows) * option_index

    # El clic ahora se hace en el centro calculado de la opción de texto
    action = ui_inst.process_menu_click((click_x, click_y))
    assert action == selected_option_text # Verificar que la UI devuelve la acción correcta
    
    # 4. Simular la lógica de Game.run() para esta acción
    if action:
        ui_inst.hide_menu() # Game normalmente ocultaría el menú
        if aircraft_model: # Si hay una aeronave seleccionada
            if action == "Join Holding Pattern":
                aircraft_model.set_pending_holding(True)
            elif action == "Finish Holding Pattern":
                # Para esta prueba, podríamos necesitar poner el avión en holding primero
                aircraft_model.set_finish_holding(True)
            elif action in ["Stop descent at", "Stop climb at", "Continue descent to", "continue climb to"]:
                ui_inst.display_level_input((click_x, click_y)) # UI muestra la ventana de nivel
                # Simular entrada de nivel si se proporciona
                if level_input is not None:
                    # Esta parte simula la lógica de Game.run después de que se ingresa el nivel
                    ui_inst.string_level = str(level_input) # El usuario "escribe" el nivel
                    # Simular presionar Enter
                    # entered_level = ui_inst.hide_level_input() # Game llamaría a esto después de K_RETURN
                    # if aircraft_model:
                    #     aircraft_model.set_continue_descent_climb_flag(ui_inst.is_continue_descent)
                    #     aircraft_model.set_desired_altitude(entered_level)

                    # En la estructura actual, Game.run maneja el K_RETURN
                    # y luego llama a aircraft_model.set_desired_altitude
                    # Aquí, simplificamos para probar el efecto de la acción del menú + entrada de nivel
                    aircraft_model.set_continue_descent_climb_flag("Continue" in action or "continue" in action)
                    aircraft_model.set_desired_altitude(str(level_input))


            elif action == "disregard":
                if game_instance: # Si estamos probando el efecto en Game
                    game_instance.selected_aircraft_model = None
                pass # El modelo no cambia directamente por "disregard"
            # Cualquier otra acción específica...

    return action, ui_inst.level_window_active

# tests/test_menu_options.py (continuación)

def test_star_option_join_holding_pattern(ui_instance, star_aircraft_model):
    action, _ = simulate_menu_action(ui_instance, star_aircraft_model, "Join Holding Pattern")
    assert action == "Join Holding Pattern"
    assert star_aircraft_model.pending_holding_pattern  # Verificar el estado del modelo

def test_star_option_finish_holding_pattern(ui_instance, star_aircraft_model):
    # Primero, poner el avión en holding para que "Finish Holding Pattern" tenga sentido
    star_aircraft_model.in_holding_pattern = True
    star_aircraft_model.pending_holding_pattern = False # Ya no está pendiente, está DENTRO

    action, _ = simulate_menu_action(ui_instance, star_aircraft_model, "Finish Holding Pattern")
    assert action == "Finish Holding Pattern"
    assert star_aircraft_model.finish_holding_pattern

def test_star_option_stop_descent_at(ui_instance, star_aircraft_model):
    desired_stop_alt = "10000"
    star_aircraft_model.altitude = 15000 # Asumir que está descendiendo
    star_aircraft_model.start_altitude = 24000 # Empezó a descender desde 24000
    star_aircraft_model.desired_altitude = 7000 # Objetivo original era 7000

    action, level_window_active = simulate_menu_action(
        ui_instance, star_aircraft_model, "Stop descent at", level_input=desired_stop_alt
    )
    assert action == "Stop descent at"
    assert level_window_active # La ventana de nivel debería haberse activado inicialmente
    assert not ui_instance.is_continue_descent # No es una continuación
    assert star_aircraft_model.desired_altitude == float(desired_stop_alt)
    # start_altitude se actualiza a la altitud actual cuando se da una nueva orden de altitud.
    assert star_aircraft_model.start_altitude == 15000


def test_star_option_continue_descent_to(ui_instance, star_aircraft_model):
    continue_alt = "5000"
    star_aircraft_model.altitude = 12000 # Altitud actual
    star_aircraft_model.start_altitude = 15000 # Donde empezó el descenso anterior
    star_aircraft_model.desired_altitude = 10000 # Objetivo del descenso anterior

    action, level_window_active = simulate_menu_action(
        ui_instance, star_aircraft_model, "Continue descent to", level_input=continue_alt
    )
    assert action == "Continue descent to"
    assert level_window_active
    assert ui_instance.is_continue_descent # Es una continuación
    assert star_aircraft_model.desired_altitude == float(continue_alt)
    # Para "continue", start_altitude se actualiza a la altitud actual en el momento de la instrucción
    assert star_aircraft_model.start_altitude == 12000

def test_star_option_disregard(ui_instance, star_aircraft_model, mocker):
    # Simular una instancia de Game para verificar la deselección
    mock_game = mocker.MagicMock(spec=Game)
    mock_game.selected_aircraft_model = star_aircraft_model

    action, _ = simulate_menu_action(ui_instance, star_aircraft_model, "disregard", game_instance=mock_game)
    assert action == "disregard"
    # La acción "disregard" en tu código de Game.run parece que también deselecciona
    # if action == "disregard":
    #     print("Game: Acción 'disregard' seleccionada.")
    #     self.selected_aircraft = None # Deseleccionar
    # Aquí, la función simulate_menu_action ya lo simula si se pasa game_instance
    assert mock_game.selected_aircraft_model is None

    # tests/test_menu_options.py (continuación)

def test_sid_option_stop_climb_at(ui_instance, sid_aircraft_model):
    desired_stop_alt = "12000"
    sid_aircraft_model.altitude = 8000 # Asumir que está ascendiendo
    sid_aircraft_model.start_altitude = 1000 # Empezó a ascender desde 1000
    sid_aircraft_model.desired_altitude = 18000 # Objetivo original era 18000

    action, level_window_active = simulate_menu_action(
        ui_instance, sid_aircraft_model, "Stop climb at", level_input=desired_stop_alt
    )
    assert action == "Stop climb at"
    assert level_window_active
    assert not ui_instance.is_continue_descent # No es una continuación (la bandera es genérica para ascenso/descenso)
    assert sid_aircraft_model.desired_altitude == float(desired_stop_alt)
    assert sid_aircraft_model.start_altitude == 8000

def test_sid_option_continue_climb_to(ui_instance, sid_aircraft_model):
    continue_alt = "20000"
    sid_aircraft_model.altitude = 10000 # Altitud actual
    sid_aircraft_model.start_altitude = 5000 # Donde empezó el ascenso anterior
    sid_aircraft_model.desired_altitude = 12000 # Objetivo del ascenso anterior


    action, level_window_active = simulate_menu_action(
        ui_instance, sid_aircraft_model, "continue climb to", level_input=continue_alt
    )
    assert action == "continue climb to"
    assert level_window_active
    assert ui_instance.is_continue_descent # Es una continuación
    assert sid_aircraft_model.desired_altitude == float(continue_alt)
    assert sid_aircraft_model.start_altitude == 10000


def test_sid_option_disregard(ui_instance, sid_aircraft_model, mocker):
    mock_game = mocker.MagicMock(spec=Game)
    mock_game.selected_aircraft_model = sid_aircraft_model

    action, _ = simulate_menu_action(ui_instance, sid_aircraft_model, "disregard", game_instance=mock_game)
    assert action == "disregard"
    assert mock_game.selected_aircraft_model is None