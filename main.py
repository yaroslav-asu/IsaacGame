import os
from abc import abstractmethod
from pprint import pprint
from collections import defaultdict
from typing import List, Dict, Tuple
from core import PhysicalSprite, PlayerBodyParts
import pygame


def load_image(directory, path, size=None):
    full_path = os.path.join(directory, path) if directory is not None else path

    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"Unable to find path to image: {full_path}")
    image = pygame.image.load(full_path)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


class RenderableObject:
    """
    Абстракный класс для описание минимального элемента, который может быть отображён на экране
    """

    def render(self, screen: pygame.Surface):
        """
        Выполняется каждрый раз при отрисовке кадра.

        Его необходимо переопределить
        :param screen: полотно для отрисовки
        :return:
        """
        pass

    def setup(self, game: 'Game'):
        """
        Вызывается при создании объекта
        :param game: полотно для отрисовки
        """
        pass

    def update(self, game: 'Game'):
        """
        Итерация игры, обновляющая состояние объекта
        :param game:
        :return:
        """
        pass


class SpriteGroup(RenderableObject, pygame.sprite.Group):
    """
    Класс для отрисовки группы спрайтов. Сами по себе спрайты недоступны для отрисовки и
    подлежат группировке в набор объектов, который уже может быть отрисован
    """

    def setup(self, game: 'Game'):
        pass

    def update(self, game: 'Game'):
        pygame.sprite.Group.update(self, game)

    def render(self, screen: pygame.Surface):
        self.draw(screen)


class Game:
    def __init__(self, width: int = 959, height: int = 540, name: str = 'Esaac', fps: int = 60):
        pygame.init()
        pygame.display.set_caption(name)

        self.screen = pygame.display.set_mode((width, height))
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = fps

        self.player = Player((479, 270))
        self.rock = Rock((400, 270))
        self.objects = []
        self.physical_group = [self.rock, self.player]
        self.groups = []

        self.background = load_image('assets/room', 'room-background.png')
        self._handlers = defaultdict(list)

        self.add_handler(pygame.KEYDOWN, self.player.key_press_handler)
        self.add_handler(pygame.KEYUP, self.player.stop_move)

        group = SpriteGroup()
        for obj in self.physical_group:
            group.add(obj)

        self.add_object(group)

    def add_object(self, obj):
        """
        Добавляет объект для отрисовки на экран.

        Должен быть экземпляром класса или наследника класса RenderableObject
        :param obj: созданный объект для отрисовки
        """
        self.objects.append(obj)
        if isinstance(obj, SpriteGroup):
            self.groups.append(obj)

    def run(self):
        while self.running:
            self.screen.blit(self.background, (0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                for handler in self._handlers.get(event.type, []):
                    handler(event)
            # self.player.key_press_handler()
            self.player.attack()
            self.update()
            self.objects += self.player.ammos_list

            self.draw()

            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

    def draw(self):
        for obj in self.objects:
            for i in obj:
                i.render(self.screen)

    def add_handler(self, event_type, handler):
        self._handlers[event_type].append(handler)

    def update(self):
        for obj in self.objects:
            obj.update(self)

    def get_groups(self):
        return self.groups


class SpriteObject(pygame.sprite.Sprite):
    """
    Класс для работы со спрайтом. Любой спрайт ассоциируются с некоторым изображением,
    поэтому для урпощения жизни были добавлены параметры для создания изображения вместе с спрайтом
    """

    def __init__(self, image_path: str, coords: Tuple[int, int], size: Tuple[int, int] = None,
                 image_dir: str = 'assets', *groups: pygame.sprite.AbstractGroup):
        super().__init__(*groups)
        self.image_dir = image_dir
        self.image_path = image_path
        self.size = size
        self.coords = coords

        self.image = load_image(image_path, image_dir, size)
        self.rect = pygame.Rect(coords[0], coords[1], *self.image.get_size())

    def update(self, game: 'Game'):
        self.rect = pygame.Rect(self.coords[0], self.coords[1], *self.image.get_size())


class PlayerAmmo:
    def __init__(self, coords, direction_x, direction_y, ammo_speed=0.01):
        self.coords = coords[0], coords[1]
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

        self.image = load_image('assets', 'player/ammo/ammo-1.png')
        self.rect = pygame.Rect(self.coords[0] - self.image.get_width() / 2, self.coords[1] -
                                self.image.get_height() / 2,
                                *self.image.get_size())

    def move(self):
        self.coords = self.coords[0] + self.speed_x, self.coords[1] + self.speed_y

    def update(self, game):
        self.move()
        self.rect = pygame.Rect(self.coords[0] - self.image.get_width() / 2, self.coords[1] -
                                self.image.get_height() / 2,
                                *self.image.get_size())

    def render(self, screen):
        screen.blit(self.image, self.rect)


class Player(PhysicalSprite):
    def __init__(self, coords: tuple, *groups):
        PhysicalSprite.__init__(self, *groups)

        head_sprite_map: Dict[str, List[str]] = dict()
        for action_folder in ('idle', 'walking-x', 'walking-down', 'walking-up', 'attack-x',
                              'attack-up', 'attack-down'):
            head_sprite_map[action_folder] = [f'player/head/{action_folder}/{i}' for i in
                                              os.listdir(f'assets/player/head/{action_folder}')]

        body_sprite_map: Dict[str, List[str]] = dict()
        for action_folder in ('idle', 'walking-x', 'walking-down', 'walking-up'):
            body_sprite_map[action_folder] = [f'player/body/{action_folder}/{i}' for i in
                                              os.listdir(f'assets/player/body/{action_folder}')]

        self.head_sprite = PlayerBodyParts(head_sprite_map, (coords[0] - 10, coords[1] - 39), self)

        self.body_sprite = PlayerBodyParts(body_sprite_map, coords, self)

        self.x, self.y = coords
        self.direction_x = None
        self.direction_y = None

        self.speed = 6

        self.sliding_time = 0
        self.action_sprites = dict()

        self.ammos_list = list()

        self.attack_speed: float = 0.05
        self.attack_delay = 0

        self.image = pygame.Surface((90, 90))
        self.image.fill((0, 255, 0))
        self.image.set_colorkey((0, 255, 0))
        self.image.blit(self.body_sprite.image, (10, 39 + self.head_sprite.image.get_height()))
        self.image.blit(self.head_sprite.image, (0, self.head_sprite.image.get_height()))

        self.render_rect = pygame.Rect(*coords, self.body_sprite.image.get_width(),
                                       self.body_sprite.image.get_height() +
                                       self.head_sprite.image.get_height())

        self.rect = pygame.Rect(coords[0] + 12, coords[1] + self.head_sprite.image.get_height() - 3,
                                self.body_sprite.image.get_width() - 4,
                                self.body_sprite.image.get_height() - 8)

        self.collision_direction = None
        # self.rect = pygame.Rect(coords[0], coords[1],
        #                                     *self.body_sprite.image.get_size())
        # self.image = self.body_sprite.image

    def key_press_handler(self, event):
        if event.key == pygame.K_a:
            self.direction_x = 'left'

        elif event.key == pygame.K_d:
            self.direction_x = 'right'

        if event.key == pygame.K_w:
            self.direction_y = 'up'
        elif event.key == pygame.K_s:
            self.direction_y = 'down'

    def stop_move(self, event):
        keys = pygame.key.get_pressed()
        for i in [zip((pygame.K_a, pygame.K_d), ('left', 'right')),
                  zip((pygame.K_w, pygame.K_s), ('up', 'down'))]:
            i = list(i)
            if keys[i[0][0]] and not keys[i[1][0]]:
                self.direction_x = i[0][1]
            elif keys[i[1][0]] and not keys[i[0][0]]:
                self.direction_x = i[1][1]
        if not len(list(filter(lambda x: x, [keys[pygame.K_a], keys[pygame.K_d]]))):
            self.direction_x = None
        if not len(list(filter(lambda x: x, [keys[pygame.K_s], keys[pygame.K_w]]))):
            self.direction_y = None

        if not len(list(filter(lambda x: x, [keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_s],
                                             keys[pygame.K_w]]))):
            self.head_sprite.start('idle')
            self.body_sprite.start('idle')

    def render(self, screen):
        screen.blit(self.image, self.render_rect)
        a = pygame.Surface((self.rect.width, self.rect.height))
        a.fill((0, 0, 100))
        a.set_alpha(230)
        screen.blit(a, self.rect)

    def update(self, game):
        if self.direction_x == 'left':
            for element in (self.head_sprite, self.body_sprite):
                element.action_sprites = element.left_sprites
                element.start(action='walking-x')
        elif self.direction_x == 'right':
            for element in (self.head_sprite, self.body_sprite):
                element.action_sprites = element.right_sprites
                element.start(action='walking-x')
        if self.direction_y == 'up':
            for element in (self.head_sprite, self.body_sprite):
                element.start(action='walking-up')
        elif self.direction_y == 'down':
            for element in (self.head_sprite, self.body_sprite):
                element.start(action='walking-down')

        self.move(self.direction_x, self.direction_y, self.collision_direction)
        self.body_sprite.update(game)
        self.head_sprite.update(game)

        self.image = pygame.Surface((300, 300))
        self.image.fill((0, 255, 0))
        self.image.set_colorkey((0, 255, 0))
        self.image.blit(self.body_sprite.image, (10, 39))
        self.image.blit(self.head_sprite.image, (0, 0))

        PhysicalSprite.update(self, game)

    def move(self, direction_x, direction_y, collision_direction):
        if direction_x == 'left' and not collision_direction == 'left':
            self.rect.move_ip(-self.speed, 0)
            self.render_rect.move_ip(-self.speed, 0)
        elif direction_x == 'right' and not collision_direction == 'right':
            self.rect.move_ip(self.speed, 0)
            self.render_rect.move_ip(self.speed, 0)
        if direction_y == 'up' and not collision_direction == 'up':
            self.rect.move_ip(0, -self.speed)
            self.render_rect.move_ip(0, -self.speed)
        elif direction_y == 'down' and not collision_direction == 'down':
            self.rect.move_ip(0, self.speed)
            self.render_rect.move_ip(0, self.speed)

    def attack(self):
        self.attack_delay += self.attack_delay + self.attack_speed * 0.1
        if self.attack_delay < 1:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.head_sprite.action_sprites = self.head_sprite.left_sprites
            self.head_sprite.start(action='attack-x', speed=1)
            self.ammos_list.append(PlayerAmmo(self.head_sprite.rect.center, 'left',
                                              self.direction_y))
            self.attack_delay = 0
        elif keys[pygame.K_RIGHT]:
            self.head_sprite.action_sprites = self.head_sprite.right_sprites
            self.head_sprite.start(action='attack-x', speed=1)
            self.ammos_list.append(PlayerAmmo(self.head_sprite.rect.center, 'right',
                                              self.direction_y))
            self.attack_delay = 0
        elif keys[pygame.K_UP]:
            self.head_sprite.start(action='attack-up', speed=1)
            self.ammos_list.append(PlayerAmmo(self.head_sprite.rect.center, self.direction_x,
                                              'up'))
            self.attack_delay = 0
        elif keys[pygame.K_DOWN]:
            self.head_sprite.start(action='attack-down', speed=1)
            self.ammos_list.append(PlayerAmmo(self.head_sprite.rect.center, self.direction_x,
                                              'down'))
            self.attack_delay = 0

    def on_collision(self, collided_sprite, game):
        if collided_sprite.rect.left < self.rect.right < collided_sprite.rect.right and \
                collided_sprite.rect.top < self.rect.bottom and self.rect.top < \
                collided_sprite.rect.bottom:
            self.collision_direction = 'right'
        elif collided_sprite.rect.right > self.rect.left > collided_sprite.rect.left and \
                collided_sprite.rect.top < self.rect.bottom and self.rect.top < \
                collided_sprite.rect.bottom:
            self.collision_direction = 'left'
        if collided_sprite.rect.bottom > self.rect.top > collided_sprite.rect.top and \
                collided_sprite.rect.left < \
                self.rect.centerx < collided_sprite.rect.right:
            self.collision_direction = 'up'
        elif collided_sprite.rect.top < self.rect.bottom and collided_sprite.rect.left < \
                self.rect.centerx < collided_sprite.rect.right:
            self.collision_direction = 'down'


    def calc(self, game):
        self.collision_direction = None


class Rock(SpriteObject, PhysicalSprite):
    def __init__(self, coords, *groups):
        PhysicalSprite.__init__(self, *groups)
        SpriteObject.__init__(self, image_path='assets', image_dir='room/room_rock.png',
                              coords=coords)
        self.coords = coords

    def update(self, game):
        SpriteObject.update(self, game)
        PhysicalSprite.update(self, game)

    def render(self, screen):
        screen.blit(self.image, self.rect)

    # def on_collision(self, collided_sprite, game):
    #     if isinstance(collided_sprite, PlayerBodyParts):
    #         collided_sprite.parent.direction_x = None
    #         collided_sprite.parent.direction_y = None


if __name__ == '__main__':
    game = Game
    game().run()
