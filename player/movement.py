"""MARS SURVIVAL — Player Movement Controller.

Handles delta-time movement calculation, normalized diagonal velocity,
low-gravity Martian hops (0.38g), sprint acceleration, and periodic movement
telemetry accumulation for MARS-EIS regolith disturbance.

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
    """Manages player motion physics, low-g hops, and backend telemetry reporting."""

    def __init__(self, speed: float = PLAYER_SPEED) -> None:
        self.base_speed = speed
        self.speed = speed
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.input_vector = pygame.Vector2(0.0, 0.0)

        # Sprint & Thruster
        self.is_sprinting: bool = False

        # Low-Gravity Martian Hop Physics (0.38g)
        self.jump_z: float = 0.0
        self.jump_vz: float = 0.0
        self.gravity: float = 440.0   # Martian vertical gravity in px/s^2
        self.jump_strength: float = 180.0
        self.just_landed: bool = False

        # Footstep cadence tracker
        self.footstep_distance: float = 0.0
        self.footstep_interval: float = 38.0  # px between steps
        self.has_footstep: bool = False

        # Telemetry tracking
        self.accumulated_distance_m: float = 0.0
        self.sync_timer: float = 0.0
        self.last_sync_pos: Optional[pygame.Vector2] = None

    def start_jump(self) -> bool:
        """Initiate floaty Martian low-g hop."""
        if self.jump_z <= 0.01:
            self.jump_vz = self.jump_strength
            self.jump_z = 0.1
            return True
        return False

    def update_input(self, dx: float, dy: float, sprint: bool = False) -> None:
        """Update and normalize raw input direction vector with sprint multiplier."""
        self.input_vector.x = dx
        self.input_vector.y = dy
        self.is_sprinting = sprint

        current_speed = self.base_speed * (1.45 if sprint else 1.0)
        self.speed = current_speed

        # Normalize diagonal movement so diagonal speed equals cardinal speed
        if self.input_vector.length_squared() > 0.0:
            self.input_vector = self.input_vector.normalize()
            self.velocity = self.input_vector * self.speed
        else:
            self.velocity = pygame.Vector2(0.0, 0.0)

    def calculate_displacement(self, dt: float) -> pygame.Vector2:
        """Calculate frame displacement based on clock delta time and update hop physics."""
        self.just_landed = False
        self.has_footstep = False

        # 1. Update low-gravity hop vertical arc
        if self.jump_z > 0.0:
            self.jump_z += self.jump_vz * dt
            self.jump_vz -= self.gravity * dt
            if self.jump_z <= 0.0:
                self.jump_z = 0.0
                self.jump_vz = 0.0
                self.just_landed = True

        # 2. Footstep cadence when moving on ground
        disp = self.velocity * dt
        if self.jump_z <= 0.01 and disp.length_squared() > 0:
            self.footstep_distance += disp.length()
            if self.footstep_distance >= self.footstep_interval:
                self.footstep_distance = 0.0
                self.has_footstep = True

        return disp

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
            heading_deg = 0.0
            if self.velocity.length_squared() > 0:
                rad = math.atan2(self.velocity.x, -self.velocity.y)
                heading_deg = (math.degrees(rad) + 360.0) % 360.0

            telemetry = {
                "distance_meters": round(self.accumulated_distance_m, 2),
                "speed_ms": round((self.speed * METERS_PER_PIXEL), 2),
                "heading_deg": round(heading_deg, 1),
                "world_position": [round(current_pos.x * METERS_PER_PIXEL, 2), round(current_pos.y * METERS_PER_PIXEL, 2), round(self.jump_z * METERS_PER_PIXEL, 2)],
            }
            self.accumulated_distance_m = 0.0
            self.sync_timer = 0.0
            return telemetry

        return None
