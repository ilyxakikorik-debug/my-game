import pygame
import random
import os
import sys

pygame.init()

W, H = 600, 800
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

WHITE = (240,240,240)
RED = (240,70,70)
GREEN = (80,255,120)
YELLOW = (255,220,120)
BLACK = (0,0,0)

font = pygame.font.SysFont(None, 26)
big = pygame.font.SysFont(None, 64)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load(name, size=None):
    try:
        img = pygame.image.load(resource_path(os.path.join("assets", name))).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except:
        return None

# ---------------- PARTICLES ----------------
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.randint(-3, 3)
        self.vy = random.randint(-3, 3)
        self.life = 20

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 3)

# ---------------- PLAYER ----------------
class Player:
    def __init__(self):
        self.x = W // 2
        self.y = H - 160
        self.left = False
        self.right = False
        self.speed = 6

        self.damage = 1
        self.fire_rate = 10.0
        self.guns = 1

        self.img = load("player.png", (200, 200))
        self.w = 200
        self.h = 200

    def update(self):
        if self.left: self.x -= self.speed
        if self.right: self.x += self.speed
        self.x = max(self.w//2, min(W - self.w//2, self.x))

    def rect(self):
        return pygame.Rect(
            self.x - self.w//4,
            self.y - self.h//4,
            self.w//2,
            self.h//2
        )

    def draw(self):
        if self.img:
            screen.blit(self.img, (self.x - self.w//2, self.y - self.h//2))
        else:
            pygame.draw.circle(screen, GREEN, (self.x, self.y), 20)

# ---------------- ENEMY ----------------
class Enemy:
    def __init__(self, hp, boss=False):
        self.x = random.randint(50, W - 50)
        self.y = -50
        self.hp = hp
        self.boss = boss

        size = (70,70) if boss else (50,50)
        self.img = load("enemy.png", size)

    def update(self):
        self.y += 1 if self.boss else 1.5

    def draw(self):
        if self.img:
            screen.blit(self.img, (self.x - self.img.get_width()//2, self.y - self.img.get_height()//2))
        else:
            pygame.draw.circle(screen, RED, (self.x, self.y), 20 if self.boss else 15)

        screen.blit(font.render(str(self.hp), True, WHITE), (self.x - 15, self.y - 40))

# ---------------- BONUS ----------------
class Bonus:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.img = load(f"bonus_{kind}.png", (40, 40))

    def update(self):
        self.y += 2.2

    def rect(self):
        return pygame.Rect(self.x - 20, self.y - 20, 40, 40)

    def draw(self):
        if self.img:
            screen.blit(self.img, (self.x - 20, self.y - 20))
        else:
            pygame.draw.circle(screen, GREEN, (self.x, self.y), 10)

        screen.blit(font.render(self.kind.upper(), True, WHITE), (self.x - 20, self.y - 35))

# ---------------- BULLET ----------------
class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dead = False
        self.img = load("poop.png", (20, 20))

    def update(self):
        self.y -= 18
        if self.y < -20:
            self.dead = True

    def rect(self):
        return pygame.Rect(self.x - 5, self.y - 5, 10, 10)

    def draw(self):
        if self.img:
            screen.blit(self.img, (self.x - 10, self.y - 10))
        else:
            pygame.draw.circle(screen, YELLOW, (self.x, self.y), 5)

# ---------------- DOOR ----------------
class Door:
    def __init__(self):
        self.w = 190
        self.h = 160
        self.x = W // 2

        self.top_y = 260 - 80
        self.y = self.top_y + self.h // 2

        self.hp = 10000
        self.img = load("litter_box.png", (self.w, self.h))

        self.dirt_img = load("dirt.png", (40, 40))
        self.dirt_positions = []

    def add_dirt(self):
        for _ in range(3):
            dx = random.randint(-self.w//2, self.w//2)
            dy = random.randint(-self.h//2, self.h//2)
            self.dirt_positions.append((dx, dy))

    def rect(self):
        return pygame.Rect(self.x - self.w//2, self.y - self.h//2, self.w, self.h)

    def draw(self):
        x = self.x - self.w//2
        y = self.y - self.h//2

        if self.img:
            screen.blit(self.img, (x, y))

        for dx, dy in self.dirt_positions:
            screen.blit(self.dirt_img, (self.x + dx, self.y + dy))

        screen.blit(font.render(str(self.hp), True, WHITE), (self.x - 25, y - 25))

# ---------------- GAME ----------------
class Game:
    def __init__(self):
        self.player = Player()
        self.door = Door()

        self.enemies = []
        self.bullets = []
        self.bonuses = []
        self.particles = []

        self.state = "menu"

        self.spawn_timer = 0
        self.shoot_timer = 0.0
        self.bonus_timer = 0
        self.timer = 0
        self.boss_timer = 0

        self.enemy_hp = 5
        self.door_damage = 0

        self.gun_bonus_count = 0
        self.max_gun_bonus = 3

        self.floor = load("floor.png", (W, H))

    def reset(self):
        self.__init__()

    def shoot(self):
        for i in range(self.player.guns):
            offset = (i - self.player.guns//2) * 20
            bullet_x = self.player.x + offset
            bullet_y = self.player.y - self.player.h//2 + 20
            self.bullets.append(Bullet(bullet_x, bullet_y))

    def update(self):
        if self.state != "play":
            return

        self.timer += 1
        self.spawn_timer += 1
        self.shoot_timer += 1
        self.bonus_timer += 1
        self.boss_timer += 1

        if self.shoot_timer >= self.player.fire_rate:
            self.shoot_timer = 0
            self.shoot()

        if self.spawn_timer >= 60:
            self.spawn_timer = 0
            self.enemies.append(Enemy(self.enemy_hp))

        if self.timer % 1800 == 0:
            self.enemy_hp += 10

        if self.boss_timer >= 3600:
            self.boss_timer = 0
            boss_hp = 500 + (self.timer // 3600) * 500
            self.enemies.append(Enemy(boss_hp, boss=True))

        if self.bonus_timer >= 240:
            self.bonus_timer = 0
            kind = random.choice(["dmg", "fire", "gun"])

            if kind == "gun" and self.gun_bonus_count >= self.max_gun_bonus:
                kind = random.choice(["dmg", "fire"])

            self.bonuses.append(Bonus(random.randint(80, W-80), random.randint(120, 400), kind))

        self.player.update()

        for e in self.enemies:
            e.update()

        for b in self.bullets:
            b.update()

        for b in self.bonuses:
            b.update()

        for b in self.bullets:
            for e in self.enemies:
                if b.rect().colliderect(pygame.Rect(e.x-20,e.y-20,40,40)):
                    e.hp -= self.player.damage
                    self.particles.append(Particle(e.x, e.y))
                    b.dead = True

            if b.rect().colliderect(self.door.rect()):
                self.door.hp -= self.player.damage
                self.door_damage += self.player.damage

                if self.door_damage >= 1000:
                    self.door_damage -= 1000
                    self.door.add_dirt()

                b.dead = True

        self.bullets = [b for b in self.bullets if not b.dead]
        self.enemies = [e for e in self.enemies if e.hp > 0]

        new = []
        for b in self.bonuses:
            if b.rect().colliderect(self.player.rect()):
                if b.kind == "dmg":
                    self.player.damage += 1
                elif b.kind == "fire":
                    self.player.fire_rate = max(3.0, self.player.fire_rate - 0.5)
                elif b.kind == "gun":
                    if self.gun_bonus_count < self.max_gun_bonus:
                        self.player.guns += 1
                        self.gun_bonus_count += 1
            else:
                new.append(b)

        self.bonuses = new

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        for e in self.enemies:
            if e.y > self.player.y:
                self.state = "gameover"

        if self.door.hp <= 0:
            self.state = "win"

    def draw(self):
        if self.floor:
            screen.blit(self.floor, (0,0))
        else:
            screen.fill((20,20,20))

        if self.state == "menu":
            screen.blit(big.render("START", True, WHITE), (200, 350))
            pygame.display.flip()
            return

        if self.state == "gameover":
            screen.fill(BLACK)
            screen.blit(big.render("GAME OVER", True, RED), (120, 320))
            screen.blit(font.render("Press R to Restart", True, WHITE), (200, 400))
            pygame.display.flip()
            return

        if self.state == "win":
            screen.fill(BLACK)
            screen.blit(big.render("YOU WIN", True, GREEN), (160, 320))
            screen.blit(font.render("Press R to Restart", True, WHITE), (200, 400))
            pygame.display.flip()
            return

        self.player.draw()
        self.door.draw()

        for e in self.enemies:
            e.draw()

        for b in self.bullets:
            b.draw()

        for b in self.bonuses:
            b.draw()

        for p in self.particles:
            p.draw()

        screen.blit(font.render(f"DMG: {self.player.damage}", True, WHITE), (10, 10))
        screen.blit(font.render(f"GUNS: {self.player.guns}", True, WHITE), (10, 35))
        screen.blit(font.render(f"TIME: {self.timer//60}", True, WHITE), (10, 60))

        pygame.display.flip()

    def run(self):
        while True:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

                if event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        self.state = "play"

                    if event.key == pygame.K_r:
                        if self.state in ["gameover", "win"]:
                            self.reset()

                    if event.key == pygame.K_LEFT:
                        self.player.left = True
                    if event.key == pygame.K_RIGHT:
                        self.player.right = True

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.player.left = False
                    if event.key == pygame.K_RIGHT:
                        self.player.right = False

            self.update()
            self.draw()

Game().run()
pygame.quit()