import math
import pygame
from pygame.sprite import Sprite

from core import load_image, Text


class HealthBar(Sprite):
    def __init__(self, game):
        Sprite.__init__(self)
        self.game = game
        self.player_health = game.player.health
        self.health_surface = pygame.Surface((200, 50))
        self.health_surface.fill((40, 30, 30))
        self.health_surface.set_colorkey((30, 30, 30))
        self.rect = self.health_surface.get_rect()
        self.full_heart = load_image('assets/room/full_heart.png', (40, 40))
        self.half_heart = load_image('assets/room/half_heart.png', (40, 40))

    def render(self, screen):
        """
        рендер объекта
        :param screen: экран
        """
        screen.blit(self.health_surface, self.rect)

    def update(self, game):
        """
        обновление
        :param game: игра
        """
        self.player_health = game.player.health
        self.health_surface.fill((30, 30, 30))
        health = self.player_health
        for i in range(math.ceil(self.player_health / 2)):
            x = 40 * i
            rect = pygame.Rect(x, 0, 40, 40)
            if health >= 2:
                self.health_surface.blit(self.full_heart, rect)
            else:
                self.health_surface.blit(self.half_heart, rect)
            health -= 2

    def add_internal(self, arg):
        """
        не знаю что, но, без него появляется ошибка
        :param arg: какой то аргумент
        """
        pass


class RoomsCounterText(Text, Sprite):

    def update(self, game):
        self.set_text(f'Комнат пройдено: {len(game.rooms_seeds_dict.keys()) - 1}')
