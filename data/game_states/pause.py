import pygame as pg
import os

from .. import Tools


class PauseMenu(Tools.State):
    def __init__(self):
        super().__init__()
        self.next_state = "ENDSCREEN"
        self.trans_bg = pg.Surface(Tools.SCREEN_SIZE).convert_alpha()
        self.trans_bg.fill((0, 0, 0, 50))

        self.font = pg.font.Font(Tools.FONTS["kenvector_future"], 40)

        self.choice_names = ["BACK", "EXIT"]

        self.create_menu()

        self.cursor = Tools.MenuPointer(Tools.SPACE_GREY, self.choices)

        self.dalpha = 15

    def get_event(self, event):
        if event.type in [pg.KEYUP, pg.KEYDOWN] and (
            event.key in Tools.PLAYER1_CONTROLS
        ):
            if event.type == pg.KEYUP and Tools.PLAYER1_CONTROLS[event.key] == "LIGHT":
                btn = self.cursor.click()
                if btn == "BACK":
                    self.withdraw = True
                    self.persist["EXIT_NOSAVE"] = False
                elif btn == "EXIT":
                    self.withdraw = True
                    self.persist["EXIT_NOSAVE"] = True

            if event.type == pg.KEYDOWN:
                if Tools.PLAYER1_CONTROLS[event.key] == "UP":
                    self.cursor.index.x -= 1

                elif Tools.PLAYER1_CONTROLS[event.key] == "DOWN":
                    self.cursor.index.x += 1

    def update(self, surface, keys, current_time, delta_time):
        self.cursor.update()
        self.draw(surface)

    def draw(self, surface):
        surface.blit(self.old_screen, (0, 0))
        surface.blit(self.trans_bg, (0, 0))
        surface.blit(
            self.menu_background,
            self.menu_background.get_rect(
                center=(Tools.SCREEN_SIZE[0] // 2, Tools.SCREEN_SIZE[1] // 2)
            ),
        )

        for choice in self.choices[0]:
            choice.draw(surface)

        self.cursor.draw(surface)

    def create_menu(self):
        self.menu_background = pg.Surface((500, 350)).convert_alpha()
        self.menu_background.fill((0, 0, 0, 200))

        self.title = self.font.render("PAUSED", True, Tools.SPACE_GREY).convert_alpha()
        title_rect = self.title.get_rect(
            midtop=(self.menu_background.get_rect().centerx, self.menu_background.get_rect().top + 20))
        self.menu_background.blit(self.title, title_rect)

        line_rect = pg.Rect(
            self.menu_background.get_rect().x + 125,
            self.menu_background.get_rect().y + 70,
            250,
            2,
        )
        pg.draw.rect(self.menu_background, Tools.SPACE_GREY, line_rect)

        self.choices = [[]]
        x_offset = Tools.SCREEN_RECT.centerx
        y_offset = Tools.SCREEN_RECT.centery - 175

        for i, name in enumerate(self.choice_names):
            self.choices[0].append(Tools.NamedBtn(name, x_offset, y_offset + ((i + 1) * 120 + 35), name, self.font, Tools.SPACE_GREY, Tools.BLACK, 0, 500))

    def startup(self, persistent, current_time):
        super().startup(persistent, current_time)
        self.old_screen = pg.display.get_surface().copy()
        self.cursor.index.x = 0
