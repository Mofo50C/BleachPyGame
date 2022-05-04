import pygame as pg
import os

from .. import Tools


class MainMenu(Tools.State):
    def __init__(self):
        super().__init__()
        self.next_state = "CHARSELECT"

        self.font = pg.font.Font(Tools.FONTS["kenvector_future"], 40)

        self.choice_names = ["PLAY", "STATS", "QUIT"]

        self.create_menu()

        self.pointer = Tools.MenuPointer(Tools.SPACE_GREY, self.buttons)
 
    def get_event(self, event):
        if event.type in [pg.KEYDOWN, pg.KEYUP] and event.key in Tools.PLAYER1_CONTROLS:
            if event.type == pg.KEYUP and Tools.PLAYER1_CONTROLS[event.key] == "LIGHT":
                btn = self.pointer.click()
                if btn == "play":
                    self.next_state = "CHARSELECT"
                    self.wrap = self.fade_wrapper(self.fade_outs)
                elif btn == "stats":
                    self.next_state = "STATSMENU"
                    self.wrap = self.fade_wrapper(self.fade_outs)
                elif btn == "quit":
                    self.quit = True

            if event.type == pg.KEYDOWN:

                if Tools.PLAYER1_CONTROLS[event.key] == "UP":
                    self.pointer.index.x -= 1

                if Tools.PLAYER1_CONTROLS[event.key] == "DOWN":
                    self.pointer.index.x += 1

    def update(self, surface, keys, current_time, delta_time):

        try:
            self.fade_caller()
        except TypeError:
            self.pointer.update()
            self.draw(surface)

    def draw(self, surface):
        surface.blit(self.bg, (0, 0))
        surface.blit(self.logo, self.logo_rect)
        surface.blit(self.menu, (0, Tools.SCREEN_RECT.centery - 15))
        for choice in self.buttons[0]:
            choice.draw(surface)
        self.pointer.draw(surface)
        
    def create_menu(self):
        self.menu = pg.Surface((Tools.SCREEN_RECT.w, 300)).convert_alpha()
        self.menu.fill((0, 0, 0, 116))

        self.buttons = [[]]
        x_offset = Tools.SCREEN_RECT.centerx
        y_offset = Tools.SCREEN_RECT.centery

        for i, name in enumerate(self.choice_names):
            self.buttons[0].append(Tools.NamedBtn(name.lower(), x_offset, y_offset + ((i + 1) * 70), name, self.font, Tools.SPACE_GREY, Tools.BLACK, 0, Tools.SCREEN_SIZE[0]))

    def logo_anim(self):
        for j in range(15):
            self.logo_rect.centery -= 15
            Tools.SCREEN.blit(self.bg, (0, 0))
            Tools.SCREEN.blit(self.logo, self.logo_rect)
            yield

    def startup(self, persistent, current_time):
        super().startup(persistent, current_time)
        self.fade_ins = [self.screen_fade_in(), self.logo_anim()]
        self.wrap = self.fade_wrapper(self.fade_ins)
        self.pointer.index.x = 0
        self.logo_rect = self.logo.get_rect(center=Tools.SCREEN_RECT.center)
