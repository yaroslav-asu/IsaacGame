from collections import defaultdict
from typing import Tuple, Any
import pygame
import os


def load_image(path, size=None):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find path to image: {path}")
    image = pygame.image.load(path)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


def get_rect_from_mask(mask):
    outline = mask.outline()
    # width = max(outline, key=lambda x: x[0]) - min(outline, key=lambda x: x[0])
    # height = max(outline, key=lambda x: x[1]) - min(outline, key=lambda x: x[1])
    min_x = outline[0][0]
    min_y = outline[0][1]
    max_x = 0
    max_y = 0
    for i in outline:
        if i[0] > max_x:
            max_x = i[0]
        if i[0] < min_x:
            min_x = i[0]
        if i[1] > max_y:
            max_y = i[1]
        if i[1] < min_y:
            min_y = i[1]
    rect = pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
    return rect


class Game:

    def __init__(self, width: int = 959, height: int = 540, name: str = 'Esaac', fps: int = 60):
        from creatures import Player, EnemyBlob, EnemyMosquito
        from objects import Rock, Walls
        from uis import HealthBar
        pygame.init()
        pygame.display.set_caption(name)

        self.screen = pygame.display.set_mode((width, height))
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = fps

        self.player = Player((100, 50))
        self.rock_1 = Rock((400, 270))
        self.rock_2 = Rock((450, 250))
        # self.blob_1 = EnemyBlob((200, 100))
        self.blob_2 = EnemyBlob((100, 200))
        # self.blob_3 = EnemyBlob((300, 400))
        self.mosquito = EnemyMosquito((200, 200), 'big')

        self.wall = Walls()

        self.interface = SpriteGroup(HealthBar(self))
        self.objects = []
        self.physical_group = [self.rock_1, self.rock_2, self.wall]
        self.creatures = SpriteGroup(self.mosquito, self.player)
        self.groups = []
        self.ammos = SpriteGroup()

        self.background = load_image('assets/room/room-background.png')
        self._handlers = defaultdict(list)

        self.add_handler(pygame.KEYDOWN, self.player.key_press_handler)
        self.add_handler(pygame.KEYUP, self.player.stop_move)

        physical_group = SpriteGroup()
        for obj in self.physical_group:
            physical_group.add(obj)

        for obj in [physical_group, self.ammos, self.interface, self.creatures]:
            self.add_object(obj)

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
            self.update()

            self.draw()

            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

    def draw(self):
        for obj in self.objects:
            if isinstance(obj, SpriteGroup):
                for i in obj:
                    i.render(self.screen)
            else:
                obj.render(self.screen)

    def add_handler(self, event_type, handler):
        self._handlers[event_type].append(handler)

    def update(self):
        for obj in self.objects:
            obj.update(self)

    def get_groups(self):
        return self.groups


class CantHurtObject:
    def __init__(self):
        self.can_hurt = False


class CanHurtObject:
    def __init__(self):
        self.can_hurt = True


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

    def setup(self, game):
        """
        Вызывается при создании объекта
        :param game: полотно для отрисовки
        """
        pass

    def update(self, game):
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

    def setup(self, game):
        pass

    def update(self, game):
        pygame.sprite.Group.update(self, game)

    def render(self, screen: pygame.Surface):
        self.draw(screen)


class SpriteObject(pygame.sprite.Sprite):
    """
    Класс для работы со спрайтом. Любой спрайт ассоциируются с некоторым изображением,
    поэтому для урпощения жизни были добавлены параметры для создания изображения вместе с спрайтом
    """

    def __init__(self, image_path: str, coords: Tuple[int, int], size: Tuple[int, int] = None,
                 *groups: pygame.sprite.AbstractGroup):
        super().__init__(*groups)
        self.image_path = image_path
        self.size = size
        self.coords = coords

        self.image = load_image(image_path, size)
        self.rect = pygame.Rect(coords[0], coords[1], *self.image.get_size())

    def update(self, game: 'Game'):
        self.rect = pygame.Rect(self.coords[0], self.coords[1], *self.image.get_size())


class PhysicalSprite(pygame.sprite.Sprite):
    collision_direction_x: str
    collision_direction_y: str

    def __init__(self, *groups):
        super().__init__(*groups)
        self.mask_rect = pygame.Rect
        self.previously_collided = set()
        self.current_collided = set()

    def update(self, game):
        collision = False
        for physical_object in game.get_groups():
            for obj in physical_object:
                try:
                    if pygame.sprite.collide_mask(self, obj):
                        collided = obj
                    else:
                        continue
                except AttributeError:
                    if pygame.sprite.collide_rect(self, obj):
                        collided = obj
                    else:
                        continue

                if not isinstance(collided, PhysicalSprite):
                    continue
                if collided is not self:
                    collision = True
                    self.on_collision(collided, game)
        if not collision:
            self.absence_collision(game)

    def on_collision(self, collided_sprite, game):
        if collided_sprite.mask_rect.left <= self.mask_rect.right < \
            collided_sprite.mask_rect.right \
            and not self.mask_rect.left > collided_sprite.mask_rect.left and \
            collided_sprite.mask_rect.top < self.mask_rect.bottom and self.mask_rect.top < \
            collided_sprite.mask_rect.bottom:
            self.collision_direction_x = 'right'

        elif collided_sprite.mask_rect.right > self.mask_rect.left > collided_sprite.mask_rect.left and \
            not self.mask_rect.right < collided_sprite.mask_rect.right and \
            collided_sprite.mask_rect.top < self.mask_rect.bottom and self.mask_rect.top < \
            collided_sprite.mask_rect.bottom:
            self.collision_direction_x = 'left'

        if collided_sprite.mask_rect.bottom > self.mask_rect.top > collided_sprite.mask_rect.top and \
            collided_sprite.mask_rect.left < self.mask_rect.right and \
            collided_sprite.mask_rect.right > self.mask_rect.left:
            self.collision_direction_y = 'up'

        elif collided_sprite.mask_rect.top < self.mask_rect.bottom and collided_sprite.mask_rect.left < \
            self.mask_rect.centerx < collided_sprite.mask_rect.right:
            self.collision_direction_y = 'down'

    def absence_collision(self, game):
        self.collision_direction_x = None
        self.collision_direction_y = None

    def on_first_collision(self, collided_sprite, game):
        pass


class HeartsIncludedCreature:
    image: pygame.image
    mask: pygame.mask
    coords: Any
    hurt_delay: float

    def __init__(self, team, health):
        self.team = team
        self.already_hurt_by = set()
        self.show_hurt_surface = pygame.Surface(self.image.get_size())
        self.show_hurt_surface.fill((0, 255, 0))
        self.show_hurt_surface.set_colorkey((0, 255, 0))
        self.is_hurt = False
        self.hurt_delay = 0
        self.health = health

    def update(self, game):
        self.show_hurt_surface.fill((0, 255, 0))
        for physical_object in game.get_groups():
            for hurt_object in physical_object:
                try:
                    if pygame.sprite.collide_mask(self, hurt_object) and hurt_object is not self:
                        hurt = True
                        if hurt_object.one_punch_object:
                            self.get_hurt(hurt_object)
                        else:
                            continue
                    else:
                        hurt = False
                except AttributeError:
                    hurt = False

                if not hurt:
                    self.absence_hurt()

    def get_hurt(self, hurt_object):
        self.is_hurt = True
        self.health -= hurt_object.damage
        if hurt_object.one_punch_object:
            self.already_hurt_by.add(hurt_object)
        self.hurt_delay = 0

    def absence_hurt(self):
        pass

    def show_hurt(self, screen, color=(255, 0, 0), alpha=60):
        olist = self.mask.outline()
        self.show_hurt_surface.set_alpha(alpha)
        pygame.draw.polygon(self.show_hurt_surface, color, olist, 0)
        screen.blit(self.show_hurt_surface, self.coords)


class CutAnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, path, columns, rows, x, y, size: float = 1, speed: float = 1):
        super().__init__()
        self.frames = []
        size_tuple = tuple(int(i * size) for i in load_image(path).get_size())
        sheet = load_image(path, size_tuple)
        self.cut_sheet(sheet, columns, rows)
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.rect.move(x, y)
        self.__counter = 0
        self.animation_speed = speed

    def cut_sheet(self, sheet, columns, rows):

        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self, game):
        self.__counter += self.__counter + 1 * self.animation_speed
        if self.__counter >= 1:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.__counter = 0


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, images_paths, coords,
                 size=1, current_action='idle', animation_speed: float = 1, color_key=None,
                 *groups):
        super().__init__(*groups)

        self.action_sprites = dict()
        for action, paths in images_paths.items():
            if action not in self.action_sprites.keys():
                self.action_sprites[action] = []
            images = []
            for sprite_path in paths:
                if size:
                    size_tuple = tuple(int(i * size) for i in load_image(sprite_path).get_size())
                    images.append(load_image(sprite_path, size_tuple))
                else:
                    images.append(load_image(sprite_path))
            self.action_sprites[action] = images[:]

        self.animation_speed = animation_speed * 0.1
        self._started = False
        self.__counter = 0
        self._index = 0
        self.current_action = current_action
        self.coords = coords
        self.color_key = color_key

        self.image = self.action_sprites[self.current_action][self._index]
        if color_key:
            self.image.set_colorkey(color_key)
        self.rect = pygame.Rect(self.coords[0], self.coords[1], *self.image.get_size())
        self.mask_rect = self.rect

    def start(self, action='idle'):
        """
        Начинает воспроизводить анимацию
        :param action: действие, по которому будет начат анимация
        :param speed: скорость воспроизведения анимации
        :return:
        """

        if action != self.current_action:
            self.change_current_action(action)
            self._started = True

            self._index = 0

    def change_current_action(self, action):
        self.current_action = action

    def stop_animation(self):
        """
        Останавливает воспроизведение анимации
        """
        self._started = False

    def is_started(self):
        """
        Проверка на то, запущена ли анимация
        :return:
        """
        return self._started

    def update(self, game):
        """
        Простенький вариант для работы анимации
        """
        if self.is_started():
            self.__counter += self.__counter + 1 * self.animation_speed

            if self.__counter >= 1:
                self._index = (self._index + 1) % len(self.action_sprites[self.current_action])
                self.__counter = 0
            self.image = self.action_sprites[self.current_action][self._index]
            if self.color_key:
                self.image.set_colorkey(self.color_key)

    @property
    def index(self):
        return self._index
