import pygame
import csv
import numpy as np
import time
from GlacierRegion import GlacierRegion
from Player import Player
from Buffer import Buffer
from utility import *

print(f"pygame=={pygame.ver}, numpy=={np.version.version}")


MIXER_SAMPLING_RATE = 22050

pygame.mixer.pre_init(MIXER_SAMPLING_RATE)
pygame.init()

pygame.mixer.set_num_channels(20)

print(pygame.mixer.get_init())

font = pygame.font.Font('assets/fonts/Thasadith/Thasadith-Regular.ttf', 24)
font_smaller = pygame.font.Font('assets/fonts/Thasadith/Thasadith-Regular.ttf', 20)
font_smaller_2 = pygame.font.Font('assets/fonts/Thasadith/Thasadith-Regular.ttf', 15)
font_knowledgeable = pygame.font.Font('assets/fonts/Noto Serif JP/NotoSerifJP-Light.ttf', 134)
font_slender = pygame.font.Font('assets/fonts/Alumni Sans Pinstripe/AlumniSansPinstripe-Regular.ttf', 40)
font_end = pygame.font.Font('assets/fonts/Waterfall/Waterfall-Regular.ttf', 27)


N_REGIONS = 19

with open("assets/region_info.csv") as file:
    reader = csv.reader(file, delimiter=",", quotechar="\"")
    data = [data for data in reader]
REGION_INFO = np.asarray(data, dtype=None)

REGION_INFO = REGION_INFO[1:]

with open("assets/data/Regional_B_mwe_series_year_1976-2023.csv", "r") as file:
    reader = csv.reader(file, delimiter=",", quotechar="\"")
    data = [data for data in reader]
B_SERIES = np.asarray(data, dtype=None)

with open("assets/data/Regional_DM_Gt_series_year_1976-2023.csv", "r") as file:
    reader = csv.reader(file, delimiter=",", quotechar="\"")
    data = [data for data in reader]
DM_SERIES = np.asarray(data, dtype=None)

B_SERIES = B_SERIES[62:].T
DM_SERIES = DM_SERIES[62:].T

TUNING_STANDARD = 440

IMAGE_BLANK_MAP = pygame.image.load("assets/blank_map1.png")

FPS = 60
WIDTH = 1200
HEIGHT = 800

global_volume = 1

timer = pygame.time.Clock()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sonification: Glacier Mass Balance")


def piano_curve(frequency, t, duration=None):
    w = 2 * np.pi * frequency

    y = 0.6 * np.sin(1 * w * t)
    y += 0.4 * np.sin(2 * w * t)
    y *= np.exp(-0.0015 * 600 * t)
    y += np.power(y, 3)
    # y *= 1 + 16 * t * np.exp(-6 * t)
    
    y *= 2 / (1 + np.exp(1 * (t - duration))) - 1 if duration else 1

    return y

def synth(frequency, duration=2, curve=piano_curve, sampling_rate=MIXER_SAMPLING_RATE, volume=1.0, fit_to_mixer_sampling_rate=True):
    time_i = time.perf_counter()


    n_samples = int(np.ceil(duration * sampling_rate))

    timings = np.linspace(0, duration, n_samples)

    samples = np.vectorize(curve)(frequency, timings, duration)
    samples /= np.max(np.abs(samples))
    

    sound_array = np.asarray([32767 * samples, 32767 * samples]).T.astype(np.int16)

    time_f = time.perf_counter()
    print(f"synth took {time_f - time_i} seconds to generate array of {len(sound_array)} samples (frequency {frequency}, duration {duration}, sampling_rate {sampling_rate})")

    if fit_to_mixer_sampling_rate:
        n_samples_fit_mixer = int(duration * MIXER_SAMPLING_RATE)
        sound_array = sound_array[np.floor(sampling_rate / MIXER_SAMPLING_RATE * np.arange(1, n_samples_fit_mixer + 1) - 1).astype(int)]

    time_f = time.perf_counter()
    print(f"synth took {time_f - time_i} seconds total to generate final array of {len(sound_array)} samples (frequency {frequency}, duration {duration}, sampling_rate {sampling_rate})")

    sound = pygame.sndarray.make_sound(sound_array.copy())

    adjusted_volume = volume * np.power(7 / np.log2(frequency), 3.7)
    print(f"setting audio volume to {adjusted_volume} (frequency {frequency}, volume {volume})")
    sound.set_volume(adjusted_volume)

    return sound


pitches = np.zeros(19)
STEP = np.power(2, 1 / 12)

# A
pitches[5] = TUNING_STANDARD / 2
pitches[10] = TUNING_STANDARD
pitches[15] = TUNING_STANDARD * 2
# G-sharp
pitches[9] = TUNING_STANDARD / STEP
pitches[14] = pitches[9] * 2
pitches[18] = pitches[9] * 4
# F-sharp
pitches[8] = pitches[9] / STEP ** 2
pitches[1] = pitches[8] / 8
pitches[2] = pitches[8] / 4
pitches[4] = pitches[8] / 2
pitches[13] = pitches[8] * 2
# E
pitches[7] = pitches[8] / STEP ** 2
pitches[12] = pitches[7] * 2
pitches[17] = pitches[7] * 4
# C-sharp
pitches[6] = pitches[7] / STEP ** 3
pitches[3] = pitches[6] / 2
pitches[11] = pitches[6] * 2
pitches[16] = pitches[6] * 4
# E-sharp
pitches[0] = pitches[1] / STEP ** 2

player = Player()
buffer = Buffer(synth)

regions = np.asarray([
    GlacierRegion(
        int(REGION_INFO[i][0]), 
        REGION_INFO[i][1], 
        (int(REGION_INFO[i][2]), int(REGION_INFO[i][3])), 
        dict(zip(B_SERIES[0].astype(int), B_SERIES[i+1].astype(float))),
        dict(zip(DM_SERIES[0].astype(int), DM_SERIES[i+1].astype(float))),
        float(REGION_INFO[i][4]),
        pitches[i])
    for i in range(N_REGIONS)])

year = 1975  # The game will instantly increment year in the first loop
YEAR_DURATION = 10000
t_year = YEAR_DURATION + 1
region_has_been_added_to_year = np.repeat(False, 19)
global_cumulative_dm = 0

count_additions = 0

displayed_stat = "dm"

image_blank_map_rect = IMAGE_BLANK_MAP.get_rect()
image_blank_map_rect.center = screen.get_rect().center

text_active_year = f"{year}"
text_active_cumulative = "+0.000 Gt"

id_region_active_text = None
text_active_region_name = ""
text_active_region_data = ""
color_text_active_region_data = (0, 0, 0, 0)
text_active_region_cumulative = ""

t_end = 0
end_surface = pygame.Surface((WIDTH, HEIGHT))
end_surface.fill((0, 0, 0))

stage = 0
game = True
while game:
    timer.tick(FPS)
    t_elapsed = timer.get_time()
    
    screen.fill((255, 255, 255))
    screen.blit(IMAGE_BLANK_MAP, image_blank_map_rect)

    draw_text(screen, font_knowledgeable, text_active_year, False, (210, 210, 230, 60), (WIDTH / 2, HEIGHT / 2 - 50), coordinates_indicate_center=True)
    draw_text(screen, font_slender, text_active_cumulative, False, (210, 210, 230, 60), (WIDTH / 2, HEIGHT / 2 + 30), coordinates_indicate_center=True)
    
    draw_text(screen, font, text_active_region_name, False, (40, 56, 140, 60), (WIDTH - 60, 80), coordinates_indicate_bottom_right=True)
    draw_text(screen, font_smaller_2, text_active_region_data, False, color_text_active_region_data, (WIDTH - 60, 102), coordinates_indicate_bottom_right=True)
    draw_text(screen, font_smaller, text_active_region_cumulative, False, (100, 120, 220, 60), (WIDTH - 60, 122), coordinates_indicate_bottom_right=True)

    for region in regions:
        region.update(t_elapsed, screen)

    player.update(t_elapsed, screen, regions)
    buffer.update(t_elapsed)

    match stage:
        case 0:
            if player.appeared:
                stage += 1

        case 1:
            t_year += t_elapsed
            # t_cumulative_addition += t_elapsed

            if t_year > YEAR_DURATION:
                if (year == 2023):
                    buffer.stop_queue = True
                    player.grey = True
                    stage += 1
                else:
                    if year > 1975:
                        i_due_regions = np.asarray(~region_has_been_added_to_year)
                        global_cumulative_dm += np.sum([region.dm_series[year] for region in regions[i_due_regions]])
                        count_additions += sum(i_due_regions)

                    region_has_been_added_to_year = np.repeat(False, 19)
                    year += 1

                    for region in regions:
                        region.cumulative_b += region.b_series[year]
                        region.cumulative_dm += region.dm_series[year]

                        region.recognize_year_change()

                    text_active_year = f"{year}"
                    
                    t_year = 0

            i_due_regions = np.asarray(~region_has_been_added_to_year & (t_year > np.arange(19) / 19 * YEAR_DURATION))
            global_cumulative_dm += np.sum([region.dm_series[year] for region in regions[i_due_regions]])
            region_has_been_added_to_year[i_due_regions] = True
            count_additions += sum(i_due_regions)

            text_active_cumulative = f"{global_cumulative_dm:+.3f} Gt"
            
            for region in regions:
                collision_result = region.check_player_collision(t_elapsed, player, MIXER_SAMPLING_RATE)

                if collision_result:
                    buffer.queue.append(collision_result)

                    region = regions[collision_result.id - 1]

                    id_region_active_text = region.id
                    text_active_region_name = f"{region.name}"
                    text_active_region_data = f"({f"{region.b_series[year]:+.3f} m w.e." if displayed_stat == "b" else f"{region.dm_series[year]:+.3f} Gt"})"
                    color_text_active_region_data = (230, 170, 200, 60) if region.b_series[year] < 0 else (180, 230, 220, 60)
                    text_active_region_cumulative = f"{region.cumulative_b:+.3f} m w.e." if displayed_stat == "b" else f"{region.cumulative_dm:+.3f} Gt"

        case 2:
            t_end += t_elapsed
            if t_end > 4600:
                t_end = 0
                stage += 1
        
        case 3:
            screen.blit(end_surface, (0, 0))

            t_end += t_elapsed

            if t_end > 7000:
                stage += 1
            elif t_end > 1800:
                draw_text(end_surface, font_smaller_2, "Ethan Zhou", False, (255, 255, 255), (WIDTH - 50, HEIGHT - 35), coordinates_indicate_bottom_right=True)
            
        case _:
            game = False
            



    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False

        if event.type == pygame.MOUSEWHEEL:
            player.current_radius = np.clip(player.current_radius - event.precise_y, 8, 520)
            print(player.current_radius)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                print("switching displayed stat")
                displayed_stat = "dm" if displayed_stat == "b" else "b"

                if year > 1975 and id_region_active_text:
                    text_active_region_data = f"({f"{region.b_series[year]:+.3f} m w.e." if displayed_stat == "b" else f"{region.dm_series[year]:+.3f} Gt"})"
                    text_active_region_cumulative = f"{region.cumulative_b:+.3f} m w.e." if displayed_stat == "b" else f"{region.cumulative_dm:+.3f} Gt"
            
            if event.key == pygame.K_n:
                if stage == 1:
                    t_year = YEAR_DURATION + 1
    
    pygame.display.flip()

print("count additions", count_additions)
pygame.quit()
