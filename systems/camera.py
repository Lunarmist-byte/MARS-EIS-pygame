"""MARS SURVIVAL — 2D World Camera System.

Translates world coordinate entities to screen viewport coordinates,
smoothly tracks the player character, and prevents camera overshoot
beyond outer Mars base world boundaries.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import Tuple, Union
import pygame


class Camera:
    """Follows target entity in world space and translates to screen coordinates."""

    def __init__(
        self,
        viewport_width: int,
        viewport_height: int,
        world_width: int,
        world_height: int,
        smoothing: float = 0.12
    ) -> None:
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.world_width = world_width
        self.world_height = world_height
        self.smoothing = smoothing

        # Camera viewport top-left corner in world space
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0

    def update(self, target_pos: Union[pygame.Vector2, Tuple[float, float]], dt: float = 0.016) -> None:
        """Update camera target tracking with smooth damping and boundary clamping."""
        target_x = target_pos[0] if isinstance(target_pos, (tuple, list)) else target_pos.x
        target_y = target_pos[1] if isinstance(target_pos, (tuple, list)) else target_pos.y

        # Ideal camera top-left position to place target at viewport center
        desired_offset_x = target_x - (self.viewport_width / 2.0)
        desired_offset_y = target_y - (self.viewport_height / 2.0)

        # Smooth camera movement
        self.offset_x += (desired_offset_x - self.offset_x) * min(1.0, self.smoothing * 60.0 * dt)
        self.offset_y += (desired_offset_y - self.offset_y) * min(1.0, self.smoothing * 60.0 * dt)

        # Clamp camera viewport within world boundaries
        # Prevents rendering void space beyond map borders
        max_offset_x = max(0.0, float(self.world_width - self.viewport_width))
        max_offset_y = max(0.0, float(self.world_height - self.viewport_height))

        self.offset_x = max(0.0, min(self.offset_x, max_offset_x))
        self.offset_y = max(0.0, min(self.offset_y, max_offset_y))

    def world_to_screen(self, world_x: float, world_y: float) -> pygame.Vector2:
        """Convert world coordinates to screen display coordinates."""
        return pygame.Vector2(world_x - self.offset_x, world_y - self.offset_y)

    def screen_to_world(self, screen_x: float, screen_y: float) -> pygame.Vector2:
        """Convert screen pixel coordinates to world coordinates."""
        return pygame.Vector2(screen_x + self.offset_x, screen_y + self.offset_y)

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Translate a world rectangle to a screen-space rectangle."""
        return rect.move(int(-self.offset_x), int(-self.offset_y))

    def get_view_rect(self) -> pygame.Rect:
        """Return the current camera viewport in world space."""
        return pygame.Rect(
            int(self.offset_x),
            int(self.offset_y),
            self.viewport_width,
            self.viewport_height
        )
