import pygame as pg
import os

from ... import Tools

FILE = os.path.dirname(__file__)
GFX_FOLDER = os.path.join(FILE, "gfx")
SPRITES_FOLDER = os.path.join(FILE, "sprites")

SPRITES = Tools.SpriteSheet(SPRITES_FOLDER).all_frames
GFX = Tools.load_gfx(GFX_FOLDER)
THUMB = GFX["dangai_thumb"]
PORTRAIT = GFX["dangai_portrait"]
NAME = "Ichigo Kurosaki (Post Dangai Ver.)"

MAX_SPEED = 12


class Action:
    def __init__(self, char):
        self.char = char
        self.suspend = False
        self.withdraw = False
        self.done = False
        self.queue = False
        self.presist = {}
        self.pop_amount = 1
        self.animation_frame = 0
        self.next_action = None
        self.prev_action = None
    
    @property
    def keys(self):
        return self.char.keys

    def btn(self, name):
        return self.char.controls[name]

    def get_event(self, event):
        pass

    def draw(self):
        pass

    def update(self):
        pass

    def startup(self, presistent):
        self.presist = presistent

    def cleanup(self):
        self.done = False
        self.withdraw = False
        return self.presist

    def pause(self):
        self.suspend = False
        return self.presist

    def resume(self, presistent):
        self.presist = presistent


class GroundedAction(Action):
    def __init__(self, char):
        super().__init__(char)
    
    def update(self):
        super().update()
        if self.keys[self.btn("JUMP")]:
            self.done = True
            self.next_action = "jumping"
        
        if self.keys[self.btn("DASH")]:
            self.done = True
            self.next_action = "dash"
        
        if self.keys[self.btn("LIGHT")]:
            self.done = True
            self.next_action = "lightneutral"


class AerialAction(Action):
    def __init__(self, char):
        super().__init__(char)
    
    def get_event(self, event):
        super().get_event(event)
        if event.type == pg.KEYDOWN:
            if event.key == self.btn("DASH"):
                self.next_action = "dash"
                self.suspend = True
        
            if event.key == self.btn("LIGHT"):
                self.next_action = "lightaerial"
                self.suspend = True

    def update(self):
        super().update()
        if self.keys[self.btn("RIGHT")]:
            self.char.vel.x = MAX_SPEED

        if self.keys[self.btn("LEFT")]:
            self.char.vel.x = -MAX_SPEED

        if not (self.keys[self.btn("RIGHT")] or self.keys[self.btn("LEFT")]):
            self.char.vel.x = 0
    

class Idle(Action):
    def __init__(self, char):
        super().__init__(char)
        self.frames = [
            frame
            for frame in self.char.all_frames["dangai"]["stand"]
            for _ in range(4)
        ]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]
    
    def update(self):
        if self.keys[self.btn("LEFT")] or self.keys[self.btn("RIGHT")]:
            self.suspend = True
            self.next_action = "walking"

        if self.keys[self.btn("JUMP")]:
            self.suspend = True
            self.next_action = "jumping"

        if self.keys[self.btn("DOWN")]:
            self.suspend = True
            self.next_action = "guarding"
        
        if self.keys[self.btn("DASH")]:
            self.suspend = True
            self.next_action = "dash"

        if self.keys[self.btn("LIGHT")]:
            self.suspend = True
            self.next_action = "lightneutral"

    def draw(self):
        self.animation_frame = self.animation_frame % 16
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(
                bottomleft=(
                    self.char.pos.x - meta["dx"],
                    self.char.pos.y,
                )
            )
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(
                bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))
        self.char.image = img
        self.char.rect = rect
        self.animation_frame += 1

    def startup(self, presistent):
        super().startup(presistent)
        self.char.status = "GROUND"

    def resume(self, presistent):
        super().startup(presistent)
        self.char.status = "GROUND"


class Jumping(AerialAction):
    def __init__(self, char):
        super().__init__(char)
        self.frames = self.char.all_frames["dangai"]["jump"][:5]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]

    def update(self):
        super().update()
        if self.animation_frame == 4:
            self.char.status = "AERIAL"
            if self.char.vel.y > 0:
                self.char.vel.y -= self.char.acc.y
                self.char.pos.y -= self.char.vel.y
            else:
                self.done = True
                self.next_action = "falling"
        else:
            self.animation_frame += 1

        self.char.pos.x += self.char.vel.x

    def draw(self):
        self.animation_frame = self.animation_frame % 5
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(
                bottomleft=(self.char.pos.x - meta["dx"], self.char.pos.y)
            )
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(
                bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y)
            )

        self.char.rect = rect
        self.char.image = img
        
    def startup(self, presistent):
        super().startup(presistent)
        self.char.vel = Tools.VEC(0, 20)

    def cleanup(self):
        self.animation_frame = 0
        return super().cleanup()
    
    def resume(self, presistent):
        super().resume(presistent)
        self.next_action = "vulfall"
        self.done = True


class Falling(AerialAction):
    def __init__(self, char):
        super().__init__(char)
        self.frames = self.char.all_frames["dangai"]["jump"][4:9]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]

    def update(self):
        super().update()
        if self.char.status == "AERIAL":
            if self.char.pos.y < self.char.ground.y:
                self.char.pos.y += self.char.vel.y
                self.char.vel.y += self.char.acc.y
            else:
                self.char.status = "GROUND"

        self.char.pos.x += self.char.vel.x

        if self.animation_frame == 4 and self.char.status == "GROUND":
            self.withdraw = True

    def draw(self):
        self.animation_frame = self.animation_frame % 5
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(
                bottomleft=(self.char.pos.x - meta["dx"], self.char.pos.y))
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(
                bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))

        self.char.rect = rect
        self.char.image = img

        if self.char.status == "AERIAL":
            self.animation_frame = 0
        else:
            self.animation_frame += 1

    def cleanup(self):
        self.animation_frame = 0
        return super().cleanup()

    def resume(self, presistent):
        super().resume(presistent)
        self.char.status = "AERIAL"


class VulFall(AerialAction):
    def __init__(self, char):
        super().__init__(char)
        self.frames = self.char.all_frames["dangai"]["jump"][4:9]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]

    def get_event(self, event):
        pass

    def update(self):
        super().update()
        if self.char.status == "AERIAL":
            if self.char.pos.y < self.char.ground.y:
                self.char.pos.y += self.char.vel.y
                self.char.vel.y += self.char.acc.y
            else:
                self.char.status = "GROUND"

        self.char.pos.x += self.char.vel.x

        if self.animation_frame == 4 and self.char.status == "GROUND":
            self.withdraw = True

    def draw(self):
        self.animation_frame = self.animation_frame % 5
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(
                bottomleft=(self.char.pos.x - meta["dx"], self.char.pos.y))
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(
                bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))

        self.char.rect = rect
        self.char.image = img

        if self.char.status == "AERIAL":
            self.animation_frame = 0
        else:
            self.animation_frame += 1

    def cleanup(self):
        self.animation_frame = 0
        return super().cleanup()

    def resume(self, presistent):
        super().resume(presistent)
        self.char.status = "AERIAL"


class Walking(GroundedAction):
    def __init__(self, char):
        super().__init__(char)
        self.frames = [frame for frame in self.char.all_frames["dangai"]["run"] for _ in range(2)]
        self.accepted = ["RIGHT", "LEFT"]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]
    
    def update(self):
        super().update()
        if self.keys[self.btn("RIGHT")]:
            self.char.facing = "right"
            self.char.vel.x = MAX_SPEED

        if self.keys[self.btn("LEFT")]:
            self.char.facing = "left"
            self.char.vel.x = -MAX_SPEED

        if not self.keys[self.btn("RIGHT")] and not self.keys[self.btn("LEFT")]:
            self.char.vel.x = 0
            self.withdraw = True
        
        self.char.pos.x += self.char.vel.x

        self.animation_frame += 1

    def draw(self):
        self.animation_frame = self.animation_frame % 16
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(bottomleft=(self.char.pos.x, self.char.pos.y))
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(bottomright=(self.char.pos.x + img.get_width(), self.char.pos.y))

        self.char.image = img
        self.char.rect = rect


class Guarding(Action):
    def __init__(self, char):
        super().__init__(char)
        self.frames = self.char.all_frames["dangai"]["guard"]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]

    def update(self):
        if self.keys[self.btn("DOWN")] and self.animation_frame == 1:
            self.char.status = "GUARD"
        elif not self.keys[self.btn("DOWN")]:
            self.char.status = "GROUND"
            if self.animation_frame == 2:
                self.withdraw = True

    def draw(self):
        self.animation_frame = self.animation_frame % 3
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(
                bottomleft=(
                    self.char.pos.x - meta["dx"],
                    self.char.pos.y,
                )
            )
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))

        self.char.image = img
        self.char.rect = rect

        if self.char.status == "GUARD":
            self.animation_frame = 1

        else:
            self.animation_frame += 1


class Dash(Action):
    def __init__(self, char):
        super().__init__(char)
        self.frames = self.char.all_frames["dangai"]["dash"]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]
        
    def update(self):
        if self.animation_frame == 0:
            self.animation_frame += 1
        elif self.animation_frame == 1:
            if self.char.current_time - self.start_time < 300:
                if self.char.facing == "right":
                    self.char.pos.x += 40
                elif self.char.facing == "left":
                    self.char.pos.x -= 40
                self.animation_frame = 1
            else:
                self.animation_frame += 1
        elif self.animation_frame == 2:
            self.withdraw = True
    
    def draw(self):
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(bottomleft=(self.char.pos.x - meta["dx"], self.char.pos.y))
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))
        
        self.char.image = img
        self.char.rect = rect

    def startup(self, presistent):
        super().startup(presistent)
        self.start_time = self.char.current_time

    def cleanup(self):
        self.animation_frame = 0
        return super().cleanup()


class Hurt(Action):
    def __init__(self, char):
        super().__init__(char)
        self.frames = self.char.all_frames["dangai"]["hit"]
        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]

    def update(self):
        if self.char.hit_count:
            if self.char.current_time - self.start_time > 1000:
                self.char.hit_count = 0
                self.withdraw = True
            else:
                self.animation_frame = self.char.hit_count - 1
                if isinstance(self.char.action_stack[-2], Falling):
                    if self.char.pos.y < self.char.ground.y:
                        self.char.pos.y += 3
            
    def draw(self):
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(bottomleft=(self.char.pos.x - meta["dx"], self.char.pos.y))
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))
        
        self.char.image = img
        self.char.rect = rect

    def startup(self, presistent):
        super().startup(presistent)
        self.start_time = self.char.current_time
        self.char.status = "HIT"
    

class KnockDown(Action):
    pass


class LightAerial(Action):
    def __init__(self, char):
        super().__init__(char)
        self.frames = [frame for frame in self.char.all_frames["dangai"]["lightA"][:3] for _ in range(5)]  # last frame 14
        self.frames.append(self.char.all_frames["dangai"]["lightA"][3])  # frame 15
        self.frames.append(self.char.all_frames["dangai"]["lightA"][4])  # frame 16

        self.sprites = [frame["img"] for frame in self.frames]
        self.meta = [frame["meta"] for frame in self.frames]
    
    def update(self):

        if self.animation_frame == 4:
            self.char.status = "ATTACK"
        
        if self.animation_frame == 5:
            self.char.status = "AERIAL"
        
        if self.animation_frame == 14:
            if self.char.current_time - self.start_time > 400:
                self.animation_frame = 15
            else:
                self.animation_frame = 14
        elif self.animation_frame == 16:
            self.withdraw = True
        else:
            self.animation_frame += 1
        
    def draw(self):
        meta = self.meta[self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.animation_frame]
            rect = img.get_rect(bottomleft=(self.char.pos.x - meta["dx"], self.char.pos.y))
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.animation_frame], True, False)
            rect = img.get_rect(bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))
        
        self.char.image = img
        self.char.rect = rect
 
    def startup(self, presistent):
        super().startup(presistent)
        self.start_time = self.char.current_time
        self.char.attack_time = self.start_time
        self.char.dmg = 25
    
    def cleanup(self):
        self.animation_frame = 0
        self.char.dmg = 0
        self.char.attack_time = None
        return super().cleanup()


class LightNeutral(Action):
    def __init__(self, char):
        super().__init__(char)
        p1 = [frame for frame in self.char.all_frames["dangai"]["lightNa"][:3] for _ in range(4)]  # last frame 11
        p1.append(self.char.all_frames["dangai"]["lightNa"][3])  # frame 12

        p2 = [frame for frame in self.char.all_frames["dangai"]["lightNb"][:4] for _ in range(4)]  # last frame 15
        p2.append(self.char.all_frames["dangai"]["lightNb"][4])  # frame 16
        p2.append(self.char.all_frames["dangai"]["lightNb"][5])  # frame 17

        p3 = [frame for frame in self.char.all_frames["dangai"]["lightNc"][:4] for _ in range(4)]  # last frame 15
        p3.append(self.char.all_frames["dangai"]["lightNc"][4])  # frame 16

        self.frames = [p1, p2, p3]
        self.sprites = [[frame["img"] for frame in part] for part in self.frames]
        self.meta = [[frame["meta"] for frame in part] for part in self.frames]

        self.part = 1
        self.end_anim = False

    def update(self):

        if self.part == 1:
            if self.animation_frame == 11:
                self.char.status = "ATTACK"
            if self.animation_frame == 12:
                self.char.status = "GROUND"
                if (self.char.current_time - self.start_time) > 600:
                    self.withdraw = True
                else:
                    self.animation_frame = 12

                if self.keys[self.btn("LIGHT")]:
                    self.part = 2
                    self.animation_frame = 0
                    self.start_time = self.char.current_time
                    if self.char.facing == "right":
                        self.char.pos.x += 20
                    elif self.char.facing == "left":
                        self.char.pos.x -= 20

            else:
                self.animation_frame += 1

        if self.part == 2:
            if self.animation_frame == 15:
                self.char.status = "ATTACK"

            if self.animation_frame == 16:
                self.char.status = "GROUND"
                if (self.char.current_time - self.start_time) > 600:
                    self.animation_frame = 17
                else:
                    self.animation_frame = 16

                if self.keys[self.btn("LIGHT")]:
                    self.part = 3
                    self.animation_frame = 0
                    self.start_time = self.char.current_time

            elif self.animation_frame == 17:
                self.withdraw = True
            else:
                self.animation_frame += 1
                if (self.animation_frame % 4) == 0:
                    if self.char.facing == "right":
                        self.char.pos.x += 4
                    elif self.char.facing == "left":
                        self.char.pos.x -= 4
        
        if self.part == 3:
            if self.animation_frame == 14:
                self.char.status = "ATTACK"

            if self.animation_frame == 15:
                self.char.status = "GROUND"
                if (self.char.current_time - self.start_time) > 500:
                    self.animation_frame = 16
                    self.start_time = self.char.current_time
                    if self.char.facing == "right":
                        self.char.pos.x += 50
                    elif self.char.facing == "left":
                        self.char.pos.x -= 50
                else:
                    self.animation_frame = 15
            elif self.animation_frame == 16:
                if self.char.current_time - self.start_time > 150:
                    self.withdraw = True
                else:
                    self.animation_frame = 16
            else:
                self.animation_frame += 1
        
    def draw(self):
        meta = self.meta[self.part - 1][self.animation_frame]
        if self.char.facing == "right":
            img = self.sprites[self.part - 1][self.animation_frame]
            rect = img.get_rect(bottomleft=(self.char.pos.x - meta["dx"], self.char.pos.y))
        elif self.char.facing == "left":
            img = pg.transform.flip(self.sprites[self.part - 1][self.animation_frame], True, False)
            rect = img.get_rect(bottomright=(self.char.pos.x + meta["dx"] + meta["off_w"], self.char.pos.y))
        
        self.char.image = img
        self.char.rect = rect
            
    def startup(self, presistent):
        super().startup(presistent)
        self.start_time = self.char.current_time
        self.char.attack_time = self.start_time
        self.char.dmg = 250

    def cleanup(self):
        self.part = 1
        self.animation_frame = 0
        self.attack_time = None
        self.char.dmg = 0
        return super().cleanup()


class LightUp(Action):
    pass


class LightDown(Action):
    pass


class MediumAerial(Action):
    pass


class MediumNeutral(Action):
    pass


class MediumUp(Action):
    pass


class MediumDown(Action):
    pass


class HeavyNeutral(Action):
    pass


class HeavyAerial(Action):
    pass


class HeavyUp(Action):
    pass


class HeavyDown(Action):
    pass


class SpecialNeutral(Action):
    pass


class SpecialAerial(Action):
    pass


class SpecialUp(Action):
    pass


class SpecialDown(Action):
    pass


class Dangai:

    def __init__(self, num, controls, ground_x, ground_y):
        self.player_num = num
        self.hp = 1000
        self.energy = 0
        self.dmg = 0
        self.hit_count = 0
        self.controls = {val: key for key, val in controls.items()}

        if self.player_num == 1:
            self.facing = "right"
        else:
            self.facing = "left"

        self.all_frames = SPRITES
        self.ground = Tools.VEC(ground_x, ground_y)
        self.pos = Tools.VEC(self.ground.x, self.ground.y)
        self.vel = Tools.VEC(0, 20)
        self.acc = Tools.VEC(0, 1)
        self.current_time = None
        self.delta_time = None
        self.keys = None
        self.status = None
        self.attack_time = None
        self.vul_actions = (Jumping, Falling, Idle, Walking, VulFall)
        self.master_actions = (Action, GroundedAction, AerialAction)
        self.action_dict = {}
        self.action_stack = []
        self.action_queue = []
        self.setup_actions()

    def setup_actions(self):
        self.keys = pg.key.get_pressed()
        for maction in self.master_actions:
            for action in maction.__subclasses__():
                if action not in self.master_actions:
                    self.action_dict[action.__name__.lower()] = action(self)

        self.action_stack.append(self.action_dict["idle"])
        self.action_stack[-1].startup({})

    def switch_action(self, name):
        presistent = self.action_stack[-1].cleanup()
        if len(self.action_stack) > 0:
            old_action = self.action_stack.pop().__class__.__name__
        self.action_stack.append(self.action_dict[name])
        self.action_stack[-1].prev_action = old_action
        self.action_stack[-1].startup(presistent)

    def push_action(self, name):
        presistent = self.action_stack[-1].pause()
        self.action_stack.append(self.action_dict[name])
        self.action_stack[-1].startup(presistent)

    def pop_action(self, amount=1):

        for _ in range(amount):
            presistent = self.action_stack[-1].cleanup()
            old_action = self.action_stack.pop().__class__.__name__

        self.action_stack[-1].prev_action = old_action
        self.action_stack[-1].resume(presistent)

    def clear_action_stack(self):
        while len(self.action_stack) > 0:
            self.action_stack[-1].cleanup()
            self.action_stack.pop()

    def enqueue_action(self, name):
        self.action_queue.append(self.action_dict[name])

    def dequeue_action(self):
        try:
            return self.action_queue.pop(0)
        except IndexError:
            print("player %s action queue empty" % self.player_num)

    def get_event(self, event):
        if event.key in self.controls.values():
            self.action_stack[-1].get_event(event)

    def update(self, keys, current_time, delta_time):
        self.keys = keys
        self.current_time = current_time
        self.delta_time = delta_time
        if self.action_stack[-1].suspend:
            self.push_action(self.action_stack[-1].next_action)
        elif self.action_stack[-1].withdraw:
            self.pop_action()
        elif self.action_stack[-1].done:
            self.switch_action(self.action_stack[-1].next_action)

        if self.hit_count:
            if isinstance(self.action_stack[-1], self.vul_actions):
                if isinstance(self.action_stack[-1], Walking):
                    self.switch_action("hurt")
                elif isinstance(self.action_stack[-1], Jumping):
                    self.switch_action("vulfall")
                    self.push_action("hurt")
                else:
                    self.push_action("hurt")

        self.action_stack[-1].update()
        self.action_stack[-1].draw()

        self.mask = pg.mask.from_surface(self.image)


def main(*args, **kwargs):
    return Dangai(*args, **kwargs)
