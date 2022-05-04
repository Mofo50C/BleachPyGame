import os
import pygame as pg
import pygame.locals as pl
import pathlib
import xml.etree.ElementTree as ET
import sqlite3
import importlib
import sgc
import datetime

pg.init()  # initiates pygame

TITLE = "BLEACH VS ULTIMATE"
SCREEN_SIZE = (1280, 960)
CAPTION = "BLEACH: VS ULTIMATE 1.2"

# pygame takes a tuple of rgb numbers as colours
# stored some common ones so i can use later
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
SPACE_GREY = (218, 218, 218)
NICE_GREY = (69, 69, 69)
PLAYER_1_BLUE = (0, 154, 255)
PLAYER_2_PURPLE = (255, 81, 163)

# dictionary of controls for each player
PLAYER1_CONTROLS = {
    pg.K_a: "LEFT",
    pg.K_d: "RIGHT",
    pg.K_w: "UP",
    pg.K_s: "DOWN",
    pg.K_u: "LIGHT",
    pg.K_i: "MEDIUM",
    pg.K_o: "HEAVY",
    pg.K_p: "DASH",
    pg.K_j: "SPECIAL",
    pg.K_ESCAPE: "PAUSE",
    pg.K_SPACE: "JUMP",
}

PLAYER2_CONTROLS = {
    pg.K_LEFT: "LEFT",
    pg.K_RIGHT: "RIGHT",
    pg.K_UP: "UP",
    pg.K_DOWN: "DOWN",
    pg.K_1: "LIGHT",
    pg.K_KP8: "MEDIUM",
    pg.K_KP9: "HEAVY",
    pg.K_KP_MINUS: "DASH",
    pg.K_KP4: "SPECIAL",
    pg.K_BACKSPACE: "PAUSE",
    pg.K_KP0: "JUMP",
}

CONTROLS = [PLAYER1_CONTROLS, PLAYER2_CONTROLS]


os.environ["SDL_VIDEO_CENTERED"] = "TRUE"
pg.display.set_caption(CAPTION)

SCREEN = sgc.surface.Screen(SCREEN_SIZE)  # starts the screen using the sgc module
# sgc is an addon library for pygame that allows programmers to implement simple onscreen widets like buttons and input boxes

SCREEN_RECT = SCREEN.get_rect()  # saves the rect object for the screen surface for later use

# set up common folder paths for use in program
GAME_DIR = pathlib.Path(__file__).parent.absolute()
ASSETS_FOLDER = os.path.join(GAME_DIR, "assets")
CHARS_FOLDER = os.path.join(GAME_DIR, "chars")

GFX_FOLDER = os.path.join(ASSETS_FOLDER, "graphics")
FONTS_FOLDER = os.path.join(ASSETS_FOLDER, "fonts")
SFX_FOLDER = os.path.join(ASSETS_FOLDER, "sound")
MUSIC_FOLDER = os.path.join(ASSETS_FOLDER, "music")
DATABASE_FOLDER = os.path.join(ASSETS_FOLDER, "databases")

# simply abbreviates the Vector2 class object from pygame for use as 2D vectors
VEC = pg.math.Vector2


# custom exception used for screen transition
class FinishFadeOut(Exception):
    pass


# meta class that allows the creation of classes that can only be instantiated once
class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        '''overiddes the __call__ method of type (the metaclass all python classes inherit from)
        and checks if an instance has been created or not, if not it will create one and store it
        next time a class is instantiated the stored one will be returned instead'''
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


# class that controls the connection to a database with sqlite3
class DBInterface(metaclass=Singleton):
    def __init__(self, directory, name):
        self.conn = sqlite3.connect(os.path.join(directory, name + ".db"))
        self.cur = self.conn.cursor()
        self.init()
    
    def init(self):
        '''used to initialise the actual database and differs from the constructor method.
        must be overriden in implementations to create tables set up default values etc.'''
        pass

    def execute(self, query, data=()):
        self.cur.execute(query, data)
        self.conn.commit()
        return self.cur


class MasterDB(DBInterface):
    def init(self):
        self.execute(
            """
        CREATE TABLE IF NOT EXISTS Users (
        ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Username TEXT NOT NULL,
        Password TEXT NOT NULL,
        DateModified TEXT NOT NULL)
        """
        )

        self.execute(
            """
        CREATE TABLE IF NOT EXISTS Stats (
        ID INTEGER PRIMARY KEY,
        Wins INTEGER NOT NULL,
        Losses INTEGER NOT NULL,
        Draws INTEGER NOT NULL,
        HighScore INTEGER NOT NULL,
        DateStamp TEXT,
        MaxCombo INTEGER NOT NULL,
        GamesPlayed INTEGER NOT NULL,
        FOREIGN KEY(ID) REFERENCES Users(ID))
        """
        )

    def get_user_stats(self, userid):
        return self.execute(
            """
        SELECT Stats.Wins, Stats.Losses, Stats.Draws, Stats.HighScore, Stats.DateStamp, Stats.MaxCombo, Stats.GamesPlayed, Users.Username
        FROM Stats, Users
        WHERE (Stats.ID = Users.ID) AND (Stats.ID = ?)
        """, (userid,))

    def get_login_details(self):
        return self.execute(
            """
        SELECT *
        FROM Users
        """
        )

    def get_leaderboard(self):
        return self.execute(
            """
        SELECT Users.Username, Stats.HighScore, Stats.DateStamp
        FROM Users, Stats
        WHERE Stats.ID = Users.ID
        ORDER BY Stats.HighScore DESC
        """
        )

    def add_user(self, user, password):
        today = datetime.date.today()
        self.execute(
            """
        INSERT INTO Users (Username, Password, DateModified)
        VALUES (?, ?, ?)
        """,
            (user, password, today)
        )

        self.execute(
            """
        INSERT INTO Stats (Wins, Losses, Draws, HighScore, MaxCombo, GamesPlayed)
        VALUES (0, 0, 0, 0, 0, 0)
        """
        )

    def update_stats(
        self, userid, wins, losses, draws, highscore, datestamp, maxcombo, gamesplayed
    ):
        self.execute(
            """
        UPDATE Stats
        SET Wins = ?, Losses = ?, Draws = ?, HighScore = ?, DateStamp = ?, MaxCombo = ?, GamesPlayed = ?
        WHERE Stats.ID = ?
        """,
            (wins, losses, draws, highscore, datestamp, maxcombo, gamesplayed, userid)
        )

    def update_password(self, user, password):
        self.execute(
            """
        UPDATE Users
        SET Password = ?
        WHERE Username = ?
        """,
            (password, user)
        )


# Interface class for game states
class State:
    def __init__(self):
        '''not too much implemdentation should go in the constructor.
        startup, cleanup, resume or pause used instead as states are
        not re-initialised everytime they are called.'''
        self.suspend = False
        self.withdraw = False
        self.current_time = 0.0
        self.start_time = 0.0
        self.resume_time = 0.0
        self.done = False
        self.quit = False
        self.next_state = None
        self.higher_state = None
        self.prev_state = None
        self.persist = {}
        self.pop_amount = 1
        self.bg = GFX["bg"]
        self.logo = GFX["logo"]
        self.fade_ins = None
        self.fade_outs = None
        self._flags = {}

    def get_event(self, event):
        '''process events passed on from main event loop and carry out logic to be updated
        in update(). Must be overriden'''
        pass

    def update(self, surface, keys, current_time, delta_time):
        '''logic to update changes based on events. Main function that controls the state and called
        every game tick. Must be overriden'''
        pass

    def draw(self):
        '''draw updated changes onto screen. Must be overriden if used'''
        pass

    def screen_fade_out(self):
        '''global animation used to fade between states. raises custom exception that the update
        method tests for and exits the state and switches. Ran last in the exiting animation queue'''
        temp_surf = pg.Surface(SCREEN_RECT.size).convert()
        temp_surf.fill(BLACK)
        temp_surf.set_alpha(0)
        for i in range(7):
            temp_surf.set_alpha(temp_surf.get_alpha() + 36)
            pg.display.get_surface().blit(self.bg, (0, 0))
            pg.display.get_surface().blit(temp_surf, (0, 0))
            yield

        raise FinishFadeOut

    def screen_fade_in(self):
        '''same as above method but ran first in the starting animation queue'''
        temp_surf = pg.Surface(SCREEN_RECT.size).convert()
        temp_surf.fill(BLACK)
        temp_surf.set_alpha(252)
        for i in range(7):
            temp_surf.set_alpha(temp_surf.get_alpha() - 36)
            pg.display.get_surface().blit(self.bg, (0, 0))
            pg.display.get_surface().blit(temp_surf, (0, 0))
            yield

    def fade_wrapper(self, x):
        '''warpper generator function that takes a list of generators and initiates them in order
        to be called. think of it as taking a queue of generator functions that run the
        animations. By doing yield from on the generators it initiates them ready for their __next__
        method to be called in the below method.'''
        for gen in x:
            yield from gen

    def fade_caller(self):
        '''calls __next__ on the wrapped generators in order and controls the program flow depending
        on it being a fade out animation or fade in.'''
        try:
            next(self.wrap)
        except FinishFadeOut:
            self.done = True
        except StopIteration:
            self.wrap = None

    def startup(self, persistent, current_time):
        '''function that is called when a state is switched to,
        reintialises attributes'''
        self.persist = persistent
        self.start_time = current_time
        self.fade_ins = [self.screen_fade_in()]
        self.fade_outs = [self.screen_fade_out()]

    def cleanup(self):
        '''called after a state is exited'''
        self.done = False
        self.withdraw = False
        self.wrap = None
        return self.persist

    def pause(self):
        '''called when another state is called on top of current state.'''
        self.suspend = False
        return self.persist

    def resume(self, persistent, current_time):
        '''called when function above this one is popped and reinitialses attributes'''
        self.persist = persistent
        self.resume_time = current_time


# class that creates label objects used for on screen UI graphics
class Label:
    def __init__(self, x, y, w, h, text, font, fg, bg=None, *, centred=False, show=True, blink=False):
        self.alpha = 255
        self.dalpha = 5
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.centred = centred
        self.blink = blink
        self.show = show
        self.text = Text(self.w // 2, self.h // 2, text, font, fg, centred=True)
        self.image = pg.Surface((self.w, self.h)).convert_alpha()
        if bg is None:
            bg = (0, 0, 0, 0)
        self.image.fill(bg)
        self.text.draw(self.image)
    
    def update(self):
        if self.blink:
            if self.alpha < 5:
                self.dalpha = 5
            elif self.alpha > 250:
                self.dalpha = -5

            self.alpha += self.dalpha
            self.image.set_alpha(self.alpha)

    def toggle(self):
        self.show = not self.show

    def draw(self, surface):
        if self.show:
            if self.centred:
                rect = self.image.get_rect(center=(self.x, self.y))
            else:
                rect = (self.x, self.y)
            surface.blit(self.image, rect)


# simplfies creating and drawing text by allowing
class Text:
    def __init__(self, x, y, text, font, colour, *, centred=False):
        self.x = x
        self.y = y
        self.centred = centred
        self.image = font.render(text, True, colour)
    
    def update(self):
        pass

    def draw(self, surface):
        if self.centred:
            rect = self.image.get_rect(center=(self.x, self.y))
        else:
            rect = (self.x, self.y)
        surface.blit(self.image, rect)


# custom menu pointer used for all menus. blinks rapidly like the MUGEN menu
class MenuPointer:
    def __init__(self, colour, buttons):
        self.colour = colour
        self.buttons = buttons
        self.index = (0, 0)
        self.dalpha = 15
        self.alpha = 0

    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, value):
        self._index = VEC(value)
    
    def update(self):
        if self.alpha > 75:
            self.dalpha = -15
        elif self.alpha < 15:
            self.dalpha = 15
        
        self.alpha += self.dalpha

    def draw(self, surface):
        img = pg.Surface((self.get_item().width, self.get_item().height))
        img.fill(self.colour)
        img.set_alpha(self.alpha)
        surface.blit(img, img.get_rect(center=(self.get_item().x, self.get_item().y)))
    
    def get_item(self):
        y = int(self.index.y) % len(self.buttons)
        x = int(self.index.x) % len(self.buttons[y])
        return self.buttons[y][x]
    
    def click(self):
        return self.get_item().click()


# creates button objects to be used for on screen UI
# doesnt actually do anything inherit from it and override
class BasicButton:
    def __init__(self, x, y, text, font, fg, bg, alpha, w=None, h=None):
        self.x = x
        self.y = y
        self.label = font.render(text, True, fg)
        if w is None:
            w = self.label.get_width()
        if h is None:
            h = self.label.get_height()
        self.width = w
        self.height = h
        self.size = (self.width, self.height)
        self.image = pg.Surface(self.size).convert_alpha()
        self.image.fill((*bg, alpha))
        self.image.blit(self.label, self.label.get_rect(center=(self.width // 2, self.height // 2)))
    
    def click(self):
        """must be overridden in a custom class if used"""
        pass
    
    def draw(self, surface):
        pos = self.image.get_rect(center=(self.x, self.y))
        surface.blit(self.image, pos)


# impleneted button object that returns its name when clicked
class NamedBtn(BasicButton):
    def __init__(self, name, x, y, text, font, fg, bg, alpha, w=None, h=None):
        super().__init__(x, y, text, font, fg, bg, alpha, w, h)
        self.name = name

    def click(self):
        return self.name
        

# class used to create a sprite sheet loader object that handles splitting sprite sheets and loading their XML info files
class SpriteSheet:
    def __init__(self, sprites, scale=2):
        self.scale = scale
        self.sheets = {}
        self.xmls = {}
        self.all_frames = {}
        self.load_spritesheets(sprites)
        self.split_sheets()

    def load_spritesheets(self, directory):
        '''ind and load all spritesheets and their respective xml data file related to character with name "self.name'''
        with os.scandir(directory) as it:
            for entry in it:
                if not entry.name.startswith(".") and entry.is_file():
                    name, ext = os.path.splitext(entry.name)
                    if ext.lower() == ".xml":
                        self.xmls[name] = entry.path
                    elif ext.lower() == ".png":
                        img = pg.image.load(entry.path)
                        img.convert_alpha()
                        self.sheets[name] = img

    def split_sheets(self):
        '''simultaneously parse xml files of every loaded sprite sheet and split said sheet into subsurfaces'''
        if self.sheets:
            for sheet in self.sheets:
                try:
                    tree = ET.parse(self.xmls[sheet])
                except KeyError:
                    return

                atlas = tree.getroot()
                temp_dict = {}

                for sub in atlas.findall("SubTexture"):
                    temp_list = []
                    for sprite in sub.iter("sprite"):
                        x = int(sprite.attrib["x"]) * self.scale
                        y = int(sprite.attrib["y"]) * self.scale
                        w = int(sprite.attrib["w"]) * self.scale
                        h = int(sprite.attrib["h"]) * self.scale

                        dx = int(sprite.attrib["ox"]) * self.scale - x
                        dy = int(sprite.attrib["oy"]) * self.scale - y
                        ow = int(sprite.attrib["ow"]) * self.scale
                        oh = int(sprite.attrib["oh"]) * self.scale

                        new_sheet = self.sheets[sheet]
                        
                        temp_list.append({"img": new_sheet.subsurface((x, y, w, h)), "meta": {"dx": dx, "dy": dy, "off_w": ow, "off_h": oh}})

                    temp_dict[sub.attrib["n"]] = temp_list

                self.all_frames[sheet] = temp_dict
        else:
            print("no loaded sprite sheets available")


def load_chars(directory):
    '''search chars folder for files with the same name as the character list in characters.txt file and load their classes'''
    char_dict = {}
    
    with open(os.path.join(directory, "characters.txt"), "r") as f:
        names = [line.strip() for line in f]
    
    with os.scandir(directory) as it:
        for entry in it:
            if entry.name in names and entry.is_dir():
                char = importlib.import_module("." + "chars." + entry.name + "." + entry.name, "data")
                char_dict[entry.name] = char
    
    return char_dict


def recur_load_gfx(directory, graphics={}, colorkey=(255, 0, 255), accept=(".png")):
    '''similar to load_gfx but searches the entire directory recuresively'''
    with os.scandir(directory) as it:
        for entry in it:
            if not entry.name.startswith(".") and entry.is_dir():
                graphics = recur_load_gfx(entry.path, graphics)
            elif not entry.name.startswith(".") and entry.is_file():
                # print(entry.path, entry.name)
                name, ext = os.path.splitext(entry.name)
                if ext.lower() in accept:
                    img = pg.image.load(entry.path)
                    if img.get_alpha():
                        img = img.convert_alpha()
                    else:
                        img = img.convert()
                        img.set_colorkey(colorkey)

                    if os.path.basename(directory) == "graphics":
                        graphics[name] = img
                    else:
                        graphics[os.path.basename(directory) + "/" + name] = img

    return graphics


def load_gfx(directory, colorkey=(255, 0, 255), accept=(".png")):
    '''similar to generic asset loading but loads image as a pygame image object and converts the
    format to a pygame readable version. Then adds them to a dictionary adn returns it'''
    graphics = {}

    with os.scandir(directory) as it:
        for entry in it:
            if not entry.name.startswith(".") and entry.is_file():
                name, ext = os.path.splitext(entry.name)
                if ext.lower() in accept:
                    img = pg.image.load(entry.path)
                    if img.get_alpha():
                        img = img.convert_alpha()
                    else:
                        img = img.convert()
                        img.set_colorkey
                        
                    graphics[name] = img
    
    return graphics


def load_generic_asset(directory, accept):
    '''generic asset loading function that takes a directory path and a tuple
    of accepted file extentions, iterates through entries of the directory path
    and loads the file paths of the accepted file extentions in the directory to a dictionary
    and returns them.'''
    assets = {}
    for asset in os.listdir(directory):
        name, ext = os.path.splitext(asset)
        if ext.lower() in accept:
            assets[name] = os.path.join(directory, asset)
    return assets


def load_sfx(directory, accept=(".wav", ".mp3", ".ogg", ".mdi")):
    '''similar to generic asset loading but it loads the sound files as pygame
    sound objects instead and adds them to a dictionary'''
    effects = {}
    for fx in os.listdir(directory):
        name, ext = os.path.splitext(fx)
        if ext.lower() in accept:
            effects[name] = pg.mixer.Sound(os.path.join(directory, fx))
    return effects


FONTS = load_generic_asset(FONTS_FOLDER, (".ttf",))
MUSIC = load_generic_asset(MUSIC_FOLDER, (".wav", ".mp3", ".ogg", ".mdi"))
SFX = load_sfx(SFX_FOLDER)
GFX = recur_load_gfx(GFX_FOLDER)
CHARS = load_chars(CHARS_FOLDER)
MASTER_DB = MasterDB(DATABASE_FOLDER, "master")
