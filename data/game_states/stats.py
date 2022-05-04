import pygame as pg
import os

from .. import Tools


class StatsMenu(Tools.State):
    def __init__(self):
        super().__init__()
        self.next_state = "MAINMENU"

    def get_event(self, event):
        if event.type in [pg.KEYDOWN, pg.KEYUP] and event.key in Tools.PLAYER1_CONTROLS:
            if event.type == pg.KEYUP and Tools.PLAYER1_CONTROLS[event.key] == "JUMP":
                self.wrap = self.fade_wrapper(self.fade_outs)

    def update(self, surface, keys, current_time, delta_time):
        try:
            self.fade_caller()
        except TypeError:
            if not self.user:
                self.persist["P#"] = 1
                self.higher_state = "LOGIN"
                self.suspend = True
            self.draw(surface)
            
    def draw(self, surface):
        surface.blit(self.bg, (0, 0))
        surface.blit(self.panel, (40, 40))
        surface.blit(self.board, (Tools.SCREEN_SIZE[0] - 600 - 40, 40))
    
    def create_stats_panel(self):
        stats = Tools.MASTER_DB.get_user_stats(self.user).fetchone()
        self.panel.fill((*Tools.BLACK, 200))
    
        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 40)
        title = font.render("STATS", True, Tools.SPACE_GREY)
        self.panel.blit(title, title.get_rect(center=(400 // 2, 30)))

        pg.draw.line(self.panel, Tools.SPACE_GREY, (400 // 2 - title.get_width(), 20 + title.get_height()), (400 // 2 + title.get_width(), 20 + title.get_height()), 7)
        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 32)
        user_name = font.render(stats[7].upper(), True, Tools.SPACE_GREY)
        self.panel.blit(user_name, (50, 100))

        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 25)
        stat_names = "wins, losses, draws, highscore, date, max combo, total games"
        for i, (name, stat) in enumerate(zip(stat_names.split(", "), stats)):
            text = Tools.Text(50, 150 + (i * 50), name.upper() + ": " + str(stat), font, Tools.SPACE_GREY)
            text.draw(self.panel)
    
    def create_leader(self):
        self.board.fill((*Tools.BLACK, 200))

        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 40)
        title = font.render("LEADERBOARD", True, Tools.SPACE_GREY)
        self.board.blit(title, title.get_rect(center=(600 // 2, 30)))
        pg.draw.line(self.board, Tools.SPACE_GREY, (600 // 2 - title.get_width() + 40, 20 + title.get_height()), (600 // 2 + title.get_width() - 40, 20 + title.get_height()), 7)
        
        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 25)
        for i, row in enumerate(Tools.MASTER_DB.get_leaderboard()):
            text = font.render(row[0] + ": " + str(row[1]), True, Tools.SPACE_GREY)
            date = font.render(str(row[2]), True, Tools.SPACE_GREY)
            self.board.blit(text, (40, 100 + (i * 30)))
            self.board.blit(date, (600 - date.get_width() - 40, 100 + (i * 30)))

    def startup(self, persistent, current_time):
        super().startup(persistent, current_time)
        self.wrap = self.fade_wrapper(self.fade_ins)
        self.user = None
        self.panel = pg.Surface((400, 800)).convert_alpha()
        self.panel.fill((*Tools.BLACK, 0))
        self.board = pg.Surface((600, 880)).convert_alpha()
        self.board.fill((*Tools.BLACK, 0))

    def resume(self, persistent, current_time):
        super().resume(persistent, current_time)
        self.user = self.persist["UUID"]
        self.create_stats_panel()
        self.create_leader()
