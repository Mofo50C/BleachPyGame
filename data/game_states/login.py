import pygame as pg
import os
import sgc

from .. import Tools


class Login(Tools.State):
    def __init__(self):
        super().__init__()
        self.next_state = "REGISTER"
        self.create_menu()
        self.pointer = Tools.MenuPointer(Tools.SPACE_GREY, self.buttons)
        self.user_id = None
        self._flags["login_error"] = False
        self._flags["reg_error"] = False
        self._flags["reg_success"] = False

    def get_event(self, event):
        if event.type in [pg.KEYDOWN, pg.KEYUP] and event.key in Tools.CONTROLS[self.player - 1]:
            if not self.user_box.has_focus() and not self.pass_box.has_focus():
                if event.type == pg.KEYUP and Tools.CONTROLS[self.player - 1][event.key] == "LIGHT":
                    self._flags["login_error"] = False
                    self._flags["reg_error"] = False
                    self._flags["reg_success"] = False
                    btn = self.pointer.click()
                    if btn == "Login":
                        self.login(self.user_box.text, self.pass_box.text)
                    elif btn == "Register":
                        self.user_id = None
                        self.register(self.user_box.text, self.pass_box.text)

                if event.type == pg.KEYDOWN:
                    if Tools.CONTROLS[self.player - 1][event.key] == "LEFT":
                        self.pointer.index.x -= 1
                    elif Tools.CONTROLS[self.player - 1][event.key] == "RIGHT":
                        self.pointer.index.x += 1

    def update(self, surface, keys, current_time, delta_time):
        self.pointer.update()
        if self.user_id:
            self.persist["UUID"] = self.user_id
            self.persist["P#"] = self.player
            self.withdraw = True
        elif self.user_id is False:
            self._flags["login_error"] = True

        self.draw(surface)

    def draw(self, surface):
        surface.blit(self.old_screen, (0, 0))

        temp = pg.Surface(surface.get_size()).convert_alpha()
        temp.fill(Tools.BLACK)
        temp.set_alpha(50)
        surface.blit(temp, (0, 0))

        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 20)
        rect = self.menu.get_rect(center=Tools.SCREEN_RECT.center)
        surface.blit(self.menu, rect)

        text = None
        if self._flags["login_error"]:
            text = Tools.Text(Tools.SCREEN_RECT.centerx, Tools.SCREEN_RECT.centery - 80, "Invalid credentials...", font, Tools.RED, centred=True)
        if self._flags["reg_error"]:
            text = Tools.Text(Tools.SCREEN_RECT.centerx, Tools.SCREEN_RECT.centery - 80, "User already exists or invalid credentials", font, Tools.RED, centred=True)
        if self._flags["reg_success"]:
            text = Tools.Text(Tools.SCREEN_RECT.centerx, Tools.SCREEN_RECT.centery - 80, "Successfully registered user", font, Tools.GREEN, centred=True)

        if text is not None:
            text.draw(surface)

        for l in self.buttons:
            for btn in l:
                btn.draw(surface)

        self.pointer.draw(surface)
    
    def register(self, user, password):
        for row in Tools.MASTER_DB.get_login_details():
            if user == row[1]:
                self._flags["reg_error"] = True
                break
        else:
            if len(user) > 3 and len(password) > 6 and user.isalnum() and password.isalnum():
                Tools.MASTER_DB.add_user(user, password)
                self._flags["reg_success"] = True
            else:
                self._flags["reg_error"] = True
    
    def login(self, user, password):
        for row in Tools.MASTER_DB.get_login_details():
            if user == row[1] and password == row[2]:
                self.user_id = row[0]
                break
        else:
            self.user_id = False
    
    def create_menu(self):
        self.user_box = sgc.InputBox((300, 50), pos=(Tools.SCREEN_RECT.centerx - 150, Tools.SCREEN_RECT.centery - 25 - 20), default="Input username...")
        self.pass_box = sgc.InputBox((300, 50), pos=(Tools.SCREEN_RECT.centerx - 150, Tools.SCREEN_RECT.centery - 25 + 30), default="Input password...")
        self.menu = pg.Surface((600, 400)).convert_alpha()
        self.menu.fill((*Tools.BLACK, 150))

        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 50)
        title = font.render("Login", True, Tools.SPACE_GREY)
        self.menu.blit(title, (600 // 2 - title.get_width() // 2, 20))
        pg.draw.line(self.menu, Tools.SPACE_GREY, (600 // 2 - title.get_width() - 20, 80), (600 // 2 + title.get_width() + 20, 80), 7)
        
        font = pg.font.Font(Tools.FONTS["kenvector_future_thin"], 20)
        self.buttons = [[Tools.NamedBtn("Login", Tools.SCREEN_RECT.centerx - 300 + 110, Tools.SCREEN_RECT.centery + 150, "Login", font, Tools.SPACE_GREY, Tools.BLACK, 0, 120),
                        Tools.NamedBtn("Register", Tools.SCREEN_RECT.centerx + 300 - 60 - 50, Tools.SCREEN_RECT.centery + 150, "Register", font, Tools.SPACE_GREY, Tools.BLACK, 0, 120)]]

    def startup(self, persistent, current_time):
        super().startup(persistent, current_time)
        self.old_screen = pg.display.get_surface().copy()
        self.pass_box.add(1, False, 2)
        self.user_box.add(0, False, 2)
        self.player = self.persist["P#"]
        self.user_id = None

    def cleanup(self):
        self.user_box.text = ""
        self.pass_box.text = ""
        self.user_box.remove(False)
        self.pass_box.remove(False)
        return super().cleanup()
