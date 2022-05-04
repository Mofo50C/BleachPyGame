import pygame as pg
import os

from .. import Tools


class TitleScreen(Tools.State):
    def __init__(self):
        super().__init__()

        self.next_state = "MAINMENU"
        font = pg.font.Font(Tools.FONTS["kenvector_future"], 30)
        self.game_start = Tools.Label(Tools.SCREEN_RECT.centerx, Tools.SCREEN_RECT.centery + 150, 250, 100, "GAME START", font, Tools.SPACE_GREY, centred=True, blink=True)
        self.fade_outs = [self.screen_fade_out()]
        self.wrap = None

    def get_event(self, event):
        if event.type == pg.KEYUP and event.key == pg.K_RETURN:
            self.wrap = self.fade_wrapper(self.fade_outs)

    def update(self, surface, keys, current_time, delta_time):

        try:
            next(self.wrap)
        except Tools.FinishFadeOut:
            self.done = True
        except TypeError:
            self.game_start.update()
            self.draw(surface)

    def draw(self, surface):
        surface.blit(self.bg, (0, 0))
        surface.blit(self.logo, self.logo.get_rect(center=Tools.SCREEN_RECT.center))
        self.game_start.draw(surface)
