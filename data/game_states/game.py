import pygame as pg
import pygame.gfxdraw as pgfx
import os
import math
from .. import Tools


class Stage:
    def __init__(self):
        self.solid_colour = (231, 206, 82)
        self.bg = pg.transform.scale(Tools.GFX["stage/bg"], Tools.SCREEN_SIZE)
        self.fg = pg.transform.scale(Tools.GFX["stage/fg"], (1280, 540))
        self.stage_surface = pg.Surface((Tools.SCREEN_SIZE))
        self.stage_surface.blit(self.bg, (0, 0))
        self.stage_surface.blit(self.fg, (0, 320))
        pg.draw.rect(self.stage_surface, self.solid_colour, pg.Rect(0, 860, Tools.SCREEN_SIZE[0], 100))
        self.floor = 720

    def draw(self, surface):
        surface.blit(self.stage_surface, (0, 0))


class Player(pg.sprite.Sprite):
    def __init__(self, char, num, x, y):
        super().__init__()
        self.num = num
        self.char_name = char.NAME
        self.char_thumb = char.THUMB
        self.char_portrait = char.PORTRAIT
        self.char = char.main(self.num, Tools.CONTROLS[self.num - 1], x, y)
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.win = False
    
    def update(self, keys, current_time, delta_time):
        self.char.update(keys, current_time, delta_time)
        if self.pos.x < 0:
            self.pos.x = 0
        elif self.pos.x > (Tools.SCREEN_SIZE[0] + 60 - self.image.get_width()):
            self.pos.x = (Tools.SCREEN_SIZE[0] + 60 - self.image.get_width())

        if self.combo > self.max_combo:
            self.max_combo = self.combo

        self.image = self.char.image
        self.rect = self.char.rect
        self.mask = self.char.mask
    
    def get_name(self):
        return self.char_name
    
    def get_thumb(self):
        return self.char_thumb
    
    def get_portrait(self):
        return self.char_portrait

    def lose_hp(self, num):
        self.hp -= num
    
    def gain_hp(self, num):
        self.hp += num

    def gain_energy(self, num):
        self.energy += num

    def lose_energy(self, num):
        self.energy -= num

    def hit(self):
        self.char.hit_count += 1
        if ((self.char.hit_count % 4) == 0) and (self.char.hit_count != 0):
            self.char.hit_count += 1
        
        self.char.hit_count %= 4

    def is_aerial(self):
        return True if self.status == "AERIAL" else False

    def is_ground(self):
        return True if self.status == "GROUND" else False

    def is_attack(self):
        return True if self.status == "ATTACK" else False
    
    def is_special(self):
        return True if self.status == "SATTACK" else False

    def is_hit(self):
        return True if self.status == "HIT" else False

    def is_knocked(self):
        return True if self.status == "KNOCKED" else False

    def is_guard(self):
        return True if self.status == "GUARD" else False
    
    def is_vulnerable(self):
        return self.is_aerial() or self.is_ground() or self.is_hit()
    
    def __getattr__(self, name):
        return getattr(self.char, name)


class PlayerInfo:
    def __init__(self, player):
        self.player = player
        self.max_hp = 1000
        self.max_energy = 300
        self.width = 520
        self.height = 150
        self.hp_w = 400
        self.y_off = 20
        self.x_off = 20
        self.surf = pg.Surface((self.width, self.height)).convert_alpha()
        self.surf.fill((0, 0, 0, 0))
        self.pointer = pg.Surface((50, 40)).convert_alpha()
        self.pointer.fill((0, 0, 0, 0))
        self.pointer_colour = None
        self.win = False

    def update(self):
        self.hp_w = (400 / self.max_hp) * (self.player.hp)
        if self.player.num == 1:
            self.pointer_colour = Tools.PLAYER_1_BLUE
        else:
            self.pointer_colour = Tools.PLAYER_2_PURPLE

    def draw(self, surface):
        pgfx.aapolygon(self.surf, [(70, 5), (520, 5), (500, 45), (50, 45)], Tools.SPACE_GREY)
        pgfx.filled_polygon(self.surf, [(70, 5), (520, 5), (500, 45), (50, 45)], Tools.SPACE_GREY)
        pgfx.box(self.surf, pg.Rect(100, 11, 400, 28), (75, 75, 75))
        if self.hp_w > 0:
            pgfx.box(self.surf, pg.Rect(100, 11, self.hp_w, 28), (0, 128, 0))
        pgfx.aacircle(self.surf, 70, 74, 70, Tools.SPACE_GREY)
        pgfx.filled_circle(self.surf, 70, 74, 70, Tools.SPACE_GREY)
        pgfx.aacircle(self.surf, 70, 74, 60, Tools.NICE_GREY)
        pgfx.filled_circle(self.surf, 70, 74, 60, Tools.NICE_GREY)

        self.surf.blit(self.player.get_thumb(), self.player.get_thumb().get_rect(center=(70, 74)))

        pgfx.aatrigon(self.pointer, 0, 0, 50, 0, 25, 30, self.pointer_colour)
        pgfx.filled_trigon(self.pointer, 0, 0, 50, 0, 25, 30, self.pointer_colour)

        if self.player.num == 1:
            surface.blit(self.surf, (self.x_off, self.y_off))
        elif self.player.num == 2:
            surface.blit(pg.transform.flip(self.surf, True, False), (Tools.SCREEN_SIZE[0] - self.x_off - self.width, self.y_off))
        
        surface.blit(self.pointer, self.pointer.get_rect(midbottom=(self.player.rect.centerx, self.player.rect.top - 20)))


class GameState(Tools.State):
    def __init__(self):
        super().__init__()
        self.next_state = "ENDSCREEN"
        self.higher_state = "PAUSEMENU"
        self.stage = Stage()
        self.players = pg.sprite.Group()

    def get_event(self, event):
        if event.type in [pg.KEYUP, pg.KEYDOWN]:
            if event.type == pg.KEYUP and event.key == pg.K_ESCAPE:
                self.suspend = True
            else:
                for player in self.players:
                    player.get_event(event)

    def update(self, surface, keys, current_time, delta_time):
        try:
            self.fade_caller()
        except TypeError:
            if not self.end_game:
                self.players.update(keys, current_time, delta_time)
                self.main_collisions()
                self.clac_scores()
                self.check_game_end(current_time)

                for i in self.infos:
                    i.update()
            else:
                if (current_time - self.end_time) > 2000:
                    self.next_state = "ENDSCREEN"
                    self.wrap = self.fade_wrapper(self.fade_outs)

            self.draw(surface)
    
    def main_collisions(self):
        if self.player_1.is_attack() and self.player_2.is_attack():
            if self.player_1.attack_time > self.player_2.attack_time:
                if pg.sprite.collide_mask(self.player_1, self.player_2):
                    self.player_2.lose_hp(self.player_1.dmg)
                    self.player_2.hit()
            elif self.player_2.attack_time > self.player_1.attack_time:
                if pg.sprite.collide_mask(self.player_2, self.player_1):
                    self.player_1.lose_hp(self.player_2.dmg)
                    self.player_1.hit()
        elif self.player_1.is_attack() and self.player_2.is_vulnerable():
            if pg.sprite.collide_mask(self.player_1, self.player_2):
                self.player_2.lose_hp(self.player_1.dmg)
                self.player_2.hit()
        elif self.player_2.is_attack() and self.player_1.is_vulnerable():
            if pg.sprite.collide_mask(self.player_2, self.player_1):
                self.player_1.lose_hp(self.player_2.dmg)
                self.player_1.hit()
    
    def check_game_end(self, current_time):
        if self.player_2.hp <= 0:
            self.winner = self.player_1
            self.loser = self.player_2
            self.player_1.win = True
            self.end_game = True
            self.end_time = current_time
        elif self.player_1.hp <= 0:
            self.winner = self.player_2
            self.loser = self.player_1
            self.player_2.win = True
            self.end_game = True
            self.end_time = current_time
    
    def clac_scores(self):
        self.player_1.combo = self.player_2.hit_count
        self.player_2.combo = self.player_1.hit_count

        for p in self.players:
            p.score += 0.2 * p.combo
            p.score = round(p.score)

    def draw(self, surface):
        self.stage.draw(surface)
        self.players.draw(surface)
        for i in self.infos:
            i.draw(surface)

        if self.end_game:
            font = pg.font.Font(Tools.FONTS["kenvector_future"], 50)
            label = Tools.Label(Tools.SCREEN_RECT.centerx, Tools.SCREEN_RECT.centery, 1280, 50, "GAME OVER!", font, Tools.SPACE_GREY, (0, 0, 0, 150), centred=True)
            label.draw(surface)

    def startup(self, persistent, current_time):
        super().startup(persistent, current_time)
        self.start_time = current_time
        self.wrap = self.fade_wrapper(self.fade_ins)
        self.player_1 = Player(self.persist["CHAR1"], 1, 100, self.stage.floor)
        self.player_2 = Player(self.persist["CHAR2"], 2, 1180, self.stage.floor)
        self.players.add(self.player_1)
        self.players.add(self.player_2)
        self.infos = [PlayerInfo(self.player_1), PlayerInfo(self.player_2)]
        self.winner = None
        self.loser = None
        self.end_game = False
        self.end_time = None
        self.persist["EXIT_NOSAVE"] = False

    def resume(self, persistent, current_time):
        super().resume(persistent, current_time)
        if self.persist["EXIT_NOSAVE"]:
            self.wrap = self.fade_wrapper(self.fade_outs)
            self.next_state = "MAINMENU"

    def cleanup(self):
        self.players.empty()
        if not self.persist["EXIT_NOSAVE"]:
            self.persist["PLAYERS"] = (self.winner, self.loser)
        else:
            self.persist["EXIT_NOSAVE"] = False
        return super().cleanup()
