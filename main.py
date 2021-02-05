from time import time

from core import Game
from items import HalfHeart, FullHeart


class MyGame(Game):
    def __init__(self):
        from creatures import Player, EnemyBlob, EnemyMosquito
        from core import Game, SpriteGroup, load_image
        from uis import HealthBar
        from room import Room
        self.rooms_seeds_dict = {}
        self.start_time = time()
        self.player = Player((300, 300))

        # door_cords (450, 25), (80, 210), (450, 455), (820, 210)

        self.room = Room((0, 0), self)

        self.interface = SpriteGroup(HealthBar(self))
        self.background = load_image('assets/room/room-background.png')
        self.create_new_room((0, 0), 'any')

        Game.__init__(self)


if __name__ == '__main__':
    game = MyGame
    game().run()
