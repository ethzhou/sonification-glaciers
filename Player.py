import pygame
import numpy as np
from utility import *

class Player:
    FADE_APPEARANCE_DURATION = 5000
    OPACITY = 80

    def __init__(self):
        self.apparent_radius = self.current_radius = self.base_radius = 96

        self.pulse_factor = 1

        self.t_fade_appearance = 0
        self.appeared = False
        
        self.grey = False

    def update(self, t_elapsed, screen, regions):
        if not self.appeared:
            if self.t_fade_appearance < Player.FADE_APPEARANCE_DURATION:
                self.t_fade_appearance += t_elapsed
            else:
                self.appeared = True

        self.position = pygame.mouse.get_pos()

        self.pulse(regions)
        self.draw(screen)

    def pulse(self, regions):
        self.pulse_factor = np.prod([np.power(region.pulse_factor, 6 / 19) for region in regions])
        
        self.apparent_radius = self.pulse_factor * self.current_radius

    def draw(self, screen):
        if not pygame.mouse.get_focused():
            return

        opacity = 1 / (1 + np.power(np.e, -4.5 * (self.t_fade_appearance / 1000 - 3.5))) * Player.OPACITY
        draw_circle(screen, (120, 120, 120, opacity) if self.grey else (240, 160, 40, opacity), self.position, self.apparent_radius)
