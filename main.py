import math
import os
from collections import defaultdict
from itertools import combinations
from typing import List, Dict, Tuple
from random import randint
import pygame

from core import PhysicalSprite, PlayerBodyParts, SpriteGroup, AnimatedSprite, CutAnimatedSprite, \
    HeartsIncludedCreature, CantHurtObject, CanHurtObject


def load_image(path, size=None):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find path to image: {path}")
    image = pygame.image.load(path)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


def get_rect_from_mask(mask):
    outline = mask.outline()
    # width = max(outline, key=lambda x: x[0]) - min(outline, key=lambda x: x[0])
    # height = max(outline, key=lambda x: x[1]) - min(outline, key=lambda x: x[1])
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


class Game:
    def __init__(self, width: int = 959, height: int = 540, name: str = 'Esaac', fps: int = 60):
        pygame.init()
        pygame.display.set_caption(name)

        self.screen = pygame.display.set_mode((width, height))
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = fps

        self.player = Player((100, 50))
        self.rock_1 = Rock((400, 270))
        self.rock_2 = Rock((450, 250))
        self.blob_1 = EnemyBlob((200, 100))
        self.blob_2 = EnemyBlob((100, 200))
        self.blob_3 = EnemyBlob((300, 400))
        self.mosquito = EnemyMosquito((200, 200))

        self.wall = Walls()

        self.interface = SpriteGroup(HealthBar(self))
        self.objects = []
        self.physical_group = [self.rock_1, self.rock_2, self.blob_1, self.blob_2,
                               self.player,
                               self.wall, self.mosquito]
        self.groups = []
        self.ammos = SpriteGroup()

        self.background = load_image('assets/room/room-background.png')
        self._handlers = defaultdict(list)

        self.add_handler(pygame.KEYDOWN, self.player.key_press_handler)
        self.add_handler(pygame.KEYUP, self.player.stop_move)

        physical_group = SpriteGroup()
        for obj in self.physical_group:
            physical_group.add(obj)

        for obj in [physical_group, self.ammos, self.interface]:
            self.add_object(obj)

    def add_object(self, obj):
        """
        Добавляет объект для отрисовки на экран.

        Должен быть экземпляром класса или наследника класса RenderableObject
        :param obj: созданный объект для отрисовки
        """
        self.objects.append(obj)
        if isinstance(obj, SpriteGroup):
            self.groups.append(obj)

    def run(self):
        while self.running:
            self.screen.blit(self.background, (0, 0))
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
        for obj in self.objects:
            if isinstance(obj, SpriteGroup):
                for i in obj:
                    i.render(self.screen)
            else:
                obj.render(self.screen)

    def add_handler(self, event_type, handler):
        self._handlers[event_type].append(handler)

    def update(self):
        for obj in self.objects:
            obj.update(self)

    def get_groups(self):
        return self.groups


class SpriteObject(pygame.sprite.Sprite):
    """
    Класс для работы со спрайтом. Любой спрайт ассоциируются с некоторым изображением,
    поэтому для урпощения жизни были добавлены параметры для создания изображения вместе с спрайтом
    """

    def __init__(self, image_path: str, coords: Tuple[int, int], size: Tuple[int, int] = None,
                 *groups: pygame.sprite.AbstractGroup):
        super().__init__(*groups)
        self.image_path = image_path
        self.size = size
        self.coords = coords

        self.image = load_image(image_path, size)
        self.rect = pygame.Rect(coords[0], coords[1], *self.image.get_size())

    def update(self, game: 'Game'):
        self.rect = pygame.Rect(self.coords[0], self.coords[1], *self.image.get_size())


class Explosion(AnimatedSprite):
    def __init__(self, coords, size, animation_speed=1):
        explosion_animation = {'explosion':
                                   [f'assets/explosions/explosion-1/{file_name}' for file_name in
                                    os.listdir('assets/explosions/explosion-1')], 'wait': [
            f'assets/explosions/explosion-1/{os.listdir("assets/explosions/explosion-1")[0]}']}

        AnimatedSprite.__init__(self, explosion_animation, coords, size, 'wait', animation_speed,
                                (68, 36, 52))


class Tears(SpriteObject, PhysicalSprite, CanHurtObject):
    def __init__(self, coords, team, game, direction_x=None, direction_y=None, ammo_speed=5,
                 dx=None, dy=None):
        SpriteObject.__init__(self, 'assets/player/ammo/ammo-1.png', coords)
        self.coords = coords
        self.start_coords = coords
        if direction_x == 'left':
            self.speed_x = -ammo_speed
        elif direction_x == 'right':
            self.speed_x = ammo_speed
        else:
            self.speed_x = 0

        if direction_y == 'up':
            self.speed_y = -ammo_speed
        elif direction_y == 'down':
            self.speed_y = ammo_speed
        else:
            self.speed_y = 0
        if dx or dy:
            self.speed_y = dy * ammo_speed * -1
            self.speed_x = dx * ammo_speed * -1

        self.transparent_num = 255

        game.ammos.add(self)
        self.game = game
        self.explosion = Explosion(self.coords, 0.3)
        self.is_killed = False
        self.hit_box = self.rect
        self.team = team
        if team == 'player':
            self.team_list = [Player]
        elif team == 'enemy':
            self.team_list = [EnemyBlob]

        self.damage = 1

    def move(self):
        if (abs(self.start_coords[0] - self.coords[0]) > 400
            or abs(self.start_coords[1] - self.coords[1]) > 400):
            self.is_killed = True

        self.rect.move_ip(self.speed_x, self.speed_y)
        self.coords = self.rect.x, self.rect.y

    def update(self, game):
        PhysicalSprite.update(self, game)
        self.explosion.update(game)
        self.move()
        self.hit_box = self.rect

    def render(self, screen):
        screen.blit(self.image, self.rect)

        if self.is_killed:
            self.kill()
            screen.blit(self.explosion.image, (self.coords[0] -
                                               self.explosion.image.get_width(
                                               ) / 2 + 15, self.coords[
                                                   1] - self.explosion.image.get_height() / 2 + 10))

    def kill(self):
        self.explosion.start('explosion')
        if self.explosion.index == 4:
            self.image.set_alpha(0)
        elif self.explosion.index == 7:
            super().kill()

    def on_collision(self, collided_sprite, game):
        if not any([isinstance(collided_sprite, team) for team in self.team_list]) and not \
            isinstance(collided_sprite, Tears):
            self.speed_y = 0
            self.speed_x = 0
            self.is_killed = True


class HealthBar:
    def __init__(self, game):
        self.game = game
        self.player_health = game.player.health
        self.health_surface = pygame.Surface((200, 50))
        self.health_surface.fill((30, 30, 30))
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


class EnemyBlob(CutAnimatedSprite, PhysicalSprite, HeartsIncludedCreature, CantHurtObject):
    player_x: int
    player_y: int
    can_attack: bool

    def __init__(self, coords):
        CutAnimatedSprite.__init__(self,'assets/enemys/i-blob.png', 4, 3, *coords, size=1.7,
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
        self.health = 8
        self.is_killed = False
        self.team = 'enemy'
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = get_rect_from_mask(self.mask).move(self.coords)
        self.explosion = Explosion(self.coords, 0.7)
        self.is_invisible = False
        self.move_delay = 0
        self.__counter = 0
        self.wait_counter = 0
        self.is_wait = False

        HeartsIncludedCreature.__init__(self, 'enemy')

    def render(self, screen: pygame.Surface):
        if not self.is_invisible:
            screen.blit(self.image, self.render_rect)
        if self.is_hurt and not self.is_invisible:
            self.show_hurt(screen)
        if self.is_killed:
            screen.blit(self.explosion.image, (self.coords[0] - self.image.get_width() / 3,
                                               self.coords[1] - 30))

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

        if self.health <= 0:
            self.is_killed = True
            self.kill()
        else:
            PhysicalSprite.update(self, game)
        HeartsIncludedCreature.update(self, game)
        if self.move_delay >= 1:
            pass

    def frames_handler(self, game):
        if self.current_frame == 2:
            self.can_attack = True
        elif self.current_frame == 3:
            self.attack(game)
            pass
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
                                     team='enemy', game=game, dx=dx, dy=dy, ammo_speed=8))
        self.can_attack = False

    def on_collision(self, collided_sprite, game):
        if isinstance(collided_sprite, Tears):
            return
        PhysicalSprite.on_collision(self, collided_sprite, game)

    def absence_collision(self, game):
        self.collision_direction_x = None
        self.collision_direction_y = None

    def get_hurt(self, hearted_object):
        if isinstance(hearted_object, Tears) and hearted_object not in self.already_hurt_by and \
            hearted_object.team == 'player':
            HeartsIncludedCreature.get_hurt(self, hearted_object)

    def kill(self):
        self.explosion.start('explosion')
        if self.explosion.index == 4:
            self.is_invisible = True
        elif self.explosion.index == 7:
            super().kill()

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

        self.health = 6
        HeartsIncludedCreature.__init__(self, 'player')

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
        if isinstance(collided_sprite, Tears):
            return
        PhysicalSprite.on_collision(self, collided_sprite, game)

    def absence_collision(self, game):
        self.collision_direction_x, self.collision_direction_y = None, None

    def get_hurt(self, hearted_object):
        if isinstance(hearted_object, Tears) and hearted_object not in self.already_hurt_by and \
            hearted_object.team == 'enemy':
            HeartsIncludedCreature.get_hurt(self, hearted_object)


class EnemyMosquito(PhysicalSprite, CanHurtObject, HeartsIncludedCreature, CutAnimatedSprite):
    def __init__(self, coords):
        PhysicalSprite.__init__(self)
        CanHurtObject.__init__(self)

        CutAnimatedSprite.__init__(self, 'assets/enemys/mosquito.png', 2, 1, *coords, size=3,
                                   speed=0.01)
        self.coords = coords
        HeartsIncludedCreature.__init__(self, 'enemy')
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_rect = self.rect

    def render(self, screen):
        screen.blit(self.image, self.rect)
        if self.is_hurt:
            self.show_hurt(screen)

    def update(self, game):
        CutAnimatedSprite.update(self, game)
        HeartsIncludedCreature.update(self, game)
        if self.hurt_delay >= 1:
            self.is_hurt = False
        self.hurt_delay += self.hurt_delay / 3 + 0.01

    def on_collision(self, collided_sprite, game):
        if isinstance(collided_sprite, Tears) or isinstance(collided_sprite, Player):
            return
        PhysicalSprite.on_collision(self, collided_sprite, game)

    def get_hurt(self, hearted_object):
        if isinstance(hearted_object, Tears) and hearted_object not in self.already_hurt_by and \
            hearted_object.team == 'player':
            HeartsIncludedCreature.get_hurt(self, hearted_object)


class Rock(SpriteObject, PhysicalSprite, CantHurtObject):
    def __init__(self, coords, *groups):
        PhysicalSprite.__init__(self, *groups)
        SpriteObject.__init__(self, image_path='assets/room/room_rock.png',
                              coords=coords)
        CantHurtObject.__init__(self)
        self.coords = coords
        self.mask_rect = self.rect

    def update(self, game):
        SpriteObject.update(self, game)
        PhysicalSprite.update(self, game)

    def render(self, screen):
        screen.blit(self.image, self.rect)

    def on_collision(self, collided_sprite, game):
        pass


class Walls(PhysicalSprite, CantHurtObject):
    def __init__(self):
        PhysicalSprite.__init__(self)
        CantHurtObject.__init__(self)
        self.rect = pygame.Rect(0, 0, 1000, 85)
        self.mask_rect = self.rect

    def update(self, game):
        PhysicalSprite.update(self, game)

    def render(self, screen):
        # pygame.draw.rect(screen, (0, 100, 0), self.rect)
        pass

    def on_collision(self, collided_sprite, game):
        pass

    # def on_collision(self, collided_sprite, game):
    #     print(collided_sprite)


if __name__ == '__main__':
    game = Game
    game().run()
