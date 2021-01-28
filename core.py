from typing import Any

import pygame
import os


def load_image(path, size=None):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find path to image: {path}")
    image = pygame.image.load(path)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


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


class HeartsIncludedCreature:
    image: pygame.image
    mask: pygame.mask
    coords: Any

    def __init__(self, team):
        self.team = team
        self.already_hurt_by = set()
        self.show_hurt_surface = pygame.Surface(self.image.get_size())
        self.show_hurt_surface.fill((0, 255, 0))
        self.show_hurt_surface.set_colorkey((0, 255, 0))

    def update(self, game):
        hurt = True
        self.show_hurt_surface.fill((0, 255, 0))
        for physical_object in game.get_groups():
            for collided in physical_object:
                try:
                    if pygame.sprite.collide_mask(self, collided) and collided is not self and \
                        collided.can_hurt:

                        hurt = True
                        self.get_hurt(collided, game.screen)
                    else:
                        hurt = False
                except AttributeError:
                    hurt = False

                if not hurt:
                    self.absence_hurt()

    def get_hurt(self, hearted_object, screen):
        pass

    def absence_hurt(self):
        pass

    def show_hurt(self, screen, color=(255, 0, 0), alpha=60):
        olist = self.mask.outline()
        self.show_hurt_surface.set_alpha(alpha)
        pygame.draw.polygon(self.show_hurt_surface, color, olist, 0)
        screen.blit(self.show_hurt_surface, self.coords)


class PhysicalSprite(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
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

                    # self.current_collided.add(collided)
                    self.on_collision(collided, game)
        if not collision:
            self.absence_collision(game)

        # if new_collided := self.current_collided - self.previously_collided:
        #     for collided in new_collided:
        #         self.on_first_collision(collided, game)

        # self.previously_collided.clear()
        # self.previously_collided.update(self.current_collided)
        # self.current_collided.clear()

    def on_collision(self, collided_sprite, game):
        pass

    def absence_collision(self, game):
        pass

    def on_first_collision(self, collided_sprite, game):
        pass


class CutAnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, columns, rows, x, y, size: float = 1, speed: float = 1):
        super().__init__()
        self.frames = []
        size_tuple = tuple(int(i * size) for i in load_image('assets/enemys/i-blob.png').get_size())
        sheet = load_image('assets/enemys/i-blob.png', size_tuple)
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
            # увеличиваем счётчик на каждой итерации на некотое небольшое значение
            self.__counter += self.__counter + 1 * self.animation_speed

            if self.__counter >= 1:
                self._index = (self._index + 1) % len(self.action_sprites[self.current_action])
                # если счётчик дошёл до отмечки, то выставляем следующее в списке изображение на отрисовку

                self.__counter = 0
            self.image = self.action_sprites[self.current_action][self._index]
            if self.color_key:
                self.image.set_colorkey(self.color_key)

    @property
    def index(self):
        return self._index


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
        # PhysicalSprite.update(self, game)
        AnimatedSprite.update(self, game)

    def calc(self, game):
        self.parent.calc(game)
