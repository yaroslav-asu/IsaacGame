from core import *
from creatures import *


class Explosion(AnimatedSprite):
    """
    класс взрыва
    """

    def __init__(self, parent, coords, offset, size, animation_speed=1):
        explosion_animation = {
            'explosion': [f'assets/explosion/{file_name}' for file_name in
                          os.listdir('assets/explosion')],
            'wait': [f'assets/explosion/{os.listdir("assets/explosion")[0]}']}
        AnimatedSprite.__init__(self, explosion_animation, coords, size, 'wait', animation_speed,
                                (68, 36, 52))
        self.parent = parent
        self.offset = offset

    def explode(self):
        """
        взрыв
        """
        self.start('explosion')
        self.parent.is_killed = True
        self.parent.is_invisible = True

    def update(self, game):
        """
        обновление
        :param game: игра
        """
        AnimatedSprite.update(self, game)
        if self.index >= 4:
            self.parent.image.set_alpha(0)
        if self.index == 7:
            pygame.sprite.Sprite.kill(self.parent)
            pygame.sprite.Sprite.kill(self)

    def render(self, screen):
        """
        рендер
        :param screen: экран
        """
        screen.blit(self.image, (self.parent.rect.x - self.offset[0], self.parent.rect.y -
                                 self.offset[1]))


class PlayerBodyParts(AnimatedSprite):
    """
    класс частей тела персонажа
    """

    def __init__(self, images_paths, coords, parent, animation_speed: float = 1):
        AnimatedSprite.__init__(self, images_paths, coords)

        self.parent = parent

        self.right_sprites = self.action_sprites
        self.left_sprites = dict()
        self.animation_speed = animation_speed * 0.1

        for action, images in self.action_sprites.items():
            rotated_images = [pygame.transform.flip(i, True, False) for i in
                              self.action_sprites[action]]
            self.left_sprites[action] = rotated_images

    def start(self, action='idle'):
        """
        Начинает воспроизводить анимацию
        :param action: действие, по которому будет начат анимация
        """

        if action != self.current_action and (not self.is_started() or (not (
            self.current_action in ('walking-up', 'walking-down') and action ==
           'walking-x') or self.parent.direction_y is None)):
            self.change_current_action(action)
            self._started = True
            self._index = 0

    def update(self, game):
        """
        обновление
        :param game: игра
        """
        AnimatedSprite.update(self, game)

    def calc(self, game):
        self.parent.calc(game)


class Tears(SpriteObject, PhysicalCreature, CanHurtObject):
    """
    класс слез
    """

    def __init__(self, coords, team, game, direction_x=None, direction_y=None, ammo_speed=5,
                 dx=None, dy=None):
        from creatures import Player, EnemyBlob, EnemyMosquito
        SpriteObject.__init__(self, 'assets/weapons/ammo-1.png', coords)
        self.coords = list(coords)
        self.start_coords = coords
        if direction_x == 'left':
            self.speed_x = -ammo_speed
        elif direction_x == 'right':
            self.speed_x = ammo_speed
        else:
            self.speed_x = 0

        if direction_y == 'up':
            self.speed_y = -ammo_speed
        elif direction_y == 'down':
            self.speed_y = ammo_speed
        else:
            self.speed_y = 0
        if dx or dy:
            self.speed_y = dy * ammo_speed * -1
            self.speed_x = dx * ammo_speed * -1

        self.transparent_num = 255

        game.ammos.add(self)
        self.game = game
        self.explosion = Explosion(self, self.coords, (self.image.get_width() / 2 + 15,
                                                       self.image.get_height() / 2 + 10), 0.3)
        self.is_killed = False
        self.hit_box = self.rect
        self.team = team
        if team == 'player':
            self.team_list = [Player]
        elif team == 'enemy':
            self.team_list = [EnemyBlob, EnemyMosquito]

        self.damage = 1
        self.one_punch_object = True

    def move(self):
        """
        передвижение
        """
        if (abs(self.start_coords[0] - self.coords[0]) > 400
           or abs(self.start_coords[1] - self.coords[1]) > 400):
            self.explosion.explode()
        self.coords = int(self.coords[0] + self.speed_x), int(self.coords[1] + self.speed_y)
        self.rect.x, self.rect.y = self.coords[0], self.coords[1]

    def update(self, game):
        """
        обновление
        :param game: игра
        """
        PhysicalCreature.update(self, game)
        self.explosion.update(game)
        self.move()
        self.hit_box = self.rect

    def render(self, screen):
        """
        рендеринг объекта
        :param screen: объект экрана
        """
        screen.blit(self.image, self.rect)
        if self.is_killed:
            self.explosion.explode()
            self.explosion.render(screen)

    def on_collision(self, collided_sprite, game):
        """
        действие при столкновении с объектом
        :param collided_sprite: с чем столкнулось
        :param game: объект игры
        """
        if not isinstance(collided_sprite, Tears):
            self.speed_y = 0
            self.speed_x = 0
            self.is_killed = True

    def on_collision_with_physical_creature(self, collided_sprite):
        """
        При столкновении с живым существом
        :param collided_sprite: с чем столкнулось
        """
        if self.team != collided_sprite.team and not isinstance(collided_sprite, Tears):
            collided_sprite.get_hurt(self)
            self.speed_y = 0
            self.speed_x = 0
            self.is_killed = True

    def kill(self):
        """
        действие для уничтожения спрайта
        """
        self.explosion.explode()


class Rock(SpriteObject, PhysicalObject, CantHurtObject):
    """
    класс камня
    """

    def __init__(self, coords):
        SpriteObject.__init__(self, image_path='assets/room/room_rock.png',
                              coords=coords)
        CantHurtObject.__init__(self)
        self.coords = coords
        self.mask_rect = self.rect
        PhysicalObject.__init__(self)

    def update(self, game):
        """
        Обновление объекта
        :param game: объект игры
        """
        SpriteObject.update(self, game)
        PhysicalObject.update(self, game)

    def render(self, screen):
        """
        рендер
        :param screen: объект экрана
        """
        screen.blit(self.image, self.rect)
