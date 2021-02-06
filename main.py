from time import time
from core import Game
from uis import RoomsCounterText


class MyGame(Game):
    def __init__(self):
        from creatures import Player
        from core import Game, SpriteGroup, load_image
        from uis import HealthBar
        from room import Room
        self.rooms_seeds_dict = {}
        self.start_time = time()
        self.player = Player((460, 230))
        self.gameover = False

        # door_cords (450, 25), (80, 210), (450, 455), (820, 210)

        self.room = Room((0, 0), self)
        self.interface = SpriteGroup(HealthBar(self),
                                     RoomsCounterText(f'Комнат пройдено: '
                                                      f'{len(self.rooms_seeds_dict.keys()) - 1}',
                                                      (0, 40), 36,
                                                      (180, 180, 180)))
        self.background = load_image('assets/room/room-background.png')
        self.create_new_room((0, 0), 'any')

        Game.__init__(self)


if __name__ == '__main__':
    game = MyGame
    game().run()
