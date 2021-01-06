import os
from pprint import pprint
from collections import defaultdict
from typing import List, Dict, Tuple

import pygame


def load_image(directory, path, size=None):
    full_path = os.path.join(directory, path) if directory is not None else path

    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"Unable to find path to image: {full_path}")
    image = pygame.image.load(full_path)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


class Game:
    def __init__(self, width: int = 959, height: int = 540, name: str = 'Esaac', fps: int = 40):
        pygame.init()
        pygame.display.set_caption(name)

        self.screen = pygame.display.set_mode((width, height))
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = fps

        self.player = Player((479, 270))
        self.objects = [self.player]
        self.groups = []

        self.background = load_image('assets/room', 'room-background.png')
        self._handlers = defaultdict(list)

        self.add_handler(pygame.KEYUP, self.player.stop_move)

    def run(self):
        while self.running:
            self.screen.blit(self.background, (0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                for handler in self._handlers.get(event.type, []):
                    handler(event)
            self.player.move()
            self.player.head_sprite.update(self)
            self.player.body_sprite.update(self)

            time_delta = self.clock.tick(self.fps)
            self.draw(time_delta)

            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

    def draw(self, time_delta):
        for obj in self.objects:
            obj.render(self.screen, time_delta)

    def add_handler(self, event_type, handler):
        self._handlers[event_type].append(handler)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, images_paths, coords, image_dir='assets',
                 size=None, current_action='idle', *groups):
        super().__init__(*groups)

        self.action_sprites = dict()
        # подгружаем изображения из спрайтов
        # for images_dict_num in range(len(images_paths)):
        #     for action, paths in images_paths[images_dict_num].items():
        #         if action not in self.all_action_sprites.keys():
        #             self.all_action_sprites[action] = []
        #         images = []
        #         for sprite_path in paths:
        #             images.append(load_image(image_dir, sprite_path, size))
        #         self.all_action_sprites[action].append(images[:])
        self.action_sprites = dict()
        for action, paths in images_paths.items():
            if action not in self.action_sprites.keys():
                self.action_sprites[action] = []
            images = []
            for sprite_path in paths:
                images.append(load_image(image_dir, sprite_path, size))
            self.action_sprites[action] = images[:]

        self.__speed = 1.0
        self._started = False
        self.__counter = 0
        self._index = 0
        self.current_action = current_action
        self.coords = coords

        # self.action_sprites = dict()
        self.image = self.action_sprites[self.current_action][self._index]
        self.rect = pygame.Rect(self.coords[0], self.coords[1], *self.image.get_size())

    def start(self, action='idle', speed: float = 1):
        """
        Начинает воспроизводить анимацию
        :param action: действие, по которому будет начат анимация
        :param speed: скорость воспроизведения анимации
        :return:
        """
        self.change_current_action(action)
        self._started = True
        self.__speed = speed * 0.1
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

    def update(self, game: 'Game') -> None:
        """
        Простенький вариант для работы анимации
        """
        if self.is_started():
            # увеличиваем счётчик на каждой итерации на некотое небольшое значение
            self.__counter += self.__counter + 1 * self.__speed

            if self.__counter >= 1:
                self._index = (self._index + 1) % len(self.action_sprites[self.current_action])
                # если счётчик дошёл до отмечки, то выставляем следующее в списке изображение на отрисовку

                self.__counter = 0
            self.image = self.action_sprites[self.current_action][self._index]


class PlayerBodyParts(AnimatedSprite):
    def __init__(self, images_paths, coords, parent):
        super().__init__(images_paths, coords)
        self.parent = parent

    def start(self, action='idle', speed: float = 1):
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
            self.__speed = speed * 0.1
            self._index = 0


class Player(AnimatedSprite):
    def __init__(self, coords: tuple):
        head_sprite_map: Dict[str, List[str]] = dict()
        for action_folder in ('idle', 'walking-x', 'walking-down', 'walking-up', 'attack-x',
                              'attack-up', 'attack-down'):
            head_sprite_map[action_folder] = [f'player/head/{action_folder}/{i}' for i in
                                              os.listdir(f'assets/player/head/{action_folder}')]

        body_sprite_map: Dict[str, List[str]] = dict()
        for action_folder in ('idle', 'walking-x', 'walking-down', 'walking-up'):
            body_sprite_map[action_folder] = [f'player/body/{action_folder}/{i}' for i in
                                              os.listdir(f'assets/player/body/{action_folder}')]

        sprite_map = body_sprite_map
        body_parts_coords = coords
        super().__init__(sprite_map, body_parts_coords)

        self.head_sprite = PlayerBodyParts(head_sprite_map, (coords[0] - 10, coords[1] - 39), self)
        self.body_sprite = PlayerBodyParts(body_sprite_map, coords, self)

        self.walking_right_sprites = self.action_sprites
        self.walking_left_sprites = dict()

        for action, images in self.action_sprites.items():
            rotated_images = [pygame.transform.flip(i, True, False) for i in
                              self.action_sprites[action]]
            self.walking_left_sprites[action] = rotated_images

        self.x, self.y = coords
        self.direction_x = None
        self.direction_y = None

        self.speed = 4

        self.sliding_time = 0
        self.action_sprites = dict()

    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.direction_x = 'left'
            self.head_sprite.rect.move_ip(-self.speed, 0)
            self.body_sprite.rect.move_ip(-self.speed, 0)
            # self.action_sprites = self.walking_left_sprites
            self.head_sprite.start(action='walking-x')
            self.body_sprite.start(action='walking-x')
        elif keys[pygame.K_d]:
            self.direction_x = 'right'
            self.head_sprite.rect.move_ip(self.speed, 0)
            self.body_sprite.rect.move_ip(self.speed, 0)
            # self.action_sprites = self.walking_right_sprites
            self.head_sprite.start(action='walking-x')
            self.body_sprite.start(action='walking-x')
        else:
            self.direction_x = None

        if keys[pygame.K_w]:
            self.direction_y = 'up'
            self.head_sprite.start(action='walking-up')
            self.body_sprite.start(action='walking-up')
            self.head_sprite.rect.move_ip(0, -self.speed)
            self.body_sprite.rect.move_ip(0, -self.speed)
        elif keys[pygame.K_s]:
            self.direction_y = 'down'
            self.head_sprite.start(action='walking-down')
            self.body_sprite.start(action='walking-down')
            self.head_sprite.rect.move_ip(0, self.speed)
            self.body_sprite.rect.move_ip(0, self.speed)
        else:
            self.direction_y = None

    def stop_move(self, event):
        keys = pygame.key.get_pressed()
        if not len(list(filter(lambda x: x, [keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_s],
                                             keys[pygame.K_w]]))):
            self.head_sprite.start('idle')
            self.body_sprite.start('idle')

    def render(self, screen, time_delta: int):
        screen.blit(self.body_sprite.image, self.body_sprite.rect)
        screen.blit(self.head_sprite.image, self.head_sprite.rect)

    # def setup_action_sprites(self):
    #     self.action_sprites = dict()
    #
    #     for key in self.all_action_sprites.keys():
    #         image = self.all_action_sprites[key][0][0]
    #         for layer_num in range(1, len(self.all_action_sprites[key][0]) - 1):
    #             image.blit(self.all_action_sprites[key][layer_num], coords[layer_num])
    #
    #         self.action_sprites[key] = image
    #     pprint(self.action_sprites[self.current_action])
    #     self.image = self.action_sprites[self.current_action][self._index]
    #     self.rect = pygame.Rect(self.coords[0], self.coords[1], *self.image.get_size())


if __name__ == '__main__':
    game = Game
    game().run()
