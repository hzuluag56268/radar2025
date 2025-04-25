
from settings import *
from util_funct import *
from aircraft import *
from ui import *
from other_funct import *
# Pygame initialization
pygame.init()



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
    radar.exercise_num = 1  # Set exercise number
    radar.run()

