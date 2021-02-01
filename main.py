from creatures import Player
from core import Game


class MyGame(Game):
    def __init__(self,):
        Game.__init__(self)

if __name__ == '__main__':
    game = MyGame
    game().run()
