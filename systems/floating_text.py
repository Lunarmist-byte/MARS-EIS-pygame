"""MARS SURVIVAL — Floating Combat & Reward Text.

Renders animated rising reward indicators ("+25 kg O2", "+30% POWER", "CHALLENGE COMPLETE!")
with easing curves, text shadows, and color transitions.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
from typing import List, Tuple, Any
import pygame


class FloatingText:
    """A single floating text notification."""

    __slots__ = ("text", "x", "y", "vx", "vy", "color", "life", "max_life", "scale")

    def __init__(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (100, 255, 160),
        max_life: float = 1.4,
    ) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = -38.0  # Drift upward
        self.color = color
        self.life = 0.0
        self.max_life = max_life
        self.scale = 1.2


class FloatingTextSystem:
    """Manages world-space floating reward popups."""

    def __init__(self) -> None:
        self.texts: List[FloatingText] = []
        pygame.font.init()
        self.font = pygame.font.SysFont("Consolas", 15, bold=True)
        self.font_big = pygame.font.SysFont("Consolas", 18, bold=True)

    def spawn(
        self,
        text: str,
        world_x: float,
        world_y: float,
        color: Tuple[int, int, int] = (100, 255, 160),
        big: bool = False,
    ) -> None:
        """Spawn a new floating reward popup."""
        ft = FloatingText(text, world_x, world_y, color=color, max_life=1.5)
        if big:
            ft.scale = 1.4
            ft.vy = -45.0
        self.texts.append(ft)

    def update(self, dt: float) -> None:
        """Update positions and life timers."""
        alive: List[FloatingText] = []
        for t in self.texts:
            t.x += t.vx * dt
            t.y += t.vy * dt
            t.vy *= 0.95  # Slow down as it rises
            t.life += dt
            if t.life < t.max_life:
                alive.append(t)
        self.texts = alive

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        """Render floating text in camera space with shadows and fading alpha."""
        for t in self.texts:
            sp = camera.world_to_screen(t.x, t.y)
            if not (-100 <= sp.x <= surface.get_width() + 100 and -50 <= sp.y <= surface.get_height() + 50):
                continue

            fade_norm = max(0.0, 1.0 - (t.life / t.max_life) ** 2)
            alpha = int(255 * fade_norm)
            if alpha <= 5:
                continue

            font_to_use = self.font_big if t.scale > 1.3 else self.font
            # Render shadow
            shadow_surf = font_to_use.render(t.text, True, (0, 0, 0))
            shadow_surf.set_alpha(int(alpha * 0.75))
            surface.blit(shadow_surf, (int(sp.x + 2), int(sp.y + 2)))

            # Render text
            text_surf = font_to_use.render(t.text, True, t.color)
            text_surf.set_alpha(alpha)
            surface.blit(text_surf, (int(sp.x), int(sp.y)))
