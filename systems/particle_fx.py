from __future__ import annotations
import math
import random
from typing import List, Tuple, Any
import pygame


class FXParticle:
    """Represents a single transient visual FX particle."""

    __slots__ = ("x", "y", "vx", "vy", "size", "color", "alpha", "life", "max_life", "decay_rate")

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        size: float,
        color: Tuple[int, int, int],
        alpha: int = 220,
        max_life: float = 0.5,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.alpha = float(alpha)
        self.life = 0.0
        self.max_life = max_life
        self.decay_rate = alpha / max_life


class ParticleFXSystem:
    """Manages world-space game feel particle effects and rendering."""

    def __init__(self) -> None:
        self.particles: List[FXParticle] = []
        self._fx_surface = pygame.Surface((32, 32), pygame.SRCALPHA)

    def spawn_footstep_puff(self, x: float, y: float, move_dir: pygame.Vector2) -> None:
        """Spawn subtle regolith dust puffs at astronaut boots."""
        # Opposite direction of movement with slight spread
        opp_x = -move_dir.x * 20.0 if move_dir.length_squared() > 0 else 0.0
        opp_y = -move_dir.y * 20.0 if move_dir.length_squared() > 0 else 0.0

        for _ in range(random.randint(2, 4)):
            vx = opp_x + random.uniform(-12.0, 12.0)
            vy = opp_y + random.uniform(-8.0, 8.0)
            size = random.uniform(2.0, 4.0)
            color = random.choice([
                (210, 125, 75),   # Terracotta
                (185, 95, 45),    # Basalt Ochre
                (225, 145, 85),   # Golden Regolith
            ])
            self.particles.append(
                FXParticle(
                    x=x + random.uniform(-6, 6),
                    y=y + random.uniform(-2, 2),
                    vx=vx,
                    vy=vy,
                    size=size,
                    color=color,
                    alpha=random.randint(110, 180),
                    max_life=random.uniform(0.35, 0.65),
                )
            )

    def spawn_landing_ring(self, x: float, y: float) -> None:
        """Spawn circular burst of regolith dust when landing from low-g hop."""
        for angle_deg in range(0, 360, 30):
            rad = math.radians(angle_deg)
            speed = random.uniform(35.0, 65.0)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed * 0.5  # Perspective squish
            size = random.uniform(2.5, 4.5)
            self.particles.append(
                FXParticle(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    size=size,
                    color=(215, 130, 80),
                    alpha=200,
                    max_life=0.45,
                )
            )

    def spawn_thruster_plume(self, x: float, y: float, move_dir: pygame.Vector2) -> None:
        """Spawn cold gas thruster vapor jets during sprint/hop."""
        for _ in range(2):
            vx = -move_dir.x * 45.0 + random.uniform(-10.0, 10.0)
            vy = -move_dir.y * 45.0 + random.uniform(-10.0, 10.0)
            self.particles.append(
                FXParticle(
                    x=x + random.uniform(-3, 3),
                    y=y + random.uniform(-3, 3),
                    vx=vx,
                    vy=vy,
                    size=random.uniform(2.0, 3.5),
                    color=random.choice([(140, 220, 255), (180, 240, 255), (255, 255, 255)]),
                    alpha=220,
                    max_life=0.25,
                )
            )

    def spawn_celebration_burst(self, x: float, y: float, particle_type: str = "spark") -> None:
        """Spawn confetti, gas venting, or electric sparks upon challenge victory."""
        colors = {
            "spark": [(255, 220, 90), (255, 180, 40), (255, 255, 200)],
            "oxygen": [(100, 220, 255), (180, 245, 255), (255, 255, 255)],
            "water": [(60, 160, 255), (120, 200, 255), (180, 230, 255)],
            "bio": [(100, 240, 120), (160, 255, 160), (220, 255, 200)],
        }.get(particle_type, [(255, 215, 0), (255, 140, 0), (100, 255, 200)])

        for _ in range(28):
            angle = random.uniform(0.0, 6.28)
            speed = random.uniform(40.0, 140.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(
                FXParticle(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    size=random.uniform(2.5, 5.0),
                    color=random.choice(colors),
                    alpha=240,
                    max_life=random.uniform(0.6, 1.1),
                )
            )

    def update(self, dt: float) -> None:
        """Advance particle positions and life timers."""
        alive: List[FXParticle] = []
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            # Air friction damping
            p.vx *= 0.92
            p.vy *= 0.92
            p.life += dt
            p.alpha = max(0.0, p.alpha - p.decay_rate * dt)
            if p.life < p.max_life and p.alpha > 5:
                alive.append(p)
        self.particles = alive

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        """Render active world-space particles in camera coordinates."""
        for p in self.particles:
            sp = camera.world_to_screen(p.x, p.y)
            # Viewport culling
            if not (-20 <= sp.x <= surface.get_width() + 20 and -20 <= sp.y <= surface.get_height() + 20):
                continue

            r = int(p.size)
            if r <= 0:
                continue

            # Draw transparent particle efficiently using cached scratch surface
            surf_size = r * 2 + 2
            if surf_size <= self._fx_surface.get_width():
                scratch = self._fx_surface
                scratch.fill((0, 0, 0, 0))
            else:
                scratch = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            pygame.draw.circle(scratch, (*p.color, int(p.alpha)), (r + 1, r + 1), r)
            surface.blit(scratch, (int(sp.x - r - 1), int(sp.y - r - 1)), area=pygame.Rect(0, 0, surf_size, surf_size))
