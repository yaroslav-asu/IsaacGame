from random import randint
import random
import pygame
from core import SpriteObject, load_image, CantHurtObject, SpriteGroup, PhysicalObject
from time import time
from objects import Rock
from creatures import EnemyBlob, EnemyMosquito


def rotate_center(image, angle):
    """
    Поворот картинки по центру на данный угол
    :param image:картинка
    :param angle:угол
    :return:картинка
    """
    rotated_image = pygame.transform.rotate(image, angle)
    return rotated_image


class BackGround(SpriteObject):
    """класс заднего фона"""
    def __init__(self):
        image_path = 'assets/room/room-background.png'
        SpriteObject.__init__(self, image_path, (0, 0))


class Room(SpriteGroup):
    doors_list: list
    """класс комнаты"""
    def __init__(self, coords, game):
        SpriteGroup.__init__(self)
        self.coords = coords
        self.mosquito_counter = 0
        self.blob_counter = 0
        self.setup_walls()
        self.objects_list = []
        self.enemy_group = SpriteGroup()
        if coords not in game.rooms_seeds_dict.keys():
            self.seed = coords[0] + coords[1] + int(time() * 1000 % 1000000)
            game.rooms_seeds_dict[coords] = self.seed
            self.setup_objects(self.seed)
            self.setup_enemies(self.objects_list, self.seed)
        else:
            self.seed = game.rooms_seeds_dict[coords]
            self.setup_objects(self.seed)
        self.setup_doors(self.seed)

    def setup_doors(self, seed):
        """
        установка дверей
        :param seed: сид комнаты
        """
        random.seed(seed)
        doors_list = [randint(0, 1) for i in range(4)]
        doors_coords_list = [(450, 25), (80, 210), (450, 455), (820, 210)]
        self.doors_list = list(map(lambda x: bool(x), doors_list))
        for i in range(len(self.doors_list)):
            if self.doors_list[i]:
                door = Door(doors_coords_list[i])
                door.close()
                self.add(door)

    def setup_walls(self):
        """установка стен"""
        self.extend([Wall(*i) for i in [[(1000, 85), (0, 0)],
                                        [(135, 1000), (0, 0)],
                                        [(1000, 90), (0, 450)],
                                        [(135, 1000), (825, 0)]]])

    def setup_objects(self, seed):
        """
        установка объектов
        :param seed: сид комнаты
        """
        random.seed(seed)
        prev = 6
        for i in range(0, 360, 60):
            obj_list = []
            for j in range(0, 680, 85):
                if randint(0, 1):
                    number = randint(0, 6)
                    if prev != 0 and number == 0 and not (i == 0 or j == 0 or i == 300 or j == 595):
                        self.add(Rock((155 + j, 95 + i)))
                        obj_list.append(1)
                    else:
                        obj_list.append(0)
                    prev = number
                else:
                    obj_list.append(0)
            self.objects_list.append(obj_list)

    def setup_enemies(self, objects_list, seed):
        """
        установка комнаты
        :param objects_list: список расставленных объектов на карте
        :param seed: сид комнаты
        """
        random.seed(seed)
        for i in range(0, 6):
            for j in range(0, 8):
                if randint(0, 1) and not objects_list[i][j]:
                    number = randint(0, 6)
                    if number == 1 and self.blob_counter < 5:
                        blob = EnemyBlob((155 + j * 85 - 30, 95 + i * 60 - 45))
                        self.add(blob)
                        self.enemy_group.add(blob)
                        self.blob_counter += 1

                    elif number == 2 and self.mosquito_counter < 5:
                        if randint(0, 1):
                            size = 'small'
                            coords = (155 + j * 85, 95 + i * 60)
                        else:
                            size = 'big'
                            coords = (155 + j * 85 - 10, 95 + i * 60 - 10)
                        mosquito = EnemyMosquito(coords, size)
                        self.enemy_group.add(mosquito)
                        self.add(mosquito)
                        self.mosquito_counter += 1


class Wall(PhysicalObject, CantHurtObject):
    """класс комнаты"""
    def __init__(self, size, coords):
        PhysicalObject.__init__(self)
        CantHurtObject.__init__(self)
        self.rect = pygame.Rect(*coords, *size)
        self.mask_rect = self.rect

    def on_collision(self, collided_sprite, game):
        """
        действие при столкновении
        :param collided_sprite: с чем столкнулось
        :param game: игра
        """
        pass

    def render(self, screen):
        pass


class Door(SpriteObject):
    """класс двери"""
    def __init__(self, coords):
        image_path = 'assets/room/door-frame.png'
        SpriteObject.__init__(self, image_path, coords, 1.9)
        self.closed_door_image = load_image('assets/room/doors.png', 1.9)
        self.is_closed = False
        angle = 0
        if coords == (450, 25):
            angle = 0
            self.doors_coords = (self.rect.x + 20, self.rect.y + 14)
        elif coords == (80, 210):
            angle = 90
            self.doors_coords = (self.rect.x + 14, self.rect.y + 20)
        elif coords == (450, 455):
            angle = 180
            self.doors_coords = (self.rect.x + 20, self.rect.y + 5)
        elif coords == (820, 210):
            angle = -90
            self.doors_coords = (self.rect.x + 4, self.rect.y + 20)
        self.rotate(angle)
        self.room_created = False

    def render(self, screen):
        """
        рендеринг объекта
        :param screen: экран
        """
        screen.blit(self.image, self.rect)
        if self.is_closed:
            screen.blit(self.closed_door_image, self.doors_coords)

    def rotate(self, angle):
        """
        поворот двери
        :param angle: угол поворота
        """
        self.image = rotate_center(self.image, angle)
        self.closed_door_image = rotate_center(self.closed_door_image, angle)

    def close(self):
        """закрыть дверь"""
        self.is_closed = True

    def open(self):
        """открыть дверь"""
        self.is_closed = False

    def toggle(self):
        """переключить состояние двери"""
        self.is_closed = not self.is_closed

    @staticmethod
    def create_new_room(game, coords):
        """
        создать новую комнату
        :param game: объект игры
        :param coords: координаты текущей комнаты
        """
        if game.room.coords[0] - coords[0] > 0:
            game.player.move_to_position(820 - 80, 210)
            door_position = 'right'
        elif game.room.coords[0] - coords[0] < 0:
            game.player.move_to_position(80 + 100, 210)
            door_position = 'left'
        elif game.room.coords[1] - coords[1] > 0:
            game.player.move_to_position(450, 25 + 80)
            door_position = 'up'
        elif game.room.coords[1] - coords[1] < 0:
            game.player.move_to_position(450, 455 - 80)
            door_position = 'down'

        game.create_new_room(coords, door_position)

    def update(self, game):
        """
        обновление
        :param game: объект игры
        """
        if self.rect.colliderect(game.player.rect) and not self.is_closed:
            if self.coords == (450, 25):
                coords = (game.room.coords[0], game.room.coords[1] + 1)
            elif self.coords == (80, 210):
                coords = (game.room.coords[0] - 1, game.room.coords[1])
            elif self.coords == (450, 455):
                coords = (game.room.coords[0], game.room.coords[1] - 1)
            elif self.coords == (820, 210):
                coords = (game.room.coords[0] + 1, game.room.coords[1])
            if not self.room_created:
                self.create_new_room(game, coords)
                self.room_created = True
        if not game.room.enemy_group:
            self.open()
