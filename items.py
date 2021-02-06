import pygame

from core import SpriteObject
from creatures import Player


class GrabAbleObject(SpriteObject):
    """
    объект который можно подобрать
    """
    def __init__(self, image_path, coords, size=None, disappearance_speed=0.01):
        SpriteObject.__init__(self, image_path, coords, size)
        self.mask_rect = self.rect
        self.disappearance_timer = 7
        self.disappearance_speed = disappearance_speed
        self.blink_delay = 0.08
        self.blink_speed = 0.01
        self.invisible_timer = 4
        self.is_visible = True

    def update(self, game):
        """
        обновление
        :param game: игра
        """
        SpriteObject.update(self, game)
        if pygame.sprite.collide_mask(self, game.player):
            self.grab(game)
        self.disappearance_timer -= self.disappearance_speed
        if 0 < self.disappearance_timer <= 2:
            self.blink()
        elif self.disappearance_timer < 0:
            self.disappear()

    def blink(self):
        """
        мигание объекта
        """
        self.blink_delay -= self.blink_speed
        if self.blink_delay <= 0:
            self.is_visible = not self.is_visible
            self.blink_delay = 0.08

    def render(self, screen):
        """
        рендер объекта
        :param screen: экран
        """
        if self.is_visible:
            super().render(screen)

    def grab(self, game):
        """
        подобрать объект
        :param game: игра
        """
        pass

    def disappear(self):
        """
        исчезновение
        """
        self.kill()

    def on_collision(self, collided_sprite, game):
        """
        что происходит при столкновении
        :param collided_sprite: с чем столкнулись
        :param game: игра
        """
        if isinstance(collided_sprite, Player):
            self.grab(game)


class HalfHeart(GrabAbleObject):
    def __init__(self, coords):
        size = 1.5
        image_path = 'assets/items/Half_Red_Heart.png'
        GrabAbleObject.__init__(self, image_path, coords, size)

    def grab(self, game):
        """
        подобрать объект
        :param game: игра
        """
        game.player.heal(1)
        self.disappear()


class FullHeart(GrabAbleObject):
    def __init__(self, coords):
        image_path = 'assets/items/Red_Heart.png'
        size = 1.5
        super().__init__(image_path, coords, size)

    def grab(self, game):
        """
        подобрать объект
        :param game: игра
        """
        game.player.heal(2)
        self.disappear()
