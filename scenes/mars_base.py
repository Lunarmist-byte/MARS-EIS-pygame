"""MARS SURVIVAL — Mars Base Environment Scene.

Loads and renders the provided Mars base background image, strictly preserving
original image aspect ratio and artistic appearance. Provides world bounds,
camera-relative rendering, and base facility location registry.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
import math
from typing import Dict, Any, Optional, Tuple, List
import pygame
from config import (
    BACKGROUND_PATH,
    WORLD_SCALE,
    BASE_WIDTH,
    BASE_HEIGHT,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    BASE_FACILITIES,
)
from systems.camera import Camera
from .doors import DoorManager


class MarsBase:
    """Represents the exterior playable Mars base environment."""

    def __init__(self, bg_path: str = BACKGROUND_PATH) -> None:
        self.bg_path = bg_path
        self.raw_surface: pygame.Surface
        self.scaled_surface: pygame.Surface
        self.world_rect: pygame.Rect

        # Facility landmarks configuration
        self.facilities = BASE_FACILITIES

        # Automated blast doors & airlocks
        self.door_manager = DoorManager()

        # Load and scale background with strict aspect ratio preservation
        self._load_environment_art()
        self._load_collision_mask()

    def _load_collision_mask(self) -> None:
        """Load wall collision bitmask generated from map architecture."""
        mask_path = "assets/backgrounds/mars_base_collision_mask.png"
        if os.path.exists(mask_path):
            mask_surf = pygame.image.load(mask_path)
            self.collision_mask = pygame.mask.from_surface(mask_surf)
        else:
            self.collision_mask = None

    def _load_environment_art(self) -> None:
        """Load background artwork and prepare scaled world surface."""
        if not os.path.exists(self.bg_path):
            raise FileNotFoundError(f"Mars base background artwork missing at {self.bg_path}")

        # Load raw original background (1024 x 682)
        loaded = pygame.image.load(self.bg_path)
        if pygame.display.get_surface() is not None:
            self.raw_surface = loaded.convert()
        else:
            self.raw_surface = loaded
        orig_w, orig_h = self.raw_surface.get_size()

        # Calculate world dimensions preserving exact aspect ratio
        aspect = orig_w / float(orig_h)
        target_w = int(orig_w * WORLD_SCALE)
        target_h = int(target_w / aspect)

        # Scale surface cleanly
        if WORLD_SCALE != 1.0:
            self.scaled_surface = pygame.transform.smoothscale(self.raw_surface, (target_w, target_h))
        else:
            self.scaled_surface = self.raw_surface

        self.world_rect = pygame.Rect(0, 0, target_w, target_h)

    def update(self, dt: float, player_pos: Tuple[float, float]) -> None:
        """Update automated base doors against player position."""
        self.door_manager.update(dt, player_pos)

    def render(self, surface: pygame.Surface, camera: Camera) -> None:
        """Render background and automated doors relative to camera viewport."""
        # Calculate sub-rectangle visible within the camera view
        view_rect = camera.get_view_rect()
        
        # Clip view rect to world boundaries
        clipped_rect = view_rect.clip(self.world_rect)

        if clipped_rect.width > 0 and clipped_rect.height > 0:
            # Subsurface blitting is high performance and avoids drawing off-screen pixels
            sub = self.scaled_surface.subsurface(clipped_rect)
            # Screen destination corresponds to clipped rect offset from camera
            dest_x = clipped_rect.x - camera.offset_x
            dest_y = clipped_rect.y - camera.offset_y
            surface.blit(sub, (dest_x, dest_y))

        # Render automated blast doors and airlocks
        self.door_manager.render(surface, camera)

    def get_nearby_facility(
        self,
        player_pos: Tuple[float, float],
        interaction_radius: float = 120.0
    ) -> Optional[Dict[str, Any]]:
        """Check if astronaut is standing near any base facility landmark."""
        px, py = player_pos
        for fac_id, info in self.facilities.items():
            rect_tuple = info.get("rect", (0, 0, 50, 50))
            fac_rect = pygame.Rect(rect_tuple)
            # Center of facility
            cx, cy = fac_rect.center
            dist = math.hypot(px - cx, py - cy)
            if dist <= interaction_radius:
                res = dict(info)
                res["facility_id"] = fac_id
                res["distance"] = dist
                return res
        return None

    def check_foot_collision(self, world_x: float, world_y: float) -> bool:
        """Check if an entity's foot placement at (world_x, world_y) collides with a wall or closed door.
        
        Uses the high-precision 1-bit collision mask scaled to world space and checks closed blast doors.
        Returns True if the foot position intersects a solid wall or closed door.
        """
        # 1. Check if blocked by any closed blast door
        foot_y = world_y + 18.0
        if hasattr(self, "door_manager") and self.door_manager.check_collision(world_x, foot_y):
            return True

        if not self.collision_mask:
            return False

        # Convert world coordinates (2048 x 1364) to mask space (1024 x 682)
        mx = world_x / WORLD_SCALE
        # Astronaut feet are located near the bottom of the sprite (+18px offset in world space)
        my = foot_y / WORLD_SCALE

        # Check sample footprint points (center, left, right, top, bottom)
        hw = 3.5  # half-width in mask space (~7px world width)
        hh = 2.0  # half-height in mask space (~4px world height)
        sample_offsets = [
            (0.0, 0.0),
            (-hw, 0.0),
            (hw, 0.0),
            (0.0, -hh),
            (0.0, hh),
        ]

        mask_w, mask_h = self.collision_mask.get_size()
        for ox, oy in sample_offsets:
            px = int(mx + ox)
            py = int(my + oy)
            if 0 <= px < mask_w and 0 <= py < mask_h:
                if self.collision_mask.get_at((px, py)):
                    return True  # Solid wall collision detected
            else:
                return True  # Outside base world bounds

        return False

    def check_collision(self, candidate_rect: pygame.Rect) -> bool:
        """Check if a candidate world rectangle collides with any wall."""
        return self.check_foot_collision(candidate_rect.centerx, candidate_rect.centery)
