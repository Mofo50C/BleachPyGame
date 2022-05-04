import os
import math
import sys
import pkgutil
import importlib
import inspect

import pygame as pg
import sgc

from . import Tools
from . import game_states


class StateManager:
    def __init__(self):
        self.state_dict = {}
        self.states = []
        self.setup_states()

    def setup_states(self):
        for name, obj in inspect.getmembers(game_states, inspect.isclass):
            if issubclass(obj, Tools.State):
                self.state_dict[name.upper()] = obj()

        self.states.append(self.state_dict["TITLESCREEN"])

    def clear(self):
        while len(self.states) > 0:
            self.peek().cleanup()
            self.states.pop()

    def switch(self, name, current_time):
        persistent = self.peek().cleanup()
        if len(self.states) > 0:
            old_state = self.states.pop().__class__.__name__.upper()
        self.states.append(self.state_dict[name])
        self.peek().prev_state = old_state
        self.peek().startup(persistent, current_time)

    def push(self, name, current_time):
        persistent = self.peek().pause()
        self.states.append(self.state_dict[name])
        self.peek().startup(persistent, current_time)

    def pop(self, amount, current_time):

        for _ in range(amount):
            persistent = self.peek().cleanup()
            old_state = self.states.pop().__class__.__name__.upper()
        
        self.peek().prev_state = old_state
        self.peek().resume(persistent, current_time)
    
    def peek(self):
        return self.states[-1]


class GameEngine:
    def __init__(self):
        self.done = False
        self.screen = pg.display.get_surface()
        self.clock = pg.time.Clock()
        self.fps = 60
        self.current_time = 0.0
        self.keys = pg.key.get_pressed()
    
    @property
    def state(self):
        return self.manager.peek()

    def event_loop(self):
        for event in pg.event.get():
            sgc.event(event)
            if event.type == pg.QUIT:
                self.done = True

            self.keys = pg.key.get_pressed()

            self.state.get_event(event)

    def update(self, dt):
        self.current_time = pg.time.get_ticks()
        if self.state.quit:
            self.done = True
        elif self.state.done:
            self.switch(self.state.next_state, self.current_time)
        elif self.state.suspend:
            self.push(self.state.higher_state, self.current_time)
        elif self.state.withdraw:
            self.pop(self.state.pop_amount, self.current_time)
        self.state.update(self.screen, self.keys, self.current_time, dt)

    def run(self):
        self.manager = StateManager()
        # main loop for game
        while not self.done:
            delta_time = self.clock.tick(self.fps)
            self.event_loop()
            self.update(delta_time)
            sgc.update(delta_time)
            pg.display.update()

    def __getattr__(self, name):
        return getattr(self.manager, name)
