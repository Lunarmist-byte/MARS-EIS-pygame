"""MARS SURVIVAL — Player State Model.

Tracks local client-side player position, health, interaction state,
traversed distance, and planetary coordinate transformations.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple
from config import METERS_PER_PIXEL, DEFAULT_SPAWN_X, DEFAULT_SPAWN_Y


@dataclass
class PlayerState:
    """Client-side player state representation."""
    x: float = DEFAULT_SPAWN_X
    y: float = DEFAULT_SPAWN_Y
    health: float = 100.0
    current_action: str = "IDLE"
    facing_direction: str = "down"

    # Environmental zone & EVA Exploration state
    is_outside: bool = False
    location_name: str = "Base Hab Interior"

    # Action execution feedback
    last_action_message: str = "System Initialized"
    last_action_success: Optional[bool] = True
    action_feedback_timer: float = 4.0

    # Continuous movement metrics for backend reporting
    accumulated_distance_px: float = 0.0
    speed_px_s: float = 0.0
    last_movement_sync_x: float = DEFAULT_SPAWN_X
    last_movement_sync_y: float = DEFAULT_SPAWN_Y

    # Sequence number for ordered actions
    action_sequence: int = 0

    def next_action_id(self, prefix: str = "act") -> str:
        """Generate a sequential unique action identifier."""
        self.action_sequence += 1
        return f"{prefix}_{self.action_sequence:05d}"

    def get_world_pos(self) -> Tuple[float, float]:
        """Return world coordinates (pixels)."""
        return self.x, self.y

    def get_planetary_coords_m(self) -> Tuple[float, float]:
        """Convert world pixels to physical meters relative to origin."""
        return round(self.x * METERS_PER_PIXEL, 2), round(self.y * METERS_PER_PIXEL, 2)

    def set_action_feedback(self, message: str, success: bool, duration: float = 4.0) -> None:
        """Update last action status display."""
        self.last_action_message = message
        self.last_action_success = success
        self.action_feedback_timer = duration

    def update_timers(self, dt: float) -> None:
        """Update action feedback timer."""
        if self.action_feedback_timer > 0.0:
            self.action_feedback_timer = max(0.0, self.action_feedback_timer - dt)
