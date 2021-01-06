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
    def __init__(self, width: int = 959, height: int = 540, name: str = 'Esaac', fps: int = 60):
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

        # self.add_handler(pygame.KEYDOWN, self.player.key_press_handler)
        self.add_handler(pygame.KEYUP, self.player.stop_move)

    def run(self):
        while self.running:
            self.screen.blit(self.background, (0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                for handler in self._handlers.get(event.type, []):
                    handler(event)
            self.player.key_press_handler()
            self.player.head_sprite.update(self)
            self.player.body_sprite.update(self)

            time_delta = self.clock.tick(self.fps)
            self.draw()

            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

    def draw(self):
        for obj in self.objects:
            obj.render(self.screen)

    def add_handler(self, event_type, handler):
        self._handlers[event_type].append(handler)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, images_paths, coords, image_dir='assets',
                 size=None, current_action='idle', *groups):
        super().__init__(*groups)

        self.action_sprites = dict()
        for action, paths in images_paths.items():
            if action not in self.action_sprites.keys():
                self.action_sprites[action] = []
            images = []
            for sprite_path in paths:
                images.append(load_image(image_dir, sprite_path, size))
            self.action_sprites[action] = images[:]

        self.__speed = 0.7
        self._started = False
        self.__counter = 0
        self._index = 0
        self.current_action = current_action
        self.coords = coords

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

        self.walking_right_sprites = self.action_sprites
        self.walking_left_sprites = dict()

        for action, images in self.action_sprites.items():
            rotated_images = [pygame.transform.flip(i, True, False) for i in
                              self.action_sprites[action]]
            self.walking_left_sprites[action] = rotated_images

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

        self.x, self.y = coords
        self.direction_x = None
        self.direction_y = None

        self.speed = 6

        self.sliding_time = 0
        self.action_sprites = dict()

    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.direction_x = 'left'
            for element in (self.head_sprite, self.body_sprite):
                element.rect.move_ip(-self.speed, 0)
                element.action_sprites = self.body_sprite.walking_left_sprites
                element.start(action='walking-x')
        elif keys[pygame.K_d]:
            self.direction_x = 'right'
            for element in (self.head_sprite, self.body_sprite):
                element.rect.move_ip(self.speed, 0)
                element.action_sprites = self.body_sprite.walking_right_sprites
                element.start(action='walking-x')
        else:
            self.direction_x = None

        if keys[pygame.K_w]:
            self.direction_y = 'up'
            for element in (self.head_sprite, self.body_sprite):
                element.start(action='walking-up')
                element.rect.move_ip(0, -self.speed)
        elif keys[pygame.K_s]:
            self.direction_y = 'down'
            for element in (self.head_sprite, self.body_sprite):
                element.start(action='walking-down')
                element.rect.move_ip(0, self.speed)
        else:
            self.direction_y = None

    def stop_move(self, event):
        keys = pygame.key.get_pressed()
        if not len(list(filter(lambda x: x, [keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_s],
                                             keys[pygame.K_w]]))):
            self.head_sprite.start('idle')
            self.body_sprite.start('idle')

    def render(self, screen):
        screen.blit(self.body_sprite.image, self.body_sprite.rect)
        screen.blit(self.head_sprite.image, self.head_sprite.rect)

    def key_press_handler(self):
        keys = pygame.key.get_pressed()
        if list(filter(lambda x: keys[x], [pygame.K_a, pygame.K_d, pygame.K_s, pygame.K_w])):
            self.move()
        elif list(filter(lambda x: keys[x], [pygame.KEYUP, pygame.KEYDOWN, pygame.K_LEFT,
                                             pygame.K_RIGHT])):
            self.attack()

    def attack(self):
        pass

if __name__ == '__main__':
    game = Game
game().run()
