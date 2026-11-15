"""MARS SURVIVAL — Collectible Martian Research Cores & Field Samples.

Scatters scientific samples and geological cores across the Jezero base perimeter:
- Ancient Olivine Olivine Crystals
- Perchlorate Glacial Ice Cores
- Iron-Nickel Meteorite Shards
- Subsurface Fossilized Regolith
- NASA Telemetry Data Storage Wafers

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
import pygame
from config import WORLD_SCALE


@dataclass
class MartianArtifact:
    """A collectible research artifact in world space."""
    artifact_id: str
    name: str
    description: str
    world_x: float
    world_y: float
    science_points: int
    color: Tuple[int, int, int]
    collected: bool = False
    phase: float = 0.0


class CollectiblesSystem:
    """Coordinates scattered scientific artifacts, pickup detection, and rendering."""

    def __init__(self) -> None:
        self.artifacts: List[MartianArtifact] = [
            MartianArtifact(
                artifact_id="art_olivine",
                name="Ancient Jezero Olivine Crystal",
                description="Igneous basaltic crystal rich in magnesium from crater floor.",
                world_x=120 * WORLD_SCALE,
                world_y=110 * WORLD_SCALE,
                science_points=100,
                color=(120, 240, 150),
                phase=0.0,
            ),
            MartianArtifact(
                artifact_id="art_meteorite",
                name="Chondritic Nickel-Iron Meteorite",
                description="Extra-Martian meteorite shard containing primordial solar metals.",
                world_x=220 * WORLD_SCALE,
                world_y=140 * WORLD_SCALE,
                science_points=150,
                color=(240, 180, 80),
                phase=1.2,
            ),
            MartianArtifact(
                artifact_id="art_ice_core",
                name="Subsurface Perchlorate Ice Core",
                description="Cryogenic sample preserving ancient Martian hydrological records.",
                world_x=110 * WORLD_SCALE,
                world_y=610 * WORLD_SCALE,
                science_points=120,
                color=(100, 220, 255),
                phase=2.4,
            ),
            MartianArtifact(
                artifact_id="art_data_wafer",
                name="NASA Rover Telemetry Cache",
                description="Hardened memory module left by previous uncrewed exploration rover.",
                world_x=70 * WORLD_SCALE,
                world_y=380 * WORLD_SCALE,
                science_points=200,
                color=(255, 120, 200),
                phase=3.6,
            ),
            MartianArtifact(
                artifact_id="art_regolith_fossil",
                name="Sedimentary Delta Mudstone Shard",
                description="Fine-grained clay deposited in ancient Jezero river delta.",
                world_x=255 * WORLD_SCALE,
                world_y=600 * WORLD_SCALE,
                science_points=180,
                color=(230, 140, 90),
                phase=4.8,
            ),
            MartianArtifact(
                artifact_id="art_solar_cell",
                name="Experimental Perovskite PV Cell",
                description="High-efficiency tandem photovoltaic prototype.",
                world_x=200 * WORLD_SCALE,
                world_y=65 * WORLD_SCALE,
                science_points=110,
                color=(255, 230, 80),
                phase=5.5,
            ),
        ]
        self.total_science_score: int = 0
        self.total_collected: int = 0
        self.anim_time: float = 0.0

    def update(self, dt: float, player_world_pos: pygame.Vector2) -> Optional[MartianArtifact]:
        """Check for player proximity pickup (radius = 32px).
        
        Returns:
            The collected MartianArtifact if picked up this frame, otherwise None.
        """
        self.anim_time += dt
        pickup_radius = 36.0

        for art in self.artifacts:
            if art.collected:
                continue

            dist = math.hypot(player_world_pos.x - art.world_x, player_world_pos.y - art.world_y)
            if dist <= pickup_radius:
                art.collected = True
                self.total_science_score += art.science_points
                self.total_collected += 1
                return art

        return None

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        """Render floating shimmering crystals with glowing auras."""
        for art in self.artifacts:
            if art.collected:
                continue

            sp = camera.world_to_screen(art.world_x, art.world_y)
            # Viewport culling
            if not (-30 <= sp.x <= surface.get_width() + 30 and -30 <= sp.y <= surface.get_height() + 30):
                continue

            # Vertical floating bob animation
            bob = math.sin(self.anim_time * 3.2 + art.phase) * 5.0
            cx = int(sp.x)
            cy = int(sp.y + bob)

            # 1. Glowing ground shadow
            shadow_surf = pygame.Surface((18, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90), (0, 0, 18, 6))
            surface.blit(shadow_surf, (cx - 9, int(sp.y + 12)))

            # 2. Glowing pulse halo
            pulse = 0.5 + 0.5 * math.sin(self.anim_time * 5.0 + art.phase)
            glow_radius = int(12 + pulse * 4)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            halo_alpha = int(60 + pulse * 45)
            pygame.draw.circle(glow_surf, (*art.color, halo_alpha), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (cx - glow_radius, cy - glow_radius))

            # 3. Rotating Diamond Crystal shape
            pts = [
                (cx, cy - 8),
                (cx + 6, cy),
                (cx, cy + 8),
                (cx - 6, cy),
            ]
            pygame.draw.polygon(surface, art.color, pts)
            pygame.draw.polygon(surface, (255, 255, 255), pts, width=1)

            # Specular sparkle center
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)
