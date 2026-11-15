"""MARS SURVIVAL — Optimized Font Management & Glyph Cache.

Provides lightning-fast, zero-allocation font caching to eliminate
per-frame SysFont lookups and garbage collection spikes.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import Dict, Tuple
import pygame


class FontManager:
    """Centralized font cache for 8-bit retro arcade typography."""

    _cache: Dict[Tuple[str, int, bool], pygame.font.Font] = {}
    _default_family: str = "Consolas"

    @classmethod
    def get(cls, size: int = 11, bold: bool = False, family: str = "Consolas") -> pygame.font.Font:
        """Retrieve pre-cached font instance or construct once."""
        key = (family, size, bold)
        font = cls._cache.get(key)
        if font is None:
            if not pygame.font.get_init():
                pygame.font.init()
            try:
                font = pygame.font.SysFont(family, size, bold=bold)
            except Exception:
                font = pygame.font.Font(None, size)
            cls._cache[key] = font
        return font

    @classmethod
    def clear(cls) -> None:
        """Clear cached fonts."""
        cls._cache.clear()
