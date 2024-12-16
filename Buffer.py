import pygame
import numpy as np
from utility import *

BUFFER_DURATION = 150

class NoteRequest:

    def __init__(self, id, pitch, sampling_rate):
        self.id, self.pitch, self.sampling_rate = id, pitch, sampling_rate

        self.t_buffer = BUFFER_DURATION
        self.acknowledged = False

dtype_NoteRequest = [("id", np.int8), ("pitch", np.int16), ("sampling_rate", np.int32)]

class Buffer:

    def __init__(self, synth):
        self.synth = synth
        
        self.queue = []
        self.chamber = []

        self.impatience = 0
        self.n_waiting = 0

        self.executing = False
        self.t_last_note_played = 0
        self.spacing = 100

        self.stop_queue = False

    def update(self, t_elapsed):
        if self.executing:
            self.execute(t_elapsed)
            return

        for request in self.queue:
            if not request.acknowledged:
                self.impatience += self.n_waiting * max([request2.t_buffer for request2 in self.queue])

                if self.impatience <= request.t_buffer:
                    request.t_buffer -= self.impatience
                    request.acknowledged = True
                else:
                    self.n_waiting = len(self.queue)
                    self.prepare()
                    return

            if request.t_buffer >= 0:
                request.t_buffer -= t_elapsed
                
                if request.t_buffer < 0:
                    self.n_waiting += 1
        
        if 0 < len(self.queue) <= self.n_waiting:
            self.prepare()
    
    def prepare(self):
        if self.stop_queue:
            return
    
        self.executing = True

        due_requests = self.queue[:self.n_waiting]

        self.chamber = np.sort(np.array([(request.id, request.pitch, request.sampling_rate) for request in due_requests], dtype=dtype_NoteRequest), order="pitch")

        self.queue = self.queue[self.n_waiting:]

        self.impatience = 0
        self.n_waiting = 0

    def execute(self, t_elapsed):
        
        if self.t_last_note_played < self.spacing:
            self.t_last_note_played += t_elapsed
        else:
            self.play_request(self.chamber[0])

            self.chamber = self.chamber[1:]

            if not len(self.chamber):
                self.executing = False
            
            self.t_last_note_played = 0

    def play_request(self, request):
        print(f"Player chamber request {request}")
        
        pygame.mixer.Channel(request["id"]).play(
            self.synth(request["pitch"], duration=1.6, sampling_rate=request["sampling_rate"], volume=.1))
