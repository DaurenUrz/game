import pygame
import random
import math
from pygame.locals import *

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 1000
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

clock = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

pygame.display.set_caption('Space sweep')

score = 0
lives = 3
bullets_left = 10
base_enemy_spawn_interval = 1500
enemy_spawn_interval = base_enemy_spawn_interval
life_spawn_interval = 15000
start_time = pygame.time.get_ticks()

# Load sound files
pygame.mixer.init()
shoot_sound = pygame.mixer.Sound("sound/shoot.wav")
hit_sound = pygame.mixer.Sound("sound/hit.wav")
pickup_sound = pygame.mixer.Sound("sound/pickup.wav")
life_sound = pygame.mixer.Sound("sound/life.wav")
collision_sound = pygame.mixer.Sound("sound/collision.wav")
pygame.mixer.music.load("sound/bg.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.1)

def load_animation_images(directory, frames_count, new_width=None, new_height=None):
    images = []
    for i in range(1, frames_count + 1):
        image_path = f'{directory}/{i}.png'
        image = pygame.image.load(image_path).convert_alpha()
        if new_width and new_height:
            image = pygame.transform.scale(image, (new_width, new_height))
        images.append(image)
    return images

class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, images):
        super().__init__()
        self.images = images
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    def update_animation(self):
        self.index = (self.index + 1) % len(self.images)
        self.image = self.images[self.index]

class Player(AnimatedSprite):
    def __init__(self):
        images = load_animation_images('player', 4, 80, 80)
        super().__init__(images)
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.speed = 6
        self.angle = 0

    def update(self, pressed_keys):
        if pressed_keys[K_w]:
            self.rect.move_ip(0, -self.speed)
        if pressed_keys[K_s]:
            self.rect.move_ip(0, self.speed)
        if pressed_keys[K_a]:
            self.rect.move_ip(-self.speed, 0)
        if pressed_keys[K_d]:
            self.rect.move_ip(self.speed, 0)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        angle = math.atan2(mouse_y - self.rect.centery, mouse_x - self.rect.centerx)
        self.angle = math.degrees(angle) - 90

class Enemy(AnimatedSprite):
    def __init__(self, target, spawn_x, spawn_y):
        images = load_animation_images('enemy', 4, 50, 50)
        super().__init__(images)
        self.rect.center = (spawn_x, spawn_y)
        self.speed = 2
        self.target = target

    def update(self):
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance != 0:
            self.rect.x += dx / distance * self.speed
            self.rect.y += dy / distance * self.speed

        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(self.rect):
            self.kill()

class Bullet(AnimatedSprite):
    def __init__(self, x, y, angle):
        images = load_animation_images('bullet', 2, 20, 20)
        super().__init__(images)
        self.rect.center = (x, y)
        self.speed = 10
        vx = math.cos(math.radians(angle))
        vy = math.sin(math.radians(angle))
        self.velocity = (vx * self.speed, vy * self.speed)

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Ammo(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        images = load_animation_images('ammo', 1, 50, 40)
        self.index = 0
        self.images = images
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(center=(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)))
        self.animation_speed = 300

class Life(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        images = load_animation_images('life', 1, 20, 20)
        self.index = 0
        self.images = images
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(center=(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)))
        self.animation_speed = 300

def check_collisions(player, enemies, bullets, ammo_group, life_group):
    global score, lives, bullets_left
    for bullet in bullets:
        hit = pygame.sprite.spritecollide(bullet, enemies, dokill=True)
        if hit:
            score += 1
            bullet.kill()
            hit_sound.play()
    hit_enemies = pygame.sprite.spritecollide(player, enemies, dokill=False)
    if hit_enemies:
        lives -= 1
        collision_sound.play()
        for enemy in hit_enemies:
            enemy.kill()
        if lives <= 0:
            return True
    hit_ammo = pygame.sprite.spritecollide(player, ammo_group, dokill=True)
    if hit_ammo:
        bullets_left += 5
        pickup_sound.play()
    hit_life = pygame.sprite.spritecollide(player, life_group, dokill=True)
    if hit_life:
        lives += 1
        life_sound.play()
    return False

def show_game_over():
    screen.fill(BLACK)
    font = pygame.font.Font(None, 36)
    text = font.render('Game Over. Press any key to restart.', True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True
            if event.type == pygame.KEYDOWN:
                return False

def game_loop():
    global score, lives, bullets_left, enemy_spawn_interval, start_time

    score = 0
    lives = 3
    bullets_left = 30
    player = Player()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    ammo_group = pygame.sprite.Group()
    life_group = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)

    ADDENEMY = pygame.USEREVENT + 1
    pygame.time.set_timer(ADDENEMY, enemy_spawn_interval)

    ADDAMMO = pygame.USEREVENT + 2
    pygame.time.set_timer(ADDAMMO, 5000)

    ADDLIFE = pygame.USEREVENT + 3
    pygame.time.set_timer(ADDLIFE, life_spawn_interval)

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) / 1000

        # Update enemy spawn interval every frame
        enemy_spawn_interval = max(1000, base_enemy_spawn_interval - 200 * (elapsed_time // 5))

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == ADDENEMY:
                side = random.choice(['left', 'right', 'top', 'bottom'])
                if side == 'left':
                    spawn_x = 0
                    spawn_y = random.randint(0, SCREEN_HEIGHT)
                elif side == 'right':
                    spawn_x = SCREEN_WIDTH
                    spawn_y = random.randint(0, SCREEN_HEIGHT)
                elif side == 'top':
                    spawn_x = random.randint(0, SCREEN_WIDTH)
                    spawn_y = 0
                else:
                    spawn_x = random.randint(0, SCREEN_WIDTH)
                    spawn_y = SCREEN_HEIGHT
                new_enemy = Enemy(player, spawn_x, spawn_y)
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)
            elif event.type == KEYDOWN and event.key == K_SPACE and bullets_left > 0:
                new_bullet = Bullet(player.rect.centerx, player.rect.centery, player.angle + 90)
                bullets.add(new_bullet)
                all_sprites.add(new_bullet)
                bullets_left -= 1
                shoot_sound.play()
            elif event.type == ADDAMMO:
                new_ammo = Ammo()
                ammo_group.add(new_ammo)
                all_sprites.add(new_ammo)
            elif event.type == ADDLIFE:
                new_life = Life()
                life_group.add(new_life)
                all_sprites.add(new_life)

        pressed_keys = pygame.key.get_pressed()
        player.update(pressed_keys)
        enemies.update()
        bullets.update()
        ammo_group.update()
        life_group.update()
        screen.fill(BLACK)
        for entity in all_sprites:
            if isinstance(entity, (Player, Enemy)):
                entity.update_animation()
            screen.blit(entity.image, entity.rect)

        if check_collisions(player, enemies, bullets, ammo_group, life_group):
            if lives <= 0:
                if show_game_over():
                    return
                else:
                    game_loop()

        score_text = pygame.font.Font(None, 36).render(f'Score: {score}', True, WHITE)
        lives_text = pygame.font.Font(None, 36).render(f'Lives: {lives}', True, WHITE)
        bullets_text = pygame.font.Font(None, 36).render(f'Bullets: {bullets_left}', True, WHITE)
        time_text = pygame.font.Font(None, 36).render(f'Time: {elapsed_time:.2f}', True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 50))
        screen.blit(bullets_text, (10, 90))
        screen.blit(time_text, (10, 130))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

game_loop()
