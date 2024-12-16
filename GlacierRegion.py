import pygame
import numpy as np
from utility import *
from Buffer import NoteRequest

import random
from datetime import datetime

random.seed(datetime.now().timestamp())

class GlacierRegion:

    def __init__(self, id, name, position, b_series, dm_series, approximate_area, pitch):
        self.id, self.name, self.position, self.b_series, self.dm_series, self.approximate_area, self.pitch = id, name, position, b_series, dm_series, approximate_area, pitch

        self.apparent_radius = self.current_radius = self.base_radius = 4 * np.power(approximate_area, 1 / 4)
        
        self.pulse_factor = 1
        self.pulse_duration = 7500

        self.pulse_strength = .4
        self.pulse_frequency = 12
        self.pulse_temporal_extent = 1200
        self.pulse_abruptness = 3.8

        self.t_since_last_fire = 0
        self.refractory_period_duration = 1800

        self.cumulative_b = 0
        self.cumulative_dm = 0

        self.sonification_stretch = 0

    def recognize_year_change(self):
        self.current_radius = ((sonification_curve_1(np.sqrt(-self.cumulative_b), 8, 1, 5.7)
            if self.cumulative_b < 0
            else sonification_curve_1(np.sqrt(self.cumulative_b), .6, -2, 1))
                + 1) * self.base_radius

    def update(self, t_elapsed, screen):
        self.sonification_stretch = np.sign(self.cumulative_b) * (np.sqrt(np.abs(self.cumulative_b) + 1) - 1)

        self.pulse(t_elapsed, self.pulse_strength, self.pulse_frequency, self.pulse_temporal_extent, self.pulse_abruptness)
        self.draw(screen)

    def pulse(self, t_elapsed, strength=.4, frequency=12, temporal_extent=1200, abruptness=3.8):
        self.pulse_factor = 1 if self.t_since_last_fire > self.pulse_duration else 1 + strength * np.sin(frequency * self.t_since_last_fire / temporal_extent) / (np.power(self.t_since_last_fire / temporal_extent, abruptness) + 1)
        
        self.t_since_last_fire += t_elapsed

        self.apparent_radius = self.pulse_factor * self.current_radius
    
    def draw(self, screen):
        opacity = int(90 * (1 / np.exp(-self.sonification_stretch / 3 + np.log(2)))) + 30
        color = (100, 74, 255, opacity) if self.t_since_last_fire < self.refractory_period_duration else (30, 164, 255, opacity)

        draw_circle(screen, color, self.position, max(6, self.apparent_radius))

    def check_player_collision(self, t_elapsed, player, mixer_sampling_rate):
        if self.t_since_last_fire < self.refractory_period_duration:
            return
        
        if not pygame.mouse.get_focused() or not pygame.mouse.get_visible():
            return

        if player.apparent_radius + self.apparent_radius < np.linalg.norm(np.asarray(player.position) - np.asarray(self.position)):
            return
        

        # collision

        player_speed = np.linalg.norm(pygame.mouse.get_rel()) / t_elapsed
        
        self.pulse_strength = np.clip(.015 * player_speed, .1, .3)
        self.pulse_frequency = max(16, 1.2 * player_speed)
        self.pulse_temporal_extent = np.clip(150 * player_speed, 1000, 3000)
        # print(self.pulse_strength, self.pulse_temporal_extent, "are the strength and the temporal extent. unclipped, they are", 0.06 * player_speed, 900 * player_speed)
        
        self.t_since_last_fire = 0

        pitch = (1 + np.power(2, random.random() * sonification_curve_1(self.sonification_stretch, 4.3, .6, -4))) * self.pitch
        sampling_rate = max(1, int(sonification_curve_1(self.sonification_stretch, 1, 1.4, -1.8, False) * mixer_sampling_rate))

        return NoteRequest(self.id, pitch, sampling_rate)
