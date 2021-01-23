import os
from collections import defaultdict
from itertools import combinations
from typing import List, Dict, Tuple
from random import randint
import pygame

from core import PhysicalSprite, PlayerBodyParts, SpriteGroup, AnimatedSprite, CutAnimatedSprite


def load_image(path, size=None):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find path to image: {path}")
    image = pygame.image.load(path)
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

        self.player = Player((0, 0))
        self.rock = Rock((400, 270))
        self.blob = EnemyBlob((200, 200))
        self.wall = Walls()

        self.objects = []
        self.physical_group = [self.rock, self.wall, self.blob, self.player]
        self.groups = []
        self.ammos = SpriteGroup()

        self.background = load_image('assets/room/room-background.png')
        self._handlers = defaultdict(list)

        self.add_handler(pygame.KEYDOWN, self.player.key_press_handler)
        self.add_handler(pygame.KEYUP, self.player.stop_move)

        physical_group = SpriteGroup()
        for obj in self.physical_group:
            physical_group.add(obj)

        for obj in [physical_group, self.ammos]:
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


class Tears(SpriteObject, PhysicalSprite):
    def __init__(self, coords, direction_x, direction_y, team, game, ammo_speed=5):
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
        self.transparent_num = 255

        game.ammos.add(self)
        self.game = game
        explosion_animation = {'explosion':
                                   [f'assets/explosions/explosion-1/{file_name}' for file_name in
                                    os.listdir('assets/explosions/explosion-1')], 'wait': [
            f'assets/explosions/explosion-1/{os.listdir("assets/explosions/explosion-1")[0]}']}

        self.explosion = AnimatedSprite(explosion_animation, self.coords, 0.3,
                                        current_action='wait')
        self.explosion_surface = pygame.Surface(self.explosion.image.get_size())
        self.explosion_surface.set_colorkey((68, 36, 52))
        self.is_killed = False
        if team == 'player':
            self.team = [Player]
        elif team == 'enemy':
            self.team = [EnemyBlob]

    def move(self):
        if (abs(self.start_coords[0] - self.coords[0]) > 400
            or abs(self.start_coords[1] - self.coords[1]) > 400):
            self.is_killed = True

        self.rect.move_ip(self.speed_x, self.speed_y)
        self.coords = self.coords[0] + self.speed_x, self.coords[1] + self.speed_y

    def update(self, game):
        PhysicalSprite.update(self, game)
        self.explosion.update(game)
        self.move()

    def render(self, screen):
        screen.blit(self.image, self.rect)
        if self.is_killed:
            self.kill()
            screen.blit(self.explosion_surface, (self.coords[0] - self.explosion.image.get_width(
            ) / 2 + 15, self.coords[1] - self.explosion.image.get_height() / 2 + 10))

    def kill(self):
        self.explosion.start('explosion')
        self.explosion_surface.blit(self.explosion.image, (0, 0))

        if self.explosion.index == 4:
            self.image.set_alpha(0)
        elif self.explosion.index == 7:
            super().kill()

    def on_collision(self, collided_sprite, game):
        if not any([isinstance(collided_sprite, team) for team in self.team]) and not \
            isinstance(collided_sprite, Tears):
            self.speed_y = 0
            self.speed_x = 0
            self.is_killed = True


class EnemyBlob(CutAnimatedSprite, PhysicalSprite):
    player_x: int
    player_y: int

    def __init__(self, coords):
        CutAnimatedSprite.__init__(self, 4, 3, *coords, size=1.7, speed=0.008)
        PhysicalSprite.__init__(self)
        self.render_rect = pygame.Rect(*coords, *self.image.get_size())
        self.rect = pygame.Rect(*coords, int(30 * 1.7), int(21 * 1.7)).move(10, 25)
        self.coords = list(coords)
        self.speed = 20
        self.move_delay = 0
        self.is_move = False
        self.tears_list = []

    def render(self, screen: pygame.Surface):
        a = pygame.Surface((250, 250))
        a.fill((0, 255, 0))
        a.blit(self.image, (-20, -30))
        a.set_colorkey((0, 255, 0))
        # pygame.draw.rect(screen, (0, 100, 0), self.rect)
        screen.blit(a, self.render_rect)

    def update(self, game):
        self.move(game)
        self.change_rect(game)
        game.ammos.add()
        CutAnimatedSprite.update(self, game)
        PhysicalSprite.update(self, game)

    def change_rect(self, game):
        if self.current_frame == 0 or self.current_frame == 8:
            self.rect = pygame.Rect(*self.coords, int(30 * 1.7), int(21 * 1.7)).move(10, 25)
        elif self.current_frame == 1 or self.current_frame == 7:
            self.rect = pygame.Rect(*self.coords, int(30 * 1.7), int(24 * 1.7)).move(10, 22)
        elif self.current_frame == 2:
            self.rect = pygame.Rect(*self.coords, int(28 * 1.7), int(29 * 1.7)).move(10, 15)
            self.can_attack = True
        elif self.current_frame == 3:
            self.attack(game)
            self.rect = pygame.Rect(*self.coords, int(28 * 1.7), int(29 * 1.7)).move(20, 15)
        elif self.current_frame == 4:
            self.rect = pygame.Rect(*self.coords, int(37 * 1.7), int(20 * 1.7)).move(16, 28)
        elif self.current_frame == 5:
            self.rect = pygame.Rect(*self.coords, int(37 * 1.7), int(20 * 1.7)).move(6, 28)
        elif self.current_frame == 6 or self.current_frame == 9:
            self.rect = pygame.Rect(*self.coords, int(41 * 1.7), int(11 * 1.7)).move(3, 44)
        elif self.current_frame == 10:
            self.is_move = True
            self.rect = pygame.Rect(*self.coords, int(30 * 1.7), int(29 * 1.7)).move(13, 6)
        elif self.current_frame == 11:
            self.rect = pygame.Rect(*self.coords, int(30 * 1.7), int(29 * 1.7)).move(13, 8)
            self.is_move = False

    @staticmethod
    def get_player_position(game):
        return game.player.coords

    def move(self, game):
        if self.move_delay > 1 and self.is_move:
            self.player_x, self.player_y = self.get_player_position(game)
            if self.player_y > self.coords[1] + randint(0, 80):
                self.coords[1] += self.speed
                self.render_rect.move_ip(0, self.speed)
            elif self.player_y < self.coords[1] + randint(0, 80):
                self.coords[1] -= self.speed
                self.render_rect.move_ip(0, -self.speed)
            if self.player_x + 400 > self.coords[0] + randint(-80, 80):
                self.coords[0] += self.speed
                self.render_rect.move_ip(self.speed, 0)
            elif self.player_x + 400 < self.coords[0] + randint(-80, 80):
                self.coords[0] -= self.speed
                self.render_rect.move_ip(-self.speed, 0)
            self.move_delay = 0
        self.move_delay += self.move_delay + 0.01

    def attack(self, game):
        if not self.can_attack:
            return
        tears_directions = []
        [tears_directions.extend(list(combinations([j, i], 2))) for i in ('up', 'down') for j
         in ('left', 'right')]
        tears_directions = list(set(tears_directions))
        tears_directions.extend([(None, i) for i in ('up', 'down')] +
                                [(i, None) for i in ('right', 'left')])
        for direction in tears_directions:
            self.tears_list.append(Tears((int(self.coords[0] + self.rect.width / 2),
                                         int(self.coords[1] + self.rect.height / 2)),
                                         *direction,  'enemy',  game))
        self.can_attack = False


class Player(PhysicalSprite):
    def __init__(self, coords: tuple, *groups):
        PhysicalSprite.__init__(self, *groups)

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

        self.image = pygame.Surface((90, 90))
        self.image.fill((0, 255, 0))
        self.image.set_colorkey((0, 255, 0))
        self.image.blit(self.body_sprite.image, (10, 39 + self.head_sprite.image.get_height()))
        self.image.blit(self.head_sprite.image, (0, self.head_sprite.image.get_height()))

        self.render_rect = pygame.Rect(*coords, self.body_sprite.image.get_width(),
                                       self.body_sprite.image.get_height() +
                                       self.head_sprite.image.get_height())

        self.rect = pygame.Rect(coords[0] + 12, coords[1] + self.head_sprite.image.get_height() - 3,
                                self.body_sprite.image.get_width() - 4,
                                self.body_sprite.image.get_height() - 8)

        self.collision_direction = None

        self.is_attack = False

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
        screen.blit(self.image, self.render_rect)

    def update(self, game):
        if self.is_attack:
            update_body_parts = (self.body_sprite,)
        else:
            update_body_parts = (self.head_sprite, self.body_sprite)

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

        self.move(self.direction_x, self.direction_y, self.collision_direction)
        self.body_sprite.update(game)
        self.head_sprite.update(game)

        self.image = pygame.Surface((300, 300))
        self.image.fill((0, 255, 0))
        self.image.set_colorkey((0, 255, 0))

        self.image.blit(self.body_sprite.image, (10, 39))
        self.image.blit(self.head_sprite.image, (0, 0))

        self.attack(game)
        PhysicalSprite.update(self, game)

    def move(self, direction_x, direction_y, collision_direction):
        if direction_x == 'left' and not collision_direction == 'left':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect,
                         self.body_sprite.rect]:
                rect.move_ip(-self.speed, 0)
            self.coords[0] -= self.speed
        elif direction_x == 'right' and not collision_direction == 'right':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect, self.body_sprite.rect]:
                rect.move_ip(self.speed, 0)
            self.coords[0] += self.speed
        if direction_y == 'up' and not collision_direction == 'up':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect, self.body_sprite.rect]:
                rect.move_ip(0, -self.speed)
            self.coords[1] -= self.speed
        elif direction_y == 'down' and not collision_direction == 'down':
            for rect in [self.rect, self.render_rect, self.head_sprite.rect, self.body_sprite.rect]:
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
            self.ammos_list.append(Tears(self.head_sprite.rect.center, 'left',
                                         self.direction_y, team, game))
            self.attack_delay = 0
            self.is_attack = True
        elif keys[pygame.K_RIGHT]:
            self.head_sprite.action_sprites = self.head_sprite.right_sprites
            self.head_sprite.start(action='attack-x')
            self.ammos_list.append(Tears(self.head_sprite.rect.center, 'right',
                                         self.direction_y, team, game))
            self.attack_delay = 0
            self.is_attack = True
        elif keys[pygame.K_UP]:
            self.head_sprite.start(action='attack-up')
            self.ammos_list.append(Tears(self.head_sprite.rect.center, self.direction_x,
                                         'up', team, game))
            self.attack_delay = 0
            self.is_attack = True
        elif keys[pygame.K_DOWN]:
            self.head_sprite.start(action='attack-down')
            self.ammos_list.append(Tears(self.head_sprite.rect.center, self.direction_x,
                                         'down', team, game))
            self.attack_delay = 0
            self.is_attack = True
        else:
            self.is_attack = False

    def on_collision(self, collided_sprite, game):
        if isinstance(collided_sprite, Tears):
            return
        if collided_sprite.rect.left < self.rect.right < collided_sprite.rect.right and \
            collided_sprite.rect.top < self.rect.bottom and self.rect.top < \
            collided_sprite.rect.bottom:
            self.collision_direction = 'right'
        elif collided_sprite.rect.right > self.rect.left > collided_sprite.rect.left and \
            collided_sprite.rect.top < self.rect.bottom and self.rect.top < \
            collided_sprite.rect.bottom:
            self.collision_direction = 'left'
        if collided_sprite.rect.bottom > self.rect.top > collided_sprite.rect.top and \
            collided_sprite.rect.left < \
            self.rect.centerx < collided_sprite.rect.right:
            self.collision_direction = 'up'
        elif collided_sprite.rect.top < self.rect.bottom and collided_sprite.rect.left < \
            self.rect.centerx < collided_sprite.rect.right:
            self.collision_direction = 'down'

    def calc(self, game):
        self.collision_direction = None


class Rock(SpriteObject, PhysicalSprite):
    def __init__(self, coords, *groups):
        PhysicalSprite.__init__(self, *groups)
        SpriteObject.__init__(self, image_path='assets/room/room_rock.png',
                              coords=coords)
        self.coords = coords

    def update(self, game):
        SpriteObject.update(self, game)
        PhysicalSprite.update(self, game)

    def render(self, screen):
        screen.blit(self.image, self.rect)

class Walls(PhysicalSprite):
    def __init__(self):
        PhysicalSprite.__init__(self)
        self.rect = pygame.Rect(0, 0, 1000, 85)

    def update(self, game):
        PhysicalSprite.update(self, game)

    def render(self, screen):
        # pygame.draw.rect(screen, (0, 100, 0), self.rect)
        pass

    # def on_collision(self, collided_sprite, game):
    #     print(collided_sprite)



if __name__ == '__main__':
    game = Game
    game().run()
