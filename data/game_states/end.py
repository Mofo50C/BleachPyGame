import pygame as pg
import os
import pygame.gfxdraw as pgfx
import sgc
import datetime

from .. import Tools

class EndScreen(Tools.State):
    def __init__(self):
        super().__init__()
        self.next_state = "MAINMENU"

        self.font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 20)
        self.font2 = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 30)
        self.font3 = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 40)
        
        grid = [[{"name": "Save P1", "label": "Save", "pos": (250 + 40, 650), "w": 500}, {"name": "Save P2", "label": "Save", "pos": (1280 - 250 - 40, 650), "w": 500}],
                [{"name": "Exit", "label": "Exit", "pos": (80, 960 - 60), "w": 100}]]
        
        self.buttons = self.create_buttons(grid)

        self.pointer = Tools.MenuPointer(Tools.SPACE_GREY, self.buttons)

    def get_event(self, event):
        if event.type in [pg.KEYDOWN, pg.KEYUP] and event.key in Tools.PLAYER1_CONTROLS:
            if event.type == pg.KEYUP and Tools.PLAYER1_CONTROLS[event.key] == "LIGHT":
                btn = self.pointer.click()
                if btn == "Exit":
                    self.next_state = "MAINMENU"
                    self.wrap = self.fade_wrapper(self.fade_outs)
                elif btn == "Save P1":
                    if self.users[0] is None:
                        self.higher_state = "LOGIN"
                        self.suspend = True
                        self.persist["P#"] = 1
                    else:
                        self.save(self.users[0], self.players[0])
                elif btn == "Save P2":
                    if self.users[1] is None:
                        self.higher_state = "LOGIN"
                        self.suspend = True
                        self.persist["P#"] = 2
                    else:
                        self.save(self.users[1], self.players[1])
            
            if event.type == pg.KEYDOWN:
                if Tools.PLAYER1_CONTROLS[event.key] == "UP":
                    self.pointer.index.y -= 1
                elif Tools.PLAYER1_CONTROLS[event.key] == "DOWN":
                    self.pointer.index.y += 1
                elif Tools.PLAYER1_CONTROLS[event.key] == "LEFT":
                    self.pointer.index.x += 1
                elif Tools.PLAYER1_CONTROLS[event.key] == "RIGHT":
                    self.pointer.index.x -= 1

                    

    def update(self, surface, keys, current_time, delta_time):
        try:
            self.fade_caller()
        except TypeError:
            self.pointer.update()
            self.draw(surface)
        
    def save(self, user, player):
        stats = Tools.MASTER_DB.get_user_stats(user).fetchone()
        if player.win:
            wins = stats[0] + 1
            losses = stats[1]
        else:
            losses = stats[1] + 1
            wins = stats[0]
        draws = stats[2]
        if player.score > stats[3]:
            high_score = player.score
            date = datetime.date.today()
        else:
            high_score = stats[3]
            date = stats[4]
        if player.combo > stats[5]:
            max_combo = player.combo
        else:
            max_combo = stats[5]

        games_played = stats[6] + 1

        Tools.MASTER_DB.update_stats(user, wins, losses, draws, high_score, date, max_combo, games_played)

    def draw(self, surface):
        surface.blit(self.bg, (0, 0))
        panels = self.make_player_panel(surface)
        surface.blit(panels[0], (40, 40))
        surface.blit(panels[1], (1280 - 40 - 500, 40))
        for l in self.buttons:
            for button in l:
                button.draw(surface)
        self.pointer.draw(surface)
    
    def create_buttons(self, grid):
        temp = []
        for l in grid:
            row = []
            for button in l:
                row.append(Tools.NamedBtn(button["name"], button["pos"][0], button["pos"][1], button["label"], self.font2, Tools.SPACE_GREY, Tools.BLACK, 0, button["w"]))

            temp.append(row)

        return temp

    def make_player_panel(self, surface):
        panels = []
        for player in self.players:
            panel = pg.Surface((500, 650)).convert_alpha()
            panel.fill((*Tools.BLACK, 150))
            x = 40
            y = player.get_portrait().get_height() + 60
            name = Tools.Text(x, y, player.get_name(), self.font, Tools.SPACE_GREY)
            score = Tools.Text(x, y + 40, "Score: " + str(player.score), self.font, Tools.SPACE_GREY)
            combo = Tools.Text(x, y + 60, "Combo: " + str(player.combo), self.font, Tools.SPACE_GREY)

            if player.win:
                winner = self.font3.render("Winner", True, Tools.SPACE_GREY)
                panel.blit(winner, winner.get_rect(midtop=(250, 10)))
                port = player.get_portrait()
            else:
                port = pg.transform.flip(player.get_portrait(), True, False)
            
            panel.blit(port, port.get_rect(midtop=(250, 50)))
        
            name.draw(panel)
            score.draw(panel)
            combo.draw(panel)

            panels.append(panel)
        
        return panels

    def startup(self, persistent, current_time):
        super().startup(persistent, current_time)
        self.wrap = self.fade_wrapper(self.fade_ins)
        self.users = [None, None]
        self.players = self.persist["PLAYERS"]

    def resume(self, persistent, current_time):
        super().resume(persistent, current_time)
        self.users[self.persist["P#"] - 1] = self.persist["UUID"]

    def cleanup(self):
        return super().cleanup()
