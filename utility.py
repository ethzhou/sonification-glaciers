import pygame
import numpy as np

def change_mixer_sampling_rate(new_sampling_rate):
    pygame.mixer.quit()
    pygame.mixer.init(new_sampling_rate)
    pygame.mixer.set_num_channels(20)
    
    print(pygame.mixer.get_init())

def draw_circle(surface, color, center, radius):
    rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    subsurface = pygame.Surface(rect.size, pygame.SRCALPHA)

    pygame.draw.circle(subsurface, color, (radius, radius), radius)
    surface.blit(subsurface, rect)

def draw_text(surface, font, text, antialias, color, position, coordinates_indicate_bottom_right=False, coordinates_indicate_center=False):
    subsurface = font.render(text, antialias, color)
    rect = subsurface.get_rect()
    if coordinates_indicate_bottom_right:
        rect.bottomright = position
    elif coordinates_indicate_center:
        rect.center = position
    else:
        rect.topleft = position

    surface.blit(subsurface, rect)

def sonification_curve_1(t, a, b, c, vertically_shift_to_origin=True):
    return a * (1 / (1 + np.exp(-b * (t - c))) + (- 1 / (1 + np.exp(b * c)) if vertically_shift_to_origin else 0))
