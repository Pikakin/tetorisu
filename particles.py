import pygame
import random
import math
from config import scale_factor


class Particle:
    def __init__(self, x, y, color, size=3, speed=2, life=1.0, effect_type="default"):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.speed = speed
        self.life = life
        self.max_life = life
        self.effect_type = effect_type

        # エフェクトタイプに応じた初期化
        if effect_type == "explosion":
            self.angle = random.uniform(0, 2 * math.pi)
            self.dx = math.cos(self.angle) * self.speed
            self.dy = math.sin(self.angle) * self.speed
        elif effect_type == "rain":
            self.angle = random.uniform(
                math.pi / 2 - 0.2, math.pi / 2 + 0.2
            )  # ほぼ真下
            self.dx = math.cos(self.angle) * self.speed * 0.5
            self.dy = math.sin(self.angle) * self.speed * 2
        elif effect_type == "spiral":
            self.angle = random.uniform(0, 2 * math.pi)
            self.radius = random.uniform(2, 10)
            self.angular_speed = random.uniform(2, 5) * (
                1 if random.random() > 0.5 else -1
            )
            self.dx = math.cos(self.angle) * self.speed * 0.2
            self.dy = math.sin(self.angle) * self.speed * 0.2
        else:  # default
            self.angle = random.uniform(0, 2 * math.pi)
            self.dx = math.cos(self.angle) * self.speed
            self.dy = math.sin(self.angle) * self.speed

    def update(self, dt):
        if self.effect_type == "spiral":
            # スパイラルエフェクトの場合は角度を更新
            self.angle += self.angular_speed * dt
            self.x += self.dx * dt * 60 + math.cos(self.angle) * self.radius * dt * 2
            self.y += self.dy * dt * 60 + math.sin(self.angle) * self.radius * dt * 2
        else:
            self.x += self.dx * dt * 60
            self.y += self.dy * dt * 60

            # 重力効果（雨エフェクト）
            if self.effect_type == "rain":
                self.dy += 9.8 * dt  # 重力加速度

        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (
            (*self.color[:3], alpha) if len(self.color) > 3 else (*self.color, alpha)
        )

        if self.effect_type == "rain":
            # 雨滴は縦長の楕円形
            size_x = max(1, int(self.size * 0.5 * (self.life / self.max_life)))
            size_y = max(1, int(self.size * 2 * (self.life / self.max_life)))
            pygame.draw.ellipse(
                surface,
                color,
                (int(self.x - size_x), int(self.y - size_y), size_x * 2, size_y * 2),
            )
        else:
            # 通常のパーティクルは円形
            size = max(1, int(self.size * (self.life / self.max_life)))
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.effect_type = "default"  # デフォルトのエフェクトタイプ

    def set_effect_type(self, effect_type):
        self.effect_type = effect_type

    def create_explosion(self, x, y, color, count=10):
        for _ in range(count):
            size = random.uniform(2, 5)
            speed = random.uniform(1, 3)
            life = random.uniform(0.5, 1.5)
            self.particles.append(
                Particle(x, y, color, size, speed, life, self.effect_type)
            )

    def create_line_clear_effect(self, x, y, color, count=15, width=None):
        # ライン消去エフェクト
        for _ in range(count):
            size = random.uniform(3, 7)
            speed = random.uniform(2, 5)
            life = random.uniform(0.7, 1.8)
            # ライン全体にパーティクルを分散
            particle_x = x + random.uniform(0, width if width else 300 * scale_factor)
            self.particles.append(
                Particle(particle_x, y, color, size, speed, life, self.effect_type)
            )

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)


class FloatingText:
    def __init__(self, x, y, text, color, size=28, life=1.5):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = life
        self.max_life = life
        # グローバルフォントを使用して文字化けを防止
        self.font = pygame.font.SysFont("yugothicuibold", size)
        self.size = size
        self.dy = -1  # 上に移動

    def update(self, dt):
        self.y += self.dy * dt * 60
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        # フォントが存在しない場合は再作成
        if not hasattr(self, "font") or self.font is None:
            self.font = pygame.font.SysFont("yugothicuibold", self.size)
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (self.x - text_surf.get_width() // 2, self.y))
