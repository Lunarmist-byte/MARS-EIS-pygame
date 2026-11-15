"""MARS SURVIVAL — UI Drawing Components.

Reusable Pygame primitives for HUD rendering, sci-fi glass panels,
progress bars, status badges, and typography.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import Tuple, Optional
import pygame
from config import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
)


class UIComponents:
    """Helper class providing stylized HUD primitives."""

    def __init__(self) -> None:
        # Load system fonts with fallback to Pygame default
        pygame.font.init()
        font_name = "consolas,couriernew,arial,sans-serif"
        self.font_large = pygame.font.SysFont(font_name, 18, bold=True)
        self.font_medium = pygame.font.SysFont(font_name, 14, bold=True)
        self.font_small = pygame.font.SysFont(font_name, 12, bold=False)
        self.font_tiny = pygame.font.SysFont(font_name, 10, bold=False)

    def draw_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        bg_color: Tuple[int, int, int, int] = COLOR_PANEL_BG,
        border_color: Tuple[int, int, int] = COLOR_PANEL_BORDER,
        border_radius: int = 6,
        border_width: int = 1,
    ) -> None:
        """Draw a semi-transparent dark panel with anti-aliased border."""
        panel_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel_surf.fill(bg_color)
        surface.blit(panel_surf, rect.topleft)

        if border_width > 0:
            pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=border_radius)

    def draw_badge(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        bg_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int] = (255, 255, 255),
        font: Optional[pygame.font.Font] = None,
    ) -> pygame.Rect:
        """Draw a compact colored status pill/badge."""
        f = font or self.font_tiny
        text_surf = f.render(text, True, text_color)
        padding_h = 6
        padding_v = 2
        badge_w = text_surf.get_width() + (padding_h * 2)
        badge_h = text_surf.get_height() + (padding_v * 2)

        badge_rect = pygame.Rect(x, y, badge_w, badge_h)
        pygame.draw.rect(surface, bg_color, badge_rect, border_radius=3)
        surface.blit(text_surf, (x + padding_h, y + padding_v))
        return badge_rect

    def draw_progress_bar(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        pct: float,
        fill_color: Tuple[int, int, int],
        bg_color: Tuple[int, int, int] = (30, 36, 48),
        border_color: Tuple[int, int, int] = (60, 72, 92),
    ) -> None:
        """Render a horizontal progress bar clamped between 0.0 and 1.0."""
        clamped_pct = max(0.0, min(pct, 1.0))
        # Background
        pygame.draw.rect(surface, bg_color, rect, border_radius=3)

        # Fill
        fill_w = int((rect.width - 2) * clamped_pct)
        if fill_w > 0:
            fill_rect = pygame.Rect(rect.x + 1, rect.y + 1, fill_w, rect.height - 2)
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=2)

        # Border
        pygame.draw.rect(surface, border_color, rect, width=1, border_radius=3)

    def draw_key_value(
        self,
        surface: pygame.Surface,
        label: str,
        value: str,
        x: int,
        y: int,
        width: int,
        font: Optional[pygame.font.Font] = None,
        label_color: Tuple[int, int, int] = COLOR_TEXT_SECONDARY,
        value_color: Tuple[int, int, int] = COLOR_TEXT_PRIMARY,
    ) -> int:
        """Draw a label and right-aligned value row. Returns height consumed."""
        f = font or self.font_small
        lbl_surf = f.render(label, True, label_color)
        val_surf = f.render(value, True, value_color)

        surface.blit(lbl_surf, (x, y))
        val_x = x + width - val_surf.get_width()
        surface.blit(val_surf, (val_x, y))

        return max(lbl_surf.get_height(), val_surf.get_height()) + 3
