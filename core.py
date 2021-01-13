import pygame
import os


def load_image(directory, path, size=None):
    full_path = os.path.join(directory, path) if directory is not None else path

    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"Unable to find path to image: {full_path}")
    image = pygame.image.load(full_path)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


class PhysicalSprite(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.previously_collided = set()
        self.current_collided = set()

    def update(self, game):
        collision = False
        for physical_object in game.get_groups():
            if collided := pygame.sprite.spritecollideany(self, physical_object):
                # обработку столкновений необходимо делать только для объектов, у которых описана физика
                if not isinstance(collided, PhysicalSprite):
                    continue
                if collided is not self:
                    collision = True
                    self.current_collided.add(collided)
                    # noinspection PyTypeChecker
                    self.on_collision(collided, game)
        # при столкновении с препятствием обработка физики не происходит
        # (никто не мешает вам в таком случае сделать отдельный обработчик, описывающий столкновения)
        if not collision:
            self.calc(game)

        # для отдельной обработки первого столкновения находим такие объекты
        # первым столкновениям считаются все столкновения, которые не были совершены на предыдущей
        # итерации обновления
        if new_collided := self.current_collided - self.previously_collided:
            for collided in new_collided:
                self.on_first_collision(collided, game)

        # подменяем буферы, отвечающие за хранение столкнувшихся объектов
        self.previously_collided.clear()
        self.previously_collided.update(self.current_collided)
        self.current_collided.clear()

    def on_collision(self, collided_sprite, game):
        pass

    def calc(self, game):
        pass

    def on_first_collision(self, collided_sprite, game):
        pass


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

        self.speed = 0.7
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
        self.speed = speed * 0.1
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
            self.__counter += self.__counter + 1 * self.speed

            if self.__counter >= 1:
                self._index = (self._index + 1) % len(self.action_sprites[self.current_action])
                # если счётчик дошёл до отмечки, то выставляем следующее в списке изображение на отрисовку

                self.__counter = 0
            self.image = self.action_sprites[self.current_action][self._index]


class PlayerBodyParts(AnimatedSprite, PhysicalSprite):
    def __init__(self, images_paths, coords, parent, *groups):
        AnimatedSprite.__init__(self, images_paths, coords)
        PhysicalSprite.__init__(self, *groups)
        self.parent = parent

        self.right_sprites = self.action_sprites
        self.left_sprites = dict()

        for action, images in self.action_sprites.items():
            rotated_images = [pygame.transform.flip(i, True, False) for i in
                              self.action_sprites[action]]
            self.left_sprites[action] = rotated_images

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
            self.speed = speed * 0.1
            self._index = 0

    def update(self, game):
        # PhysicalSprite.update(self, game)
        AnimatedSprite.update(self, game)

    def calc(self, game):
        self.parent.calc(game)
