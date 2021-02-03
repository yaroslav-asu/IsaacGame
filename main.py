from core import Game
from items import HalfHeart, FullHeart


class MyGame(Game):
    def __init__(self,):
        from creatures import Player, EnemyBlob, EnemyMosquito
        from core import Game, SpriteGroup, load_image
        from objects import Rock, Walls
        from uis import HealthBar
        self.player = Player((100, 50))
        self.rock_1 = Rock((400, 270))
        self.rock_2 = Rock((450, 250))
        # self.blob_1 = EnemyBlob((200, 100))
        self.blob_2 = EnemyBlob((100, 200))
        # self.blob_3 = EnemyBlob((300, 400))
        self.mosquito = EnemyMosquito((200, 200), 'big')
        self.half_heart_1 = HalfHeart((100, 200))
        self.half_heart_2 = HalfHeart((100, 200))
        self.heart_1 = FullHeart((400, 300))

        self.wall = Walls()

        self.interface = SpriteGroup(HealthBar(self))
        self.objects = []
        self.physical_group = SpriteGroup(self.rock_1, self.blob_2, self.rock_2, self.wall)
        self.items = SpriteGroup(self.half_heart_1, self.half_heart_2, self.heart_1)
        self.creatures = SpriteGroup(self.mosquito, self.player)
        self.groups = []
        self.ammos = SpriteGroup()

        self.background = load_image('assets/room/room-background.png')
        for obj in [self.physical_group, self.items, self.ammos, self.interface, self.creatures]:
            self.add_object(obj)

        Game.__init__(self)


if __name__ == '__main__':
    game = MyGame
    game().run()
