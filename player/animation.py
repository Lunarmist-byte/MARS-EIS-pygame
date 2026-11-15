"""MARS SURVIVAL — Player Animation Controller.

Modular state-driven 2D animation system for Pygame.
Configured with the user-supplied Mars astronaut sprite sheet, supporting
multi-character selection (4 distinct crew members), directional mapping,
delta-time stepping cycles, and horizontal flipping for right-facing movement.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional, Tuple
import pygame
from config import ANIMATION_NAMES, CREW_MEMBERS


class AnimationController:
    """Manages player animation states, frames, and directional flipping."""

    def __init__(self, character_id: int = 1) -> None:
        self.character_id = character_id
        # Configurable animation frames storage: { anim_name: [Surface, Surface, ...] }
        self.animations: Dict[str, List[pygame.Surface]] = {name: [] for name in ANIMATION_NAMES}
        self.frame_durations: Dict[str, float] = {
            "idle": 0.45,
            "walk_down": 0.12,
            "walk_up": 0.12,
            "walk_left": 0.12,
            "walk_right": 0.12,
        }

        # Active state tracking
        self.current_animation: str = "idle"
        self.facing_direction: str = "down"  # Starts facing down
        self.current_frame_index: int = 0
        self.animation_timer: float = 0.0
        self.flip_horizontal: bool = False

        # Load astronaut sprites from assets/characters/
        self.load_crew_character(self.character_id)

    def load_crew_character(self, char_id: int) -> None:
        """Load animation frames for a specific astronaut crew member."""
        self.character_id = max(1, min(char_id, 4))
        base_dir = "assets/characters"

        # Check if pre-rendered sprite frames exist
        idle_files = [f"{base_dir}/char_{self.character_id}_idle_0.png", f"{base_dir}/char_{self.character_id}_idle_1.png"]
        walk_files = [f"{base_dir}/char_{self.character_id}_walk_{i}.png" for i in range(4)]

        has_files = all(os.path.exists(f) for f in idle_files + walk_files)

        if has_files:
            # Note: base sprite in char_*_walk_*.png is facing LEFT (as canonical walk_left)
            def _load_img(path: str) -> pygame.Surface:
                img = pygame.image.load(path)
                return img.convert_alpha() if pygame.display.get_surface() is not None else img

            walk_left_frames = [_load_img(f) for f in walk_files]
            idle_frames = [_load_img(f) for f in idle_files]

            # In accordance with API contract:
            # walk_left: Walking left
            # walk_right: Walking right (played as walk_left with flip_horizontal enabled)
            self.animations["walk_left"] = walk_left_frames
            self.animations["walk_right"] = walk_left_frames
            self.animations["walk_down"] = walk_left_frames
            self.animations["walk_up"] = walk_left_frames
            self.animations["idle"] = idle_frames
        else:
            # Fallback to procedural frames if asset not on disk
            self.animations = {name: [] for name in ANIMATION_NAMES}

    def set_animation_frames(
        self,
        animation_name: str,
        frames: List[pygame.Surface],
        frame_duration: float = 0.15
    ) -> None:
        """Register externally supplied frames for a designated animation name."""
        if animation_name in self.animations:
            self.animations[animation_name] = frames
            self.frame_durations[animation_name] = frame_duration

    def update(self, input_vector: pygame.Vector2, dt: float) -> None:
        """Update animation state and direction based on current player input."""
        is_moving = input_vector.length_squared() > 0.0

        if not is_moving:
            # When no movement input exists, play 'idle'
            self.current_animation = "idle"
            # Maintain last valid facing direction when player stops moving
            self.flip_horizontal = (self.facing_direction == "right")
        else:
            # Determine primary direction from input vector
            if abs(input_vector.x) > abs(input_vector.y):
                if input_vector.x < 0:
                    # Moving left: play walk_left (unflipped, since canonical frame faces left)
                    self.current_animation = "walk_left"
                    self.facing_direction = "left"
                    self.flip_horizontal = False
                else:
                    # Moving right: play walk_left with horizontal flipping enabled
                    self.current_animation = "walk_left"
                    self.facing_direction = "right"
                    self.flip_horizontal = True
            else:
                if input_vector.y < 0:
                    # Moving upward: play walk_up
                    self.current_animation = "walk_up"
                    self.facing_direction = "up"
                    # Preserve last horizontal flip orientation
                else:
                    # Moving downward: play walk_down
                    self.current_animation = "walk_down"
                    self.facing_direction = "down"

        # Advance frame timer
        active_frames = self.animations.get(self.current_animation, [])
        if active_frames:
            dur = self.frame_durations.get(self.current_animation, 0.15)
            self.animation_timer += dt
            if self.animation_timer >= dur:
                self.animation_timer = 0.0
                self.current_frame_index = (self.current_frame_index + 1) % len(active_frames)

    def get_current_frame(self) -> pygame.Surface:
        """Return the current frame Surface, applying horizontal flip if facing right."""
        active_frames = self.animations.get(self.current_animation, [])

        if active_frames:
            idx = min(self.current_frame_index, len(active_frames) - 1)
            surface = active_frames[idx]
        else:
            # Procedural fallback placeholder
            surface = self._get_fallback_placeholder(self.facing_direction)

        # Apply horizontal flipping for right-facing movement
        if self.flip_horizontal:
            return pygame.transform.flip(surface, True, False)

        return surface

    def _get_fallback_placeholder(self, facing: str) -> pygame.Surface:
        """Fallback placeholder surface if assets are missing."""
        surf = pygame.Surface((32, 56), pygame.SRCALPHA)
        pygame.draw.rect(surf, (220, 225, 235), (4, 16, 24, 28), border_radius=4)
        pygame.draw.circle(surf, (220, 225, 235), (16, 12), 10)
        pygame.draw.ellipse(surf, (245, 180, 45), (10, 8, 12, 7))
        return surf
