import pygame
import time
from pyproj import Geod
from settings import *
# Pygame initialization
pygame.init()



class ui():
    def __init__(self, ):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 30)
        self.left = 0 
        self.top = 0
        self.cols = 1
        self.route_name = None
        self.option_height = 25
        self.show_menu = False
        self.acft = None
        self.level_window_active = False
        self.string_level = ""
        self.update_level = False
        self.is_continue_descent = False
        self.is_star = None 
        self.star_options =  ["Join Holding Pattern", "Finish Holding Pattern", "Stop descent at","Continue descent to", "disregard"]
        self.sid_options = ["Stop climb at", "continue climb to ", "disregard"]
        
        self.menu_options =  None
        self.rows = None

    def get_input(self, text_rect,i):

        if  text_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            if self.menu_options[i] == "Join Holding Pattern":
                self.show_menu = False
                self.acft.pending_holding_pattern = True
            if self.menu_options[i] == "Finish Holding Pattern":
                self.acft.finish_holding_pattern = True
                self.show_menu = False
            if self.menu_options[i] == "Stop descent at":
                self.show_menu = False
                self.level_window_active = True
                self.string_level = ""     
            if self.menu_options[i] == "Continue descent to":
                self.level_window_active = True
                self.show_menu = False
                self.string_level = ""     
                self.is_continue_descent = True
            if self.menu_options[i] == "disregard":
                self.show_menu = False
            if self.menu_options[i] == "Stop climb at":
                print("stop climb at")
                self.show_menu = False
                self.level_window_active = True
                self.string_level = ""     
            if self.menu_options[i] == "continue climb to ":
                self.level_window_active = True
                self.show_menu = False
                self.string_level = ""     
                self.is_continue_descent = True
                print("continue climb to ")
    def show_level(self):
        
        if self.level_window_active: 
            rect2 = pygame.Rect(0, 0 , 400,25)
            pygame.draw.rect(self.display_surface, (0, 0, 0),rect2, 0, 4) 
            pygame.draw.rect(self.display_surface, (0, 0,80),rect2, 4, 4)

            text_surf2 = self.font.render(f"level: {self.string_level}", True, (0, 255, 0))        
            text_rect2 = text_surf2.get_rect(center = (rect2.centerx,rect2.centery))
            self.display_surface.blit(text_surf2, text_rect2)
        
    def update(self):
        if self.update_level:
             if self.is_continue_descent:
                self.acft.start_altitude = self.acft.altitude
                self.acft.cumulative_distance_to_last_descent = \
                    self.acft.partial_cumulative_distance_travelled + self.acft.cumulative_segment_distance
                self.is_continue_descent = False
                print(f"start altitude updated to {self.acft.start_altitude}")

             self.acft.desired_altitude = int(self.string_level)
             self.update_level = False
            
             print("level updated to ", self.acft.desired_altitude)

    def draw(self):
        if self.is_star:
            self.menu_options = self.star_options
            self.rows = len(self.menu_options)
        else:
            self.menu_options = self.sid_options
            self.rows = len(self.menu_options)    

        if self.level_window_active:
            self.show_level()
        # bg
        if not self.show_menu:
            return
        # Dynamic placement (ensure label stays within the screen bounds)
                
        if self.left + 10 + self.cols * 400 > self.display_surface.get_width():
            self.left -= 10 + self.cols * 400
        if self.top + 10 + self.rows * self.option_height > self.display_surface.get_height():
            self.top -= 10 + self.rows * self.option_height
        rect = pygame.Rect(self.left + 10, self.top + 10 ,self.cols * 400, self.rows * self.option_height)
        pygame.draw.rect(self.display_surface, (0, 0, 0),rect, 0, 4)
        pygame.draw.rect(self.display_surface, (0, 80, 0),rect, 4, 4)
        # Draw menu options
        for col in range(self.cols):
            for row in range(self.rows):
                x = rect.left + rect.width / (self.cols * 2) + (rect.width / self.cols) * col
                y = rect.top + rect.height / (self.rows * 2) + (rect.height / self.rows) * row
                i = row  
                text_surf = self.font.render(self.menu_options[i], True, (0, 255, 0))
                text_rect = text_surf.get_rect(center = (x,y))
                self.display_surface.blit(text_surf, text_rect)
                self.get_input(text_rect,i) 
        
        
class Aircraft(pygame.sprite.Sprite):
    def __init__(self, groups, color, route_name, speed,label, screen, ui, acft_type):  # Added `label` parameter
        super().__init__(groups)
        self.route_name = route_name
        self.route_type = ROUTES[self.route_name]["type"]
        self.start_pos = ROUTES[self.route_name]["pixel_points"][0]
        self.radius = 8
        self.color = color
        self.label = label  # Added to store a unique identifier for the aircraft
        self.creation_time = time.time()
        self.start_segment_time = time.time()
        self.speed = speed
        self.acft_type = acft_type
        self.cumulative_distance_to_last_descent = 0
        self.partial_cumulative_distance_travelled = 0
        self.cumulative_distance_travelled = 0
        self.cumulative_segment_distance = 0
        self.current_segment = 0
        self.current_segment_distance_nm = 0
        self.ui = ui
        self.altitude =self.start_altitude = ROUTES[self.route_name]['altitude']
        self.desired_altitude = 6000 if ROUTES[self.route_name]["type"] == "star" else 24000
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center= self.start_pos)
        self.moving_point = ROUTES[self.route_name]["pixel_points"][0]
        self.descent_rate = 333  # feet per nautical mile
        self.in_holding_pattern = False
        self.pending_holding_pattern = False
        self.finish_holding_pattern = False
        self.screen = screen
        self.label_offset = (15, -20)  # Default offset for the label relative to the aircraft
        self.dragging_label = False  # Track whether the label is being dragged


    def interpolate(self, p1, p2, t):
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        return (x, y)

    def calculate_altitude(self, cumulative_distance_from_last_descent, start_altitude, desired_altitude):
        if ROUTES[self.route_name]["type"] == "star":
            return max(start_altitude - (cumulative_distance_from_last_descent * self.descent_rate), desired_altitude)    
        else:
            return min(start_altitude + (cumulative_distance_from_last_descent * self.descent_rate), desired_altitude)
    #
    def draw_label(self, screen, font, icon=None):
        """
        Draws a radar-style label with each piece of information displayed on a separate line.
        """
        # Define radar-green color
        radar_green = (0, 255, 0)
        background_color = (0, 50, 0)  # Dark green for the rectangle background

        # Aircraft data for the label
        label_lines = [
            f"{self.label}",             # Aircraft identifier
            f"{self.altitude/100:.0f}00 ft",  # Current altitude
            #f"{self.speed} kts",      # Aircraft speed
            f"{self.acft_type}"
        ]

        # Render each line of text
        rendered_lines = [font.render(line, True, radar_green) for line in label_lines]

        # Calculate the size of the label box
        line_height = rendered_lines[0].get_height()
        text_width = max(line.get_width() for line in rendered_lines)
        text_height = len(rendered_lines) * line_height + 6  # Add spacing between lines
        padding = 10
        rect_width = text_width + 2 * padding
        rect_height = text_height + padding

        # Determine the label's position relative to the aircraft
        if not self.dragging_label:
            # Calculate position relative to the aircraft
            rect_x = self.rect.centerx + self.label_offset[0]
            rect_y = self.rect.centery + self.label_offset[1]
        else:
            # Maintain the label position while dragging
            rect_x, rect_y = self.label_position

        # Dynamic placement to ensure label stays within screen bounds
        rect_x = max(0, min(rect_x, screen.get_width() - rect_width))
        rect_y = max(0, min(rect_y, screen.get_height() - rect_height))
        self.label_position = (rect_x, rect_y)

        # Draw a thin line connecting the label to the aircraft
        pygame.draw.line(screen, radar_green, self.rect.center, (rect_x + rect_width / 2, rect_y), 1)

        # Draw the rounded rectangle background
        pygame.draw.rect(
            screen,
        background_color,
            (rect_x, rect_y, rect_width, rect_height),
            border_radius=8
        )

        # Draw the rectangle border
        pygame.draw.rect(
            screen,
            radar_green,
            (rect_x, rect_y, rect_width, rect_height),
            width=2,
            border_radius=8
        )

        # Blit each line of text onto the rectangle
        for i, line_surface in enumerate(rendered_lines):
            line_y = rect_y + padding + i * line_height  # Position each line below the previous one
            screen.blit(line_surface, (rect_x + padding, line_y))

        # Handle mouse events for dragging and selection
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        label_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

        if mouse_pressed[0]:  # Left mouse button is pressed
            if label_rect.collidepoint(mouse_pos) and not self.dragging_label:
                # Start dragging when clicking on the label
                self.dragging_label = True
                self.drag_offset = (rect_x - mouse_pos[0], rect_y - mouse_pos[1])
            elif self.dragging_label:
                # Update label position while dragging
                self.label_position = (mouse_pos[0] + self.drag_offset[0], mouse_pos[1] + self.drag_offset[1])
                # Update the offset relative to the aircraft
                self.label_offset = (self.label_position[0] - self.rect.centerx,
                                     self.label_position[1] - self.rect.centery)
        elif mouse_pressed[2]:  # Right mouse button is pressed
            if label_rect.collidepoint(mouse_pos):
                # Right-click selects the aircraft
                self.acft_selected()
        else:
            # Stop dragging when the mouse button is released
            self.dragging_label = False
            # Update the offset relative to the aircraft
            self.label_offset = (self.label_position[0] - self.rect.centerx,
                                 self.label_position[1] - self.rect.centery)
    def acft_selected(self):
        if self.ui.show_menu:
            return
        print(" route type ", self.route_type, "ui star", self.ui.is_star)
        self.ui.is_star = self.route_type == "star"
        self.ui.left = self.rect.centerx
        self.ui.top = self.rect.centery
        print(" route type ", self.route_type, "ui star", self.ui.is_star)     

        self.ui.show_menu = True
        
        self.ui.acft = self
        

    def update(self):
        #self.get_input()
        
        p1, p2 = ROUTES[self.route_name]["pixel_points"][self.current_segment], \
                 ROUTES[self.route_name]["pixel_points"][self.current_segment + 1]
        self.current_segment_distance_nm = ROUTES[self.route_name]["distances"][self.current_segment]
        time_required_sec = (self.current_segment_distance_nm / self.speed) * 3600
        segment_elapsed = time.time() - self.start_segment_time
        t = min(segment_elapsed / time_required_sec, 1)
        self.moving_point = self.interpolate(p1, p2, t)
        self.rect.center = self.moving_point
        self.cumulative_segment_distance = t * self.current_segment_distance_nm
        self.cumulative_distance_travelled = \
            (self.partial_cumulative_distance_travelled + self.cumulative_segment_distance) - \
            self.cumulative_distance_to_last_descent
        self.altitude = \
            self.calculate_altitude(self.cumulative_distance_travelled, self.start_altitude, self.desired_altitude)

        if t >= 1:
            self.partial_cumulative_distance_travelled += self.current_segment_distance_nm
            self.current_segment += 1
            self.start_segment_time = time.time()
            if self.current_segment >= len(ROUTES[self.route_name]["pixel_points"]) - 1:
                if self.in_holding_pattern and self.finish_holding_pattern:
                    self.kill()
                elif not self.in_holding_pattern and self.pending_holding_pattern:
                    self.in_holding_pattern = True
                    self.current_segment = 0
                    self.route_name = "HOLDING"
                elif not self.in_holding_pattern and not self.pending_holding_pattern:
                    self.kill()
                elif self.in_holding_pattern:
                    self.current_segment = 0
        
        self.draw_label(self.screen, pygame.font.Font(None, 24))
        
geod = Geod(ellps="WGS84")

def latlon_to_pixel(lat, lon):
    x = int((lon - LON_MIN) / (LON_MAX - LON_MIN) * SCREEN_WIDTH)
    y = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * SCREEN_HEIGHT)
    return x, y


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

def get_exercise_input(screen, font):
    input_active = True
    user_text = ""
    input_rect = pygame.Rect(200, 300, 250, 50)
    color_active = (0, 255, 0)
    color_inactive = (255, 255, 255)
    color = color_inactive

    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    input_active = True
                    color = color_active
                else:
                    color = color_inactive
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try:
                        exercise_num = int(user_text)
                        if exercise_num in range(5):
                            return exercise_num
                        else:
                            user_text = "Invalid! Enter 0-4."
                    except ValueError:
                        user_text = "Invalid! Enter 0-4."
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                elif event.unicode.isdigit():
                    user_text += event.unicode

        screen.fill((0, 0, 0))  # Clear screen
        pygame.draw.rect(screen, color, input_rect, 2)  # Draw input box

        text_surface = font.render(user_text, True, (255, 255, 255))
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))  # Display text in the box

        prompt_text = font.render("Enter exercise number (0-4):", True, (255, 255, 255))
        screen.blit(prompt_text, (200, 250))  # Display prompt text

        pygame.display.flip()  # Update the display

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


class Game:
    def __init__(self):
        print('ejercicio 0')
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Radar Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)  # Added font for aircraft labels
        self.running = True
        
        self.elapsed_time = 0
        self.all_sprites = pygame.sprite.Group()
        
        self.ui = ui()
        self.level_str = ""
        self.exercise_num = 1
        self.Aircraft = Aircraft
        #self.exercise_num = input("Enter the exercise number: ")
        #print(f"Exercise number: {self.exercise_num}")
        self.aircraft_timers = {
                                0 : [
                                    {'name':'UMPEX1A', 'time':0, 'speed':240, 'label':'EFY9070','acft_type':'ATR45'},
                                    {'name':'DIMIL6A', 'time':0, 'speed':180, 'label':'JEC5678','acft_type':'A320'},
                                    {'name':'ESNUT2B', 'time':0, 'speed':290, 'label':'AVA9321','acft_type':'A320'},
                                    {'name':'DIMIL_star', 'time':0, 'speed':250, 'label':'CMP9345','acft_type':'B737'},
                                    {'name':'ESNUT2A', 'time':1, 'speed':290, 'label':'AVA9571','acft_type':'A320'}
                                ], 
                                1 : [
                                    {'name':'DIMIL_star', 'time':0, 'speed':200, 'label':'JEC5768','acft_type':'A320'},
                                    {'name':'TORAT2A', 'time':120, 'speed':250, 'label':'AVA9321','acft_type':'A320'},
                                    {'name':'DIMIL_star', 'time':240, 'speed':180, 'label':'FAC5078','acft_type':'C208'},
                                    {'name':'TORAT2A', 'time':300, 'speed':290, 'label':'AVA9571','acft_type':'A320'},
                                    {'name':'UMPEX1A', 'time':360, 'speed':260, 'label':'EFY9070','acft_type':'ATR45'}

                                ],
                                2 : [
                                    {'name':'TORAT2A', 'time':0, 'speed':200, 'label':'EFY9070','acft_type':'ATR45'},
                                    {'name':'UMPEX1A', 'time':0, 'speed':290, 'label':'JEC5678','acft_type':'A320'},
                                    {'name':'ESNUT2B', 'time':240, 'speed':180, 'label':'HK5020','acft_type':'PA34'},
                                    {'name':'TORAT2A', 'time':420, 'speed':250, 'label':'CMP9345','acft_type':'B737'},
                                    {'name':'DIMIL6A', 'time':480, 'speed':290, 'label':'AVA9571','acft_type':'A320'}
                                ],
                                3 : [
                                    {'name':'TORAT2A', 'time':0, 'speed':180, 'label':'PNC2044','acft_type':'SW4'},
                                    {'name':'ESNUT2A', 'time':0, 'speed':290, 'label':'AVA9321','acft_type':'A320'},
                                    {'name':'UMPEX1A', 'time':120, 'speed':260, 'label':'EFY9070','acft_type':'ATR45'},
                                    {'name':'DIMIL_star', 'time':180, 'speed':260, 'label':'CMP9345','acft_type':'B737'},
                                    {'name':'ESNUT2B', 'time':240, 'speed':180, 'label':'HK5020','acft_type':'PA34'}

                                ],
                                4 : [
                                    {'name':'TORAT2A', 'time':0, 'speed':260, 'label':'AVA9321','acft_type':'A320'},
                                    {'name':'ESNUT2B', 'time':60, 'speed':260, 'label':'JEC5678','acft_type':'A320'},
                                    {'name':'TORAT2A', 'time':120, 'speed':200, 'label':'EFY9070','acft_type':'ATR45'}, 
                                    {'name':'DIMIL6A', 'time':180, 'speed':200, 'label':'JEC5470','acft_type':'A320'},
                                    {'name':'UMPEX1A', 'time':240, 'speed':200, 'label':'PNC2044','acft_type':'SW4'}
                                ]
                                }

    def display_time(self):
    # Calculate elapsed time in minutes and seconds
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        # Render the time
        time_text = self.font.render(f"Time  00 : {minutes} : {seconds:02d} ", True, (0, 255, 0))
        
        # Position the text on the screen
        self.screen.blit(time_text, (10, 10))  # Adjust position as needed
    
    
    def run(self):
        start_time = time.time()  # Initialize start time
        while self.running:
            self.elapsed_time =  time.time() - start_time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    
                    if self.ui.level_window_active:
                        
                        if event.key == pygame.K_RETURN:  # Confirm input
                            print("key return pressed")
                            self.ui.level_window_active = False
                            self.ui.update_level = True
                        elif event.key == pygame.K_BACKSPACE:  # Remove last character
                            self.ui.string_level = self.ui.string_level[:-1]
                        elif event.unicode.isdigit():  # Add digit to input
                            self.ui.string_level += event.unicode
            
            for acft in self.aircraft_timers[self.exercise_num][:]:
                if self.elapsed_time >= acft['time']:
                    self.Aircraft(self.all_sprites, (0, 100, 0),acft['name'],acft['speed'] ,\
                                  acft['label'],self.screen,self.ui,acft['acft_type'])
                    self.aircraft_timers[self.exercise_num].remove(acft)
            
            self.screen.fill((0, 0, 0))

            for route_name, route_data in ROUTES.items():
                route_label = self.font.render(f"{route_name} ", True, (0, 255, 0))
                if route_data["type"] == "star" and route_name != "DIMIL_star":
                    self.screen.blit(route_label, route_data["pixel_points"][0] )
                if route_data["type"] == "sid":
                    self.screen.blit(route_label, route_data["pixel_points"][-1] )
                for i in range(len(route_data["pixel_points"]) - 1):
                    pygame.draw.aaline(self.screen, route_data["color"], route_data["pixel_points"][i], route_data["pixel_points"][i + 1], 1)
                    
            self.all_sprites.update()
            self.all_sprites.draw(self.screen)
            self.ui.update()
            self.ui.draw()

            
            self.display_time()
            collision_check(self.all_sprites, self.screen)
            pygame.display.update()

        pygame.quit()

if __name__ == '__main__':
    #pygame.init()  # Initialize Pygame
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    font = pygame.font.Font(None, 36)

    # Get exercise input
    #exercise_num = get_exercise_input(screen, font)

    # Pass the exercise number to the Game instance
    radar = Game()
    radar.exercise_num = 0 # Set exercise number
    radar.run()

