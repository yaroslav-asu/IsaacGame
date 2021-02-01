import math
import os
from random import randint
from typing import Dict, List, Any

import pygame

from objects import Explosion, Tears, PlayerBodyParts
from core import CutAnimatedSprite, PhysicalSprite, CantHurtObject, HeartsIncludedCreature, \
    get_rect_from_mask, CanHurtObject


class EnemyBlob(CutAnimatedSprite, PhysicalSprite, HeartsIncludedCreature, CantHurtObject):
    player_x: int
    player_y: int
    can_attack: bool

    def __init__(self, coords):
        CutAnimatedSprite.__init__(self, 'assets/enemys/i-blob.png', 4, 3, *coords, size=1.7,
                                   speed=0.0008)
        PhysicalSprite.__init__(self)
        CantHurtObject.__init__(self)
        self.render_rect = pygame.Rect(*coords, *self.image.get_size())
        self.rect = pygame.Rect(*coords, int(30 * 1.7), int(21 * 1.7))
        self.coords = list(coords)
        self.speed = 20
        self.move_delay = 0
        self.can_move = False
        self.tears_list = []
        self.collision_direction_x = None
        self.collision_direction_y = None
        self.is_killed = False
        self.team = 'enemy'
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = get_rect_from_mask(self.mask).move(self.coords)
        self.explosion = Explosion(self, (500, 500), (self.image.get_width() / 3, 30), 0.7)
        self.is_invisible = False
        self.move_delay = 0
        self.__counter = 0
        self.wait_counter = 0
        self.is_wait = False

        HeartsIncludedCreature.__init__(self, 'enemy', health=8)

    def render(self, screen: pygame.Surface):
        if not self.is_invisible:
            screen.blit(self.image, self.render_rect)
        if self.is_hurt and not self.is_invisible:
            self.show_hurt(screen)
        if self.is_killed:
            self.explosion.render(screen)
            self.explosion.explode()

    def update(self, game):
        if self.wait_counter < 5:
            self.wait()
        else:
            CutAnimatedSprite.update(self, game)
            self.move(game)
        self.frames_handler(game)
        self.explosion.update(game)
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = get_rect_from_mask(self.mask).move(self.coords)
        if self.hurt_delay >= 1:
            self.is_hurt = False
        self.hurt_delay += self.hurt_delay / 3 + 0.01

        if not self.is_killed:
            PhysicalSprite.update(self, game)
        HeartsIncludedCreature.update(self, game)
        if self.move_delay >= 1:
            pass

    def frames_handler(self, game):
        if self.current_frame == 2:
            self.can_attack = True
        elif self.current_frame == 3:
            self.attack(game)
        elif self.current_frame == 10:
            self.can_move = True
        elif self.current_frame == 11:
            self.can_move = False
            self.wait_counter = 0

    @staticmethod
    def get_player_position(game):
        return game.player.coords

    def move(self, game):
        if self.move_delay > 1 and self.can_move:
            self.player_x, self.player_y = self.get_player_position(game)
            if self.player_y > self.coords[1] + randint(0, 80) and self.collision_direction_y \
                != \
                'down':
                self.coords[1] += self.speed
                for rect in [self.render_rect, self.rect]:
                    rect.move_ip(0, self.speed)
            elif self.player_y < self.coords[1] + randint(0, 80) and self.collision_direction_y != \
                'up':
                self.coords[1] -= self.speed
                for rect in [self.render_rect, self.rect]:
                    rect.move_ip(0, -self.speed)
            if self.player_x - 400 > self.coords[0] + randint(-80, 80) < self.player_x + 400 and \
                self.collision_direction_x != 'right':
                self.coords[0] += self.speed
                for rect in [self.render_rect, self.rect]:
                    rect.move_ip(self.speed, 0)
            elif self.collision_direction_x != 'left':
                self.coords[0] -= self.speed
                for rect in [self.render_rect, self.rect]:
                    rect.move_ip(-self.speed, 0)
            self.move_delay = 0
        self.move_delay += self.move_delay + 0.01

    def attack(self, game):
        if not self.can_attack:
            return
        dx = self.rect.x - game.player.mask_rect.x
        dy = self.rect.y - game.player.mask_rect.y

        dist = math.hypot(dx, dy)
        dx = dx / dist
        dy = dy / dist

        self.tears_list.append(Tears((int(self.coords[0] + self.rect.width / 2 + 20),
                                      int(self.coords[1] + self.rect.height / 2 + 45)),
                                     team='enemy', game=game, dx=dx, dy=dy))
        self.can_attack = False

    def on_collision(self, collided_sprite, game):
        if isinstance(collided_sprite, Tears) or collided_sprite in game.creatures:
            return
        PhysicalSprite.on_collision(self, collided_sprite, game)

    def get_hurt(self, hurt_object):
        if isinstance(hurt_object, Tears) and hurt_object not in self.already_hurt_by and \
            hurt_object.team == 'player':
            HeartsIncludedCreature.get_hurt(self, hurt_object)
        if self.health <= 0:
            self.is_killed = True

    # def kill(self):
    #     self.explosion.start('explosion')
    #     if self.explosion.index == 4:
    #         self.is_invisible = True
    #     elif self.explosion.index == 7:
    #         super().kill()

    def wait(self):
        self.is_wait = True
        self.__counter += self.__counter / 3 + self.animation_speed
        if self.__counter >= 1:
            self.wait_counter += 1
            if self.current_frame == 0:
                self.current_frame = 1
            else:
                self.current_frame = 0
            self.image = self.frames[self.current_frame]
            self.__counter = 0


class Player(PhysicalSprite, CantHurtObject, HeartsIncludedCreature):
    mask: pygame.mask.Mask

    def __init__(self, coords: tuple, *groups):
        PhysicalSprite.__init__(self, *groups)
        CantHurtObject.__init__(self)

        head_sprite_map: Dict[str, List[str]] = dict()
        for action_folder in ('idle', 'walking-x', 'walking-down', 'walking-up', 'attack-x',
                              'attack-up', 'attack-down'):
            head_sprite_map[action_folder] = [f'assets/player/head/{action_folder}/{i}' for i in
                                              os.listdir(f'assets/player/head/{action_folder}')]

        body_sprite_map: Dict[str, List[str]] = dict()
        for action_folder in ('idle', 'walking-x', 'walking-down', 'walking-up'):
            body_sprite_map[action_folder] = [f'assets/player/body/{action_folder}/{i}' for i in
                                              os.listdir(f'assets/player/body/{action_folder}')]

        self.head_sprite = PlayerBodyParts(head_sprite_map, (coords[0], coords[1]), self,
                                           animation_speed=0.001)

        self.body_sprite = PlayerBodyParts(body_sprite_map, (coords[0] + 10, coords[1] + 39),
                                           self, animation_speed=0.001)

        self.coords = list(coords)
        self.direction_x = None
        self.direction_y = None

        self.speed = 4

        self.sliding_time = 0
        self.action_sprites = dict()

        self.ammos_list = list()

        self.attack_speed: float = 0.05
        self.attack_delay = 0

        self.image = pygame.Surface((self.head_sprite.image.get_width(),
                                     self.head_sprite.image.get_height() +
                                     self.body_sprite.image.get_height()))
        self.image.fill((0, 255, 0))
        self.image.set_colorkey((0, 255, 0))
        self.image.blit(self.body_sprite.image, (10, 39))
        self.image.blit(self.head_sprite.image, (0, 0))

        self.render_rect = pygame.Rect(*coords, self.body_sprite.image.get_width(),
                                       self.body_sprite.image.get_height() +
                                       self.head_sprite.image.get_height())

        self.rect = pygame.Rect((coords[0], coords[1],
                                 self.head_sprite.image.get_width(),
                                 self.head_sprite.image.get_height() +
                                 self.body_sprite.image.get_height()))
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = get_rect_from_mask(self.mask)
        self.collision_direction_x = None
        self.collision_direction_y = None

        self.is_attack = False

        HeartsIncludedCreature.__init__(self, 'player', health=10)

    def key_press_handler(self, event):
        if event.key == pygame.K_a:
            self.direction_x = 'left'

        elif event.key == pygame.K_d:
            self.direction_x = 'right'

        if event.key == pygame.K_w:
            self.direction_y = 'up'
        elif event.key == pygame.K_s:
            self.direction_y = 'down'

    def stop_move(self, event=None):
        keys = pygame.key.get_pressed()
        for i in [zip((pygame.K_a, pygame.K_d), ('left', 'right')),
                  zip((pygame.K_w, pygame.K_s), ('up', 'down'))]:
            i = list(i)
            if keys[i[0][0]] and not keys[i[1][0]]:
                self.direction_x = i[0][1]
            elif keys[i[1][0]] and not keys[i[0][0]]:
                self.direction_x = i[1][1]
        if not len(list(filter(lambda x: x, [keys[pygame.K_a], keys[pygame.K_d]]))):
            self.direction_x = None
        if not len(list(filter(lambda x: x, [keys[pygame.K_s], keys[pygame.K_w]]))):
            self.direction_y = None

        if not len(list(filter(lambda x: x, [keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_s],
                                             keys[pygame.K_w]]))):
            if not self.is_attack:
                self.head_sprite.start('idle')
            self.body_sprite.start('idle')

    def render(self, screen):
        screen.blit(self.image, self.rect)
        if self.is_hurt:
            self.show_hurt(screen)

    def update(self, game):
        if self.is_attack:
            update_body_parts = (self.body_sprite,)
        else:
            update_body_parts = (self.head_sprite, self.body_sprite)

        if self.hurt_delay >= 1:
            self.is_hurt = False
        self.hurt_delay += self.hurt_delay / 3 + 0.01

        if self.direction_x == 'left':
            for element in update_body_parts:
                element.action_sprites = element.left_sprites
                element.start(action='walking-x')
        elif self.direction_x == 'right':
            for element in update_body_parts:
                element.action_sprites = element.right_sprites
                element.start(action='walking-x')
        if self.direction_y == 'up':
            for element in update_body_parts:
                element.start(action='walking-up')
        elif self.direction_y == 'down':
            for element in update_body_parts:
                element.start(action='walking-down')

        if self.direction_x is None and self.direction_y is None:
            self.stop_move()

        self.move(self.direction_x, self.direction_y, self.collision_direction_x,
                  self.collision_direction_y)
        self.body_sprite.update(game)
        self.head_sprite.update(game)

        self.image = pygame.Surface((self.head_sprite.image.get_width(),
                                     self.head_sprite.image.get_height() +
                                     self.body_sprite.image.get_height()))
        self.image.fill((0, 255, 0))
        self.image.set_colorkey((0, 255, 0))

        self.image.blit(self.body_sprite.image, (10, 39))
        self.image.blit(self.head_sprite.image, (0, 0))

        self.attack(game)
        self.mask_rect = get_rect_from_mask(self.mask).move(self.coords)
        PhysicalSprite.update(self, game)
        HeartsIncludedCreature.update(self, game)

    def move(self, direction_x, direction_y, collision_direction_x, collision_direction_y):
        if direction_x == 'left' and not collision_direction_x == 'left':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect,
                         self.body_sprite.rect, self.mask_rect]:
                rect.move_ip(-self.speed, 0)
            self.coords[0] -= self.speed
        elif direction_x == 'right' and not collision_direction_x == 'right':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect,
                         self.body_sprite.rect, self.mask_rect]:
                rect.move_ip(self.speed, 0)
            self.coords[0] += self.speed
        if direction_y == 'up' and not collision_direction_y == 'up':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect,
                         self.body_sprite.rect, self.mask_rect]:
                rect.move_ip(0, -self.speed)
            self.coords[1] -= self.speed
        elif direction_y == 'down' and not collision_direction_y == 'down':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect,
                         self.body_sprite.rect, self.mask_rect]:
                rect.move_ip(0, self.speed)
            self.coords[1] += self.speed

    def attack(self, game):
        team = 'player'
        self.attack_delay += self.attack_delay / 2.5 + self.attack_speed * 0.0001
        if self.attack_delay < 1:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.head_sprite.action_sprites = self.head_sprite.left_sprites
            self.head_sprite.start(action='attack-x')
            self.ammos_list.append(Tears(self.head_sprite.rect.center, team, game, 'left',
                                         self.direction_y))
            self.attack_delay = 0
            self.is_attack = True
        elif keys[pygame.K_RIGHT]:
            self.head_sprite.action_sprites = self.head_sprite.right_sprites
            self.head_sprite.start(action='attack-x')
            self.ammos_list.append(Tears(self.head_sprite.rect.center, team, game, 'right',
                                         self.direction_y))
            self.attack_delay = 0
            self.is_attack = True
        elif keys[pygame.K_UP]:
            self.head_sprite.start(action='attack-up')
            self.ammos_list.append(Tears(self.head_sprite.rect.center, team, game, self.direction_x,
                                         'up'))
            self.attack_delay = 0
            self.is_attack = True
        elif keys[pygame.K_DOWN]:
            self.head_sprite.start(action='attack-down')
            self.ammos_list.append(Tears(self.head_sprite.rect.center, team, game, self.direction_x,
                                         'down'))
            self.attack_delay = 0
            self.is_attack = True
        else:
            self.is_attack = False

    def on_collision(self, collided_sprite, game):
        if isinstance(collided_sprite, Tears) or collided_sprite in game.creatures:
            return
        PhysicalSprite.on_collision(self, collided_sprite, game)

    def absence_collision(self, game):
        self.collision_direction_x, self.collision_direction_y = None, None

    def get_hurt(self, hurt_object):
        if (isinstance(hurt_object, Tears) or isinstance(hurt_object, EnemyMosquito)) and \
            hurt_object not in self.already_hurt_by and hurt_object.team == 'enemy':
            HeartsIncludedCreature.get_hurt(self, hurt_object)


class EnemyMosquito(PhysicalSprite, CanHurtObject, HeartsIncludedCreature, CutAnimatedSprite):
    player_position: Any

    def __init__(self, coords, size):
        PhysicalSprite.__init__(self)
        CanHurtObject.__init__(self)
        self.is_invisible = False
        if size == 'big':
            self.speed = 1
            self.damage = 2
            self.attack_speed = 0.00001
            creature_size = 3
            health = 3
            explosion_size = 0.7
        CutAnimatedSprite.__init__(self, 'assets/enemys/mosquito.png', 2, 1, *coords,
                                   size=creature_size,
                                   speed=0.01)
        self.coords = list(coords)
        HeartsIncludedCreature.__init__(self, 'enemy', health)
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = get_rect_from_mask(self.mask)

        self.attack_delay = 0
        self.one_punch_object = False
        self.explosion = Explosion(self, self.coords, (35, 40),
                                   explosion_size)
        self.is_killed = False
        self.collision_direction_y = None
        self.collision_direction_x = None

    def render(self, screen):
        if not self.is_invisible:
            screen.blit(self.image, self.rect)
            olist = self.mask.outline()
            pygame.draw.polygon(self.show_hurt_surface, (0, 255, 0), olist, 0)
            screen.blit(self.show_hurt_surface, (self.rect.x, self.rect.y))
        if self.is_hurt:
            self.show_hurt(screen)
        if self.is_killed:
            self.explosion.render(screen)

    def move(self):
        dx = self.rect.x - self.player_position[0] + randint(-80, 80)
        dy = self.rect.y - self.player_position[1] + randint(-80, 80)

        dist = math.hypot(dx, dy)
        dx /= dist + 1
        dy /= dist + 1
        if dx > 0 and self.collision_direction_x == 'left':
            dx = 0
        elif dx < 0 and self.collision_direction_x == 'right':
            dx = 0

        if dy > 0 and self.collision_direction_y == 'up':
            dy = 0
        elif dy < 0 and self.collision_direction_y == 'down':
            dy = 0
        self.coords[0] += dx * self.speed * -1
        self.coords[1] += dy * self.speed * -1
        for rect in [self.rect]:
            rect.x = self.coords[0]
            rect.y = self.coords[1]

    def update(self, game):
        self.player_position = game.player.coords
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = get_rect_from_mask(self.mask).move(self.coords)
        CutAnimatedSprite.update(self, game)

        if self.hurt_delay >= 1:
            self.is_hurt = False
        self.hurt_delay += self.hurt_delay / 3 + 0.01
        self.move()
        HeartsIncludedCreature.update(self, game)
        self.attack_delay += self.attack_delay / 5 + self.attack_speed
        if self.attack_delay >= 1 and pygame.sprite.collide_mask(self, game.player):
            self.attack(game.player)
        if self.is_killed:
            self.explosion.update(game)
            self.explosion.explode()
        PhysicalSprite.update(self, game)

    def on_collision(self, collided_sprite, game):
        print(collided_sprite)
        if isinstance(collided_sprite, Tears) or collided_sprite in game.creatures:
            return
        PhysicalSprite.on_collision(self, collided_sprite, game)

    def get_hurt(self, hurt_object):
        if isinstance(hurt_object, Tears) and hurt_object not in self.already_hurt_by and \
            hurt_object.team == 'player':
            HeartsIncludedCreature.get_hurt(self, hurt_object)
        if self.health <= 0:
            self.is_killed = True

    def attack(self, player):
        self.attack_delay = 0
        player.get_hurt(self)

    # def kill(self):
    #     super().kill()
