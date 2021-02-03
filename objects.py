from core import *
from creatures import *


class Explosion(AnimatedSprite):
    def __init__(self, parent, coords, offset, size, animation_speed=1):
        explosion_animation = {'explosion':
                                   [f'assets/explosions/explosion-1/{file_name}' for file_name in
                                    os.listdir('assets/explosions/explosion-1')], 'wait': [
            f'assets/explosions/explosion-1/{os.listdir("assets/explosions/explosion-1")[0]}']}
        AnimatedSprite.__init__(self, explosion_animation, coords, size, 'wait', animation_speed,
                                (68, 36, 52))
        self.parent = parent
        self.offset = offset

    def explode(self):
        self.start('explosion')
        self.parent.is_killed = True
        self.parent.is_invisible = True

    def update(self, game):
        AnimatedSprite.update(self, game)
        if self.index == 4:
            self.parent.image.set_alpha(0)
        elif self.index == 7:
            pygame.sprite.Sprite.kill(self.parent)
            pygame.sprite.Sprite.kill(self)

    def render(self, screen):
        screen.blit(self.image, (self.parent.rect.x - self.offset[0], self.parent.rect.y -
                                 self.offset[1]))


class PlayerBodyParts(AnimatedSprite, PhysicalSprite):
    def __init__(self, images_paths, coords, parent, animation_speed: float = 1, *groups):
        AnimatedSprite.__init__(self, images_paths, coords)
        PhysicalSprite.__init__(self, *groups)
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
        :param speed: скорость воспроизведения анимации
        :return:
        """

        if action != self.current_action and (not self.is_started() or (not (
            self.current_action in ('walking-up', 'walking-down') and action ==
            'walking-x') or self.parent.direction_y is None)):
            self.change_current_action(action)
            self._started = True
            self._index = 0

    def update(self, game):
        AnimatedSprite.update(self, game)

    def calc(self, game):
        self.parent.calc(game)


class Tears(SpriteObject, PhysicalSprite, CanHurtObject):
    def __init__(self, coords, team, game, direction_x=None, direction_y=None, ammo_speed=5,
                 dx=None, dy=None):
        from creatures import Player, EnemyBlob, EnemyMosquito
        SpriteObject.__init__(self, 'assets/player/ammo/ammo-1.png', coords)
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
        if (abs(self.start_coords[0] - self.coords[0]) > 400
            or abs(self.start_coords[1] - self.coords[1]) > 400):
            # print(self.is_killed)
            self.explosion.explode()
        self.coords = int(self.coords[0] + self.speed_x), int(self.coords[1] + self.speed_y)
        self.rect.x, self.rect.y = self.coords[0], self.coords[1]

    def update(self, game):
        PhysicalSprite.update(self, game)
        self.explosion.update(game)
        self.move()
        self.hit_box = self.rect

    def render(self, screen):
        screen.blit(self.image, self.rect)
        if self.is_killed:
            self.explosion.explode()
            self.explosion.render(screen)

    def on_collision(self, collided_sprite, game):
        if not any([isinstance(collided_sprite, team) for team in self.team_list]) and not \
            isinstance(collided_sprite, Tears):
            self.speed_y = 0
            self.speed_x = 0
            self.is_killed = True

    def kill(self):
        self.explosion.explode()


class Rock(SpriteObject, PhysicalSprite, CantHurtObject):
    def __init__(self, coords, *groups):
        PhysicalSprite.__init__(self, *groups)
        SpriteObject.__init__(self, image_path='assets/room/room_rock.png',
                              coords=coords)
        CantHurtObject.__init__(self)
        self.coords = coords
        self.mask_rect = self.rect

    def update(self, game):
        SpriteObject.update(self, game)
        PhysicalSprite.update(self, game)

    def render(self, screen):
        screen.blit(self.image, self.rect)

    def on_collision(self, collided_sprite, game):
        pass


class Walls(PhysicalSprite, CantHurtObject):
    def __init__(self):
        PhysicalSprite.__init__(self)
        CantHurtObject.__init__(self)
        self.rect = pygame.Rect(0, 0, 1000, 85)
        self.mask_rect = self.rect

    def update(self, game):
        PhysicalSprite.update(self, game)

    def render(self, screen):
        # pygame.draw.rect(screen, (0, 100, 0), self.rect)
        pass

    def on_collision(self, collided_sprite, game):
        pass
