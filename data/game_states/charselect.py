import pygame as pg
import os

from .. import Tools


class Grid:
    def __init__(self, x_dim, y_dim, bg, alpha, x, y, slot_w, slot_h, slot_bg, characters, font, gap=0, outline=None, outline_colour=None):
        self.x = x
        self.y = y
        self.width = x_dim * slot_w + (x_dim - 1) * gap
        self.height = y_dim * slot_h + (y_dim - 1) * gap
        self.image = pg.Surface((self.width, self.height)).convert_alpha()
        self.image.fill((*bg, alpha))
        self.grid = []
        index = 0
        if (x_dim * y_dim) > len(characters):
            for _ in range((x_dim * y_dim) - len(characters)):
                characters.append(None)
        else:
            characters = characters[:(x_dim * y_dim)]

        for i in range(1, y_dim * 2, 2):
            row = []
            for counter, (j, c) in enumerate(zip(range(1, x_dim * 2, 2), characters[index:]), 1):
                
                X = j * ((slot_w + gap) // 2)
                Y = i * ((slot_h + gap) // 2)

                row.append(
                    Slot(
                        slot_w,
                        slot_h,
                        gap,
                        X,
                        Y,
                        slot_bg,
                        c,
                        outline,
                        outline_colour,
                    )
                )

                row[-1].draw(self.image)
           
            index = counter
            self.grid.append(row)
        
        text = font.render("P1", True, Tools.PLAYER_1_BLUE).convert_alpha()
        self.pointer1 = Pointer(slot_w + 8, slot_h + 8, Tools.PLAYER_1_BLUE, self.grid, self.x - self.width // 2, self.y - self.height // 2, text, "left")
        text = font.render("P2", True, Tools.PLAYER_2_PURPLE).convert_alpha()
        self.pointer2 = Pointer(slot_w + 8, slot_h + 8, Tools.PLAYER_2_PURPLE, self.grid, self.x - self.width // 2, self.y - self.height // 2, text, "right")

    def draw(self, surface):
        surface.blit(self.image, self.image.get_rect(center=(self.x, self.y)))
        self.pointer1.draw(surface)
        self.pointer2.draw(surface)


class Slot:
    def __init__(self, w, h, gap, x, y, bg, char, outline=None, outline_colour=None):
        self.gap = gap
        self.width = w
        self.height = h
        self.x = x
        self.y = y
        self.colour = bg
        self.char = char
        self.image = pg.Surface((self.width, self.height)).convert_alpha()
        self.image.fill(bg)
        if outline:
            outline = (outline * 2) + 1
            pg.draw.rect(self.image, outline_colour, (0, 0, self.width, self.height), outline)
        if self.char:
            self.image.blit(self.char.THUMB, self.char.THUMB.get_rect(center=(self.width // 2, self.height // 2)))

    def draw(self, surface):
        surface.blit(self.image, (self.x - ((self.width + self.gap) // 2), self.y - ((self.height + self.gap) // 2)))


class Pointer:
    def __init__(self, w, h, colour, slots, x_off, y_off, text, side):
        self.show = True
        self.width = w
        self.height = h
        self.colour = colour
        self.slots = slots
        self.x_off = x_off
        self.y_off = y_off
        self.index = (0, 0)
        self.image = pg.Surface((self.width, self.height)).convert_alpha()
        self.image.fill((0, 0, 0, 0))
        pg.draw.rect(self.image, self.colour, (0, 0, self.width, self.height), 9)
        self.align = side
        self.text = text

    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, tup):
        self._index = Tools.VEC(tup)
    
    def toggle(self):
        self.show = not self.show
    
    def get_slot(self):
        y = int(self.index.y) % len(self.slots)
        x = int(self.index.x) % len(self.slots[y])
        return self.slots[y][x]
    
    def draw(self, surface):
        if self.show:
            slot = self.get_slot()
            x = (slot.x - ((self.width - slot.width) // 2)) + self.x_off
            y = (slot.y - ((self.height - slot.height) // 2)) + self.y_off
            rect = self.image.get_rect(center=(x, y))
            surface.blit(self.image, rect)
            if self.align == "right":
                rect = self.text.get_rect(bottomright=(rect.right + 5, rect.top - 10))
            else:
                rect = self.text.get_rect(bottomleft=(rect.left, rect.top - 10))
            surface.blit(self.text, rect)


class CharSelect(Tools.State):
    def __init__(self):
        super().__init__()

        self.characters = [Tools.CHARS[k] for k in sorted(list(Tools.CHARS.keys()))]

        self.font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 15)
        self.font2 = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 20)

        self.grid = Grid(10, 2, Tools.BLACK, 50, Tools.SCREEN_RECT.centerx, Tools.SCREEN_RECT.centery + 200, 90, 90, Tools.BLACK, self.characters, self.font2, 10, 4, Tools.SPACE_GREY)

    def get_event(self, event):
        if event.type in [pg.KEYDOWN, pg.KEYUP] and (
            event.key in Tools.PLAYER1_CONTROLS or event.key in Tools.PLAYER2_CONTROLS
        ):
            if event.type == pg.KEYUP and event.key in Tools.PLAYER1_CONTROLS:
                if Tools.PLAYER1_CONTROLS[event.key] == "JUMP":
                    if self._flags["P1Ready"]:
                        self._flags["P1Ready"] = False
                        self.grid.pointer1.toggle()
                    elif not (self._flags["P1Ready"] and self._flags["P2Ready"]):
                        self.next_state = "MAINMENU"
                        self.wrap = self.fade_wrapper(self.fade_outs)
            
            if event.type == pg.KEYUP and event.key in Tools.PLAYER2_CONTROLS:
                if Tools.PLAYER2_CONTROLS[event.key] == "JUMP" and self._flags["P2Ready"]:
                    self._flags["P2Ready"] = False
                    self.grid.pointer2.toggle()

            if event.type == pg.KEYDOWN and event.key in Tools.PLAYER1_CONTROLS:

                if Tools.PLAYER1_CONTROLS[event.key] == "LIGHT" and not self._flags["P1Ready"]:
                    char = self.grid.pointer1.get_slot().char
                    if char:
                        self._flags["P1Ready"] = True
                        self.grid.pointer1.toggle()

                if not self._flags["P1Ready"]:
                    if Tools.PLAYER1_CONTROLS[event.key] == "UP":
                        self.grid.pointer1.index.y -= 1
                    elif Tools.PLAYER1_CONTROLS[event.key] == "DOWN":
                        self.grid.pointer1.index.y += 1
                    elif Tools.PLAYER1_CONTROLS[event.key] == "LEFT":
                        self.grid.pointer1.index.x -= 1
                    elif Tools.PLAYER1_CONTROLS[event.key] == "RIGHT":
                        self.grid.pointer1.index.x += 1

            if event.type == pg.KEYDOWN and event.key in Tools.PLAYER2_CONTROLS:
                if Tools.PLAYER2_CONTROLS[event.key] == "LIGHT" and not self._flags["P2Ready"]:
                    char = self.grid.pointer2.get_slot().char
                    if char:
                        self._flags["P2Ready"] = True
                        self.grid.pointer2.toggle()

                if not self._flags["P2Ready"]:
                    if Tools.PLAYER2_CONTROLS[event.key] == "UP":
                        self.grid.pointer2.index.y -= 1
                    elif Tools.PLAYER2_CONTROLS[event.key] == "DOWN":
                        self.grid.pointer2.index.y += 1
                    elif Tools.PLAYER2_CONTROLS[event.key] == "LEFT":
                        self.grid.pointer2.index.x -= 1
                    elif Tools.PLAYER2_CONTROLS[event.key] == "RIGHT":
                        self.grid.pointer2.index.x += 1

        if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
            if self._flags["P1Ready"] and self._flags["P2Ready"]:
                self._flags["Ready"] = True

    def update(self, surface, keys, current_time, delta_time):
        try:
            self.fade_caller()
        except TypeError:

            if self._flags["P1Ready"]:
                self.player1 = self.grid.pointer1.get_slot().char

            if self._flags["P2Ready"]:
                self.player2 = self.grid.pointer2.get_slot().char

            if self._flags["Ready"]:
                self.next_state = "GAMESTATE"
                self.wrap = self.fade_wrapper(self.fade_outs)

            self.draw(surface)

    def draw_portraits(self, surface):
        temp = pg.Surface((470, 40)).convert_alpha()
        temp.fill((0, 0, 0, 150))
        surface.blit(temp, (0, 375))
        surface.blit(temp, (815, 375))

        char = self.grid.pointer1.get_slot().char
        if char:
            surface.blit(char.PORTRAIT, (40, 40))
            name = Tools.Text(10, 385, char.NAME, self.font2, Tools.SPACE_GREY)
            name.draw(surface)
        
        char = self.grid.pointer2.get_slot().char
        if char:
            surface.blit(char.PORTRAIT, (915, 40))
            name = Tools.Text(825, 385, char.NAME, self.font2, Tools.SPACE_GREY)
            name.draw(surface)

    def draw(self, surface):
        surface.blit(self.bg, (0, 0))
        self.grid.draw(surface)
        self.draw_portraits(surface)
        if self._flags["P1Ready"] and self._flags["P2Ready"] and not self._flags["Ready"]:
            font = pg.font.Font(Tools.FONTS["kenvector_future"], 50)
            label = Tools.Label(Tools.SCREEN_RECT.centerx, Tools.SCREEN_RECT.centery, 1280, 50, "READY!", font, Tools.SPACE_GREY, (0, 0, 0, 150), centred=True)
            label.draw(surface)

    def startup(self, persistent, current_time):
        super().startup(persistent, current_time)
        self.wrap = self.fade_wrapper(self.fade_ins)
        self._flags["P1Ready"] = False
        self._flags["P2Ready"] = False
        self._flags["Ready"] = False
        self.player1 = None
        self.player2 = None
        self.grid.pointer1.show = True
        self.grid.pointer2.show = True

    def cleanup(self):
        self.bg = Tools.GFX["bg"]
        self.logo = Tools.GFX["logo"]
        if self._flags["Ready"]:
            self.persist["CHAR1"] = self.player1
            self.persist["CHAR2"] = self.player2
        return super().cleanup()
