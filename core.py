from collections import defaultdict
from random import random
from typing import Tuple, Any
import pygame
import os


def load_image(path, size=None):
    """
    загрузка изображения
    :param path: путь к файлу
    :param size: размер выходного изображения
    :return: изображение
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find path to image: {path}")
    image = pygame.image.load(path)
    if isinstance(size, float) or isinstance(size, int):
        size = list(map(lambda x: int(x * size), image.get_size()))
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


def get_rect_from_mask(mask):
    """
    получение rect из маски объекта
    :param mask: маска объекта
    :return: объект rect
    """
    outline = mask.outline()
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


def check_doors(default_door_position, room):
    """
    проверяет существует ли дверь в соседней комнате из которой должен будет выйти персонаж
    :param default_door_position: положение двери
    :param room: объект комнаты
    :return: bool
    """
    if (default_door_position == 'any' and any(room.doors_list)) or \
        (default_door_position == 'left' and room.doors_list[1]) or \
        (default_door_position == 'right' and room.doors_list[3]) or \
        (default_door_position == 'up' and room.doors_list[0]) or \
       (default_door_position == 'down' and room.doors_list[2]):
        return False
    return True


class Game:
    room: Any
    interface: Any
    objects: list
    groups: list
    physical_group: Any
    player_group: Any
    items: Any
    creatures: Any
    ammos: Any
    gameover: bool
    background: Any
    rooms_seeds_dict: dict
    player: Any
    """класс комнаты"""

    def __init__(self, width: int = 959, height: int = 540, name: str = 'Esaac', fps: int = 60):
        pygame.init()
        pygame.display.set_caption(name)

        self.screen = pygame.display.set_mode((width, height))
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = fps
        self._handlers = defaultdict(list)

        self.add_handler(pygame.KEYDOWN, self.player.key_press_handler)
        self.add_handler(pygame.KEYUP, self.player.stop_move)

    def add_object(self, obj):
        """
        Добавляет объект для отрисовки на экран.

        :param obj: созданный объект для отрисовки
        """
        self.objects.append(obj)
        if isinstance(obj, SpriteGroup) and obj != self.interface:
            self.groups.append(obj)

    def gameover_render(self):
        """
        сообщение при смерти персонажа
        """
        self.screen.fill((40, 40, 40))
        Text(f'Вы умерли, может быть вам повезет в другой раз',
             (160, 220), 50, (255, 255, 255)).render(self.screen)
        Text(f'Пройдено комнат: {len(self.rooms_seeds_dict.keys()) - 1}', (350, 260),
             50, (255, 255, 255)).render(self.screen)

    def run(self):
        """
        главный цикл программы
        """
        while self.running:
            if not self.gameover:
                self.screen.blit(self.background, (0, 0))
            else:
                self.gameover_render()

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
        """
        отрисока объектов на экран
        """
        for obj in self.objects:
            if isinstance(obj, SpriteGroup):
                for i in obj:
                    i.render(self.screen)
            else:
                obj.render(self.screen)

    def add_handler(self, event_type, handler):
        """
        добавление обработчика нажатий на кнопки
        :param event_type: тип кнопки
        :param handler: функция обработчик
        """
        self._handlers[event_type].append(handler)

    def update(self):
        """
        обновление всех объектов
        """
        for obj in self.objects:
            obj.update(self)

    def get_groups(self):
        """получение всех групп"""
        return self.groups

    def create_new_room(self, coords, default_door_position):
        """
        создание новой комнаты
        :param coords: ее координаты
        :param default_door_position: дверь которая должна быть у двери
        """
        from room import Room
        room = Room(coords, self)
        no_default_door = check_doors(default_door_position, room)
        while no_default_door:
            self.rooms_seeds_dict.pop(coords)
            room = Room(coords, self)
            no_default_door = check_doors(default_door_position, room)

        self.room = room
        self.room.coords = coords
        self.objects = []
        self.groups = []
        self.physical_group = SpriteGroup()
        self.player_group = SpriteGroup(self.player)
        self.items = SpriteGroup()
        self.creatures = SpriteGroup()
        self.ammos = SpriteGroup()
        for obj in [self.room, self.physical_group, self.items, self.ammos, self.interface,
                    self.creatures, self.player_group]:
            self.add_object(obj)

    def end_game(self):
        """
        событие по завершении игры
        """
        self.objects = []
        self.groups = []
        self.gameover = True


class ItemsSpawner:
    mask_rect: pygame.Rect
    """класс объектов которые создают вещи, которые можно подбирать"""
    def __init__(self):
        self.item_spawned = False

    def spawn_items(self, items_list, game):
        """
        спавн предметов
        :param items_list: список вещей
        :param game: объект игры
        """
        if not self.item_spawned:
            for i in items_list:
                if random() < i[1]:
                    game.items.add(i[0](self.mask_rect.center))
                    self.item_spawned = True
                    return
            self.item_spawned = True


class CantHurtObject:
    """объект который не  может бить """
    def __init__(self):
        self.can_hurt = False


class CanHurtObject:
    """объект который может бить """
    def __init__(self):
        self.can_hurt = True


class RenderableObject:
    """
    Абстракный класс для описание минимального элемента, который может быть отображён на экране
    """

    def render(self, screen):
        """
        рендеринг объекта
        :param screen: экран
        """
        pass

    def setup(self, game):
        """
        создание объекта
        :param game: полотно для отрисовки
        """
        pass

    def update(self, game):
        """
        обновление объекта
        :param game: объект игры
        """
        pass


class SpriteGroup(RenderableObject, pygame.sprite.Group):
    """
    Класс для отрисовки группы спрайтов
    """

    def setup(self, game):
        """
        Установка спрайта
        :param game: класс игры
        """
        pass

    def update(self, game):
        """
        обновление
        :param game: игра
        """
        pygame.sprite.Group.update(self, game)

    def render(self, screen: pygame.Surface):
        self.draw(screen)

    def extend(self, obj_list):
        """
        помещение групп из списка в отрисовку
        :param obj_list: список
        """
        for obj in obj_list:
            self.add(obj)


class Text(RenderableObject):
    text_surface: Any
    """
    Обёртка вокруг текста для более удобной отрисовке на экране
    """

    def __init__(self, text, pos, font_size=20, color=(40, 40, 40)):
        """
        :param text: стартовый текст для отрисовки
        :param pos: кортеж с координатами верхнего левого угла текста
        :param font_size: размер шрифта
        :param color: цвет для отрисовки
        """
        pygame.font.init()
        self.color = color
        self.pos = pos
        self.__text = text
        self.__freeze = False
        self.rect = pygame.Rect
        self.font = pygame.font.Font('assets/Thintel.ttf', font_size)
        self.setup()

    def render(self, screen):
        screen.blit(self.text_surface, self.pos)

    def freeze(self):
        """
        Замораживает текст, запрещая его изменять до момента разморозки
        """
        self.__freeze = True

    def unfreeze(self):
        """
        Снимает заморозку текста, позволяя его изменять
        :return:
        """
        self.__freeze = False

    def set_text(self, text):
        """
        Назначает текст для отрисовки
        :param text: текст, который будет отображён на экране
        """
        if self.__freeze:
            return
        self.__text = text

        self.text_surface = self.font.render(self.__text, False, self.color)

    def setup(self, **kwargs):
        """
        Инициализация текста для отрисовки
        """
        self.text_surface = self.font.render(self.__text, False, self.color)

    def add_internal(self, arg):
        pass


class SpriteObject(pygame.sprite.Sprite):
    """
    Класс для работы со спрайтом. Любой спрайт ассоциируются с некоторым изображением,
    поэтому для урпощения жизни были добавлены параметры для создания изображения вместе с спрайтом
    """

    def __init__(self, image_path, coords, size= None):
        super().__init__()
        self.image_path = image_path
        self.size = size
        self.coords = coords

        self.image = load_image(image_path, size)
        self.rect = pygame.Rect(coords[0], coords[1], *self.image.get_size())
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = get_rect_from_mask(self.mask)

    def update(self, game: 'Game'):
        self.rect = pygame.Rect(self.coords[0], self.coords[1], *self.image.get_size())

    def render(self, screen):
        screen.blit(self.image, self.rect)


class PhysicalObject(pygame.sprite.Sprite):
    """
    физический объект
    """
    def __init__(self):
        super().__init__()


class PhysicalCreature(pygame.sprite.Sprite):
    collision_direction_x: Any
    collision_direction_y: Any
    """
    физическое существо
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        self.mask_rect = pygame.Rect
        self.is_collision_direction_x_changed = False
        self.is_collision_direction_y_changed = False

    def update(self, game):
        """обновление"""
        collision = False
        self.is_collision_direction_x_changed = False
        self.is_collision_direction_y_changed = False
        for objects_group in game.get_groups():
            for obj in objects_group:
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

                if not isinstance(collided, PhysicalObject) and not \
                   isinstance(collided, PhysicalCreature):
                    continue

                if collided is not self:
                    if isinstance(collided, PhysicalCreature):
                        self.on_collision_with_physical_creature(collided)
                    else:
                        self.on_collision(collided, game)
                    collision = True
        if collision:
            if not self.is_collision_direction_x_changed:
                self.collision_direction_x = None
            if not self.is_collision_direction_y_changed:
                self.collision_direction_y = None
        else:
            self.absence_collision(game)

    def on_collision(self, collided_sprite, game):
        """
        действие на сколкновение
        :param collided_sprite: с чем столкнулось
        :param game: игра
        """
        if collided_sprite.mask_rect.left <= self.mask_rect.right < \
            collided_sprite.mask_rect.right \
            and not self.mask_rect.left > collided_sprite.mask_rect.left and \
            collided_sprite.mask_rect.top < self.mask_rect.bottom and self.mask_rect.top < \
           collided_sprite.mask_rect.bottom:
            self.collision_direction_x = 'right'
            self.is_collision_direction_x_changed = True

        elif collided_sprite.mask_rect.right > self.mask_rect.left > collided_sprite.mask_rect.left \
            and not self.mask_rect.right < collided_sprite.mask_rect.right and \
            collided_sprite.mask_rect.top < self.mask_rect.bottom and self.mask_rect.top < \
           collided_sprite.mask_rect.bottom:
            self.collision_direction_x = 'left'
            self.is_collision_direction_x_changed = True

        if collided_sprite.mask_rect.bottom > self.mask_rect.top > \
            collided_sprite.mask_rect.bottom - 20 and \
            collided_sprite.mask_rect.left < self.mask_rect.right and \
           collided_sprite.mask_rect.right > self.mask_rect.left:
            self.collision_direction_y = 'up'
            self.is_collision_direction_y_changed = True

        elif collided_sprite.mask_rect.top < self.mask_rect.bottom < \
            collided_sprite.mask_rect.top + 20 and \
            collided_sprite.mask_rect.left < self.mask_rect.right and \
           collided_sprite.mask_rect.right > self.mask_rect.left:
            self.collision_direction_y = 'down'
            self.is_collision_direction_y_changed = True

    def on_collision_with_physical_creature(self, collided_object):
        """действие при столкновении с живым существом"""
        pass

    def absence_collision(self, game):
        """действие при отсутствии коллизии"""
        self.collision_direction_x = None
        self.collision_direction_y = None


class HeartsIncludedCreature:
    image: pygame.image
    mask: pygame.mask
    coords: Any
    hurt_delay: float
    """существо с хп"""
    def __init__(self, team, health):
        self.team = team
        self.already_hurt_by = set()
        self.show_hurt_surface = pygame.Surface(self.image.get_size())
        self.show_hurt_surface.fill((0, 255, 0))
        self.show_hurt_surface.set_colorkey((0, 255, 0))
        self.is_hurt = False
        self.hurt_delay = 0
        self.max_health = health
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
                            pass
                        else:
                            continue
                    else:
                        hurt = False
                except AttributeError:
                    hurt = False

                if not hurt:
                    self.absence_hurt()

    def get_hurt(self, hurt_object):
        """
        получить урон
        :param hurt_object: от чего получить урон
        """
        self.is_hurt = True
        self.health -= hurt_object.damage
        if hurt_object.one_punch_object:
            self.already_hurt_by.add(hurt_object)
        self.hurt_delay = 0

    def absence_hurt(self):
        """
        действие при отсутсвии урона
        """
        pass

    def show_hurt(self, screen, color=(255, 0, 0), alpha=60):
        """
        показать удар
        :param screen: экран
        :param color: цвет
        :param alpha: прозрачность
        """
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
        """
        разрезание картинки на кадры
        :param sheet: картинка для разрезания
        :param columns: склоько столбцов
        :param rows: сколько колонок
        """

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
                 size=1, current_action='idle', animation_speed: float = 1, color_key=None):
        super().__init__()

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
