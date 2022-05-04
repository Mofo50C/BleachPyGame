import pygame as pg

from data import Main


# simple function that runs the main game loop
def main():
    game = Main.GameEngine()
    game.run()
    pg.quit()


if __name__ == "__main__":
    main()
