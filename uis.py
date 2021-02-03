import math
import pygame
from core import load_image


class HealthBar:
    def __init__(self, game):
        self.game = game
        self.player_health = game.player.health
        self.health_surface = pygame.Surface((200, 50))
        self.health_surface.fill((40, 30, 30))
        self.health_surface.set_colorkey((30, 30, 30))
        self.rect = self.health_surface.get_rect()
        self.full_heart = load_image('assets/room/full_heart.png', (40, 40))
        self.half_heart = load_image('assets/room/half_heart.png', (40, 40))

    def render(self, screen):
        screen.blit(self.health_surface, self.rect)

    def update(self, game):
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
        pass
