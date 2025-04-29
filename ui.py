from settings import *


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
                    self.acft.partial_cumulative_distance_travelled + self.acft.distance_covered_on_segment_nm
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
        