"""MARS SURVIVAL — Player Movement Controller.

Handles delta-time movement calculation, normalized diagonal velocity,
and periodic movement telemetry accumulation for MARS-EIS regolith disturbance.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, Dict, Any
import pygame
from config import PLAYER_SPEED, METERS_PER_PIXEL, MOVEMENT_SYNC_INTERVAL, MOVEMENT_MIN_DISTANCE_M


class MovementController:
    """Manages player motion physics and backend telemetry reporting."""

    def __init__(self, speed: float = PLAYER_SPEED) -> None:
        self.speed = speed
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.input_vector = pygame.Vector2(0.0, 0.0)

        # Telemetry tracking
        self.accumulated_distance_m: float = 0.0
        self.sync_timer: float = 0.0
        self.last_sync_pos: Optional[pygame.Vector2] = None

    def update_input(self, dx: float, dy: float) -> None:
        """Update and normalize raw input direction vector."""
        self.input_vector.x = dx
        self.input_vector.y = dy

        # Normalize diagonal movement so diagonal speed equals cardinal speed
        if self.input_vector.length_squared() > 0.0:
            self.input_vector = self.input_vector.normalize()
            self.velocity = self.input_vector * self.speed
        else:
            self.velocity = pygame.Vector2(0.0, 0.0)

    def calculate_displacement(self, dt: float) -> pygame.Vector2:
        """Calculate frame displacement based on clock delta time."""
        return self.velocity * dt

    def track_movement(self, current_pos: pygame.Vector2, dt: float) -> Optional[Dict[str, Any]]:
        """Accumulate traversed physical distance and check if telemetry sync is due.
        
        Avoids sending network packets every rendered frame.
        """
        if self.last_sync_pos is None:
            self.last_sync_pos = pygame.Vector2(current_pos)
            return None

        disp_px = current_pos.distance_to(self.last_sync_pos)
        self.accumulated_distance_m += disp_px * METERS_PER_PIXEL
        self.last_sync_pos = pygame.Vector2(current_pos)
        self.sync_timer += dt

        # Send periodic movement update when distance threshold or timer reached
        if (self.accumulated_distance_m >= MOVEMENT_MIN_DISTANCE_M and self.sync_timer >= MOVEMENT_SYNC_INTERVAL):
            # Calculate heading in degrees (0 = North/Up, 90 = East/Right, etc.)
            heading_deg = 0.0
            if self.velocity.length_squared() > 0:
                rad = math.atan2(self.velocity.x, -self.velocity.y)
                heading_deg = (math.degrees(rad) + 360.0) % 360.0

            telemetry = {
                "distance_meters": round(self.accumulated_distance_m, 2),
                "speed_ms": round((self.speed * METERS_PER_PIXEL), 2),
                "heading_deg": round(heading_deg, 1),
                "world_position": [round(current_pos.x * METERS_PER_PIXEL, 2), round(current_pos.y * METERS_PER_PIXEL, 2), 0.0],
            }
            # Reset telemetry counters
            self.accumulated_distance_m = 0.0
            self.sync_timer = 0.0
            return telemetry

        return None
