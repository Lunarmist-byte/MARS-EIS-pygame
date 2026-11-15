"""MARS SURVIVAL — Crew NPC & Interactive Dialogue System.

Places the other 3 astronaut crew members from the user sprite sheet into the base
as living interactive NPCs:
- Amal (Sprite 3, Comms): Communications Specialist at Deep Space Telemetry / Comms Hub
- Gowri (Sprite 2, Research Fellow): Astrobiologist in Hydroponic Greenhouse & Medbay
- Christy (Sprite 4, Engineer): Chief Robotics & Systems Engineer in Workshop & Reactor

Commander Suso (Sprite 1) is the active main player character.

Provides 8-bit retro arcade name tags, proximity prompts, and interactive
mission dialogues with station advice and stat boosts.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any, Dict
import pygame
from config import WORLD_SCALE


class CrewNPC:
    """An interactive crew member NPC in the base environment."""

    def __init__(
        self,
        npc_id: str,
        name: str,
        role: str,
        sprite_id: int,
        world_x: float,
        world_y: float,
        dialogues: List[str],
    ) -> None:
        self.npc_id = npc_id
        self.name = name
        self.role = role
        self.sprite_id = sprite_id
        self.world_x = world_x
        self.world_y = world_y
        self.dialogues = dialogues
        self.dialogue_index = 0

        # Animation state
        self.idle_frames: List[pygame.Surface] = []
        self.avatar_img: Optional[pygame.Surface] = None
        self.frame_index = 0
        self.anim_timer = 0.0
        self.facing_right = False
        self._load_sprites()

    def _load_sprites(self) -> None:
        """Load character idle frames and avatar portrait."""
        base_dir = "assets/characters"
        f0 = f"{base_dir}/char_{self.sprite_id}_idle_0.png"
        f1 = f"{base_dir}/char_{self.sprite_id}_idle_1.png"
        av = f"{base_dir}/char_{self.sprite_id}_avatar.png"

        def _load(path: str) -> Optional[pygame.Surface]:
            if os.path.exists(path):
                img = pygame.image.load(path)
                return img.convert_alpha() if pygame.display.get_surface() else img
            return None

        img0 = _load(f0)
        img1 = _load(f1)
        if img0 and img1:
            self.idle_frames = [img0, img1]
        elif img0:
            self.idle_frames = [img0]
        else:
            # Fallback placeholder 32x56 surface
            surf = pygame.Surface((32, 56), pygame.SRCALPHA)
            surf.fill((60, 120, 200, 200))
            self.idle_frames = [surf]

        self.avatar_img = _load(av)

    def update(self, dt: float, player_world_pos: pygame.Vector2) -> None:
        """Update idle breathing animation and face toward player."""
        self.anim_timer += dt
        if self.anim_timer >= 0.45:
            self.anim_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.idle_frames)

        # Turn to face player
        self.facing_right = (player_world_pos.x > self.world_x)

    def get_current_dialogue(self) -> str:
        """Get dialogue and cycle to next line."""
        text = self.dialogues[self.dialogue_index % len(self.dialogues)]
        self.dialogue_index += 1
        return text

    def render(self, surface: pygame.Surface, camera: Any, is_near: bool = False) -> None:
        """Render NPC sprite, ground shadow, 8-bit name tag, and proximity indicator."""
        sp = camera.world_to_screen(self.world_x, self.world_y)
        # Viewport culling
        if not (-40 <= sp.x <= surface.get_width() + 40 and -40 <= sp.y <= surface.get_height() + 40):
            return

        cx, cy = int(sp.x), int(sp.y)

        # 1. Ground shadow
        shadow_surf = pygame.Surface((22, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90), (0, 0, 22, 6))
        surface.blit(shadow_surf, (cx - 11, cy + 24))

        # 2. Main character frame
        frame = self.idle_frames[self.frame_index]
        if self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        frame_rect = frame.get_rect(center=(cx, cy))
        surface.blit(frame, frame_rect.topleft)

        # 3. 8-Bit Retro Name Badge
        font_badge = pygame.font.SysFont("Consolas", 10, bold=True)
        tag_text = f"[{self.name.upper()}]"
        tag_surf = font_badge.render(tag_text, True, (0, 255, 200))
        tag_bg = pygame.Surface((tag_surf.get_width() + 6, tag_surf.get_height() + 2))
        tag_bg.fill((10, 15, 25))
        pygame.draw.rect(tag_bg, (0, 255, 200), (0, 0, tag_bg.get_width(), tag_bg.get_height()), width=1)
        tag_bg.blit(tag_surf, (3, 1))
        surface.blit(tag_bg, (cx - tag_bg.get_width() // 2, cy - 38))

        # 4. Proximity "[E] TALK" Prompt
        if is_near:
            prompt_font = pygame.font.SysFont("Consolas", 11, bold=True)
            p_surf = prompt_font.render("[E] TALK", True, (255, 220, 0))
            p_bg = pygame.Surface((p_surf.get_width() + 8, p_surf.get_height() + 2))
            p_bg.fill((20, 24, 34))
            pygame.draw.rect(p_bg, (255, 220, 0), (0, 0, p_bg.get_width(), p_bg.get_height()), width=1)
            p_bg.blit(p_surf, (4, 1))
            surface.blit(p_bg, (cx - p_bg.get_width() // 2, cy - 54))


class NPCSystem:
    """Manages base crew NPCs, proximity dialogue, and rendering."""

    def __init__(self) -> None:
        self.all_npcs: List[CrewNPC] = [
            CrewNPC(
                npc_id="npc_suso",
                name="Commander Suso",
                role="Mission Commander",
                sprite_id=1,
                world_x=450 * WORLD_SCALE,
                world_y=410 * WORLD_SCALE,
                dialogues=[
                    "Commander Suso here! Great to see you on station. All habitat telemetry and ECLSS reserves are green.",
                    "Keep the exterior solar arrays clear of ferric dust and monitor battery charge levels.",
                    "Proceed with your research and engineering operations. Jezero base is running smoothly.",
                    "Radio comms to mission control are open. Outstanding work keeping the expedition on track!",
                ],
            ),
            CrewNPC(
                npc_id="npc_amal",
                name="Amal",
                role="Comms Specialist",
                sprite_id=3,
                world_x=340 * WORLD_SCALE,
                world_y=210 * WORLD_SCALE,
                dialogues=[
                    "Commander Suso! Amal here at telemetry comms. Deep space relays to Earth are nominal and green!",
                    "Orbital downlink is tracking solar wind velocity. Let me know if you need satellite packet synchronization.",
                    "Radio bursts across Jezero are within background limits. All comms channels are listening for your transmission, Commander!",
                    "Keep that EVA suit transceiver powered. If an emergency arises, my relay channel is always open!",
                ],
            ),
            CrewNPC(
                npc_id="npc_gowri",
                name="Gowri",
                role="Research Fellow",
                sprite_id=2,
                world_x=280 * WORLD_SCALE,
                world_y=560 * WORLD_SCALE,
                dialogues=[
                    "Commander Suso! Gowri reporting from the research lab. The extraterrestrial crop samples and spirulina cultures are thriving!",
                    "Atmospheric CO2 scrubbers and hydroponic beds are balancing ECLSS oxygen reserves nicely.",
                    "I'm analyzing ancient hydrated silica clay cores from the Jezero river delta. Fascinating microbial fossil markers!",
                    "If your EVA vitals drop or suit integrity takes a hit, visit the Medbay bio-scanner for regenerative biocell dressings!",
                ],
            ),
            CrewNPC(
                npc_id="npc_christy",
                name="Christy",
                role="Chief Engineer",
                sprite_id=4,
                world_x=660 * WORLD_SCALE,
                world_y=560 * WORLD_SCALE,
                dialogues=[
                    "Commander Suso! Christy on engineering duty. I've tuned the workshop 3D milling arm and checked the reactor bus.",
                    "Ferric basalt dust is always blowing across the solar arrays. Press [C] or use the wiper to keep power flowing!",
                    "Subsurface perchlorate drill motors are primed. Hit the grid challenge markers when you need regolith excavation cores.",
                    "The fission power grid is holding strong at 2.7 kW. Let me know if you need emergency circuits routed!",
                ],
            ),
        ]
        self.active_player_id: int = 1
        # By default, player is Commander Suso (1), so NPCs are Amal (3), Gowri (2), and Christy (4)
        self.npcs: List[CrewNPC] = [npc for npc in self.all_npcs if npc.sprite_id != 1]

        # Active dialogue overlay state
        self.active_dialogue: Optional[Dict[str, Any]] = None
        self.dialogue_timer: float = 0.0

    def set_active_player(self, character_id: int) -> None:
        """Update active crew member; the other 3 become interactive NPCs."""
        self.active_player_id = character_id
        self.npcs = [npc for npc in self.all_npcs if npc.sprite_id != character_id]

    def get_nearby_npc(self, player_world_pos: pygame.Vector2, radius: float = 65.0) -> Optional[CrewNPC]:
        """Find NPC within talking range."""
        for npc in self.npcs:
            dist = math.hypot(player_world_pos.x - npc.world_x, player_world_pos.y - npc.world_y)
            if dist <= radius:
                return npc
        return None

    def trigger_talk(self, player_world_pos: pygame.Vector2) -> Optional[str]:
        """Trigger dialogue with nearby NPC."""
        npc = self.get_nearby_npc(player_world_pos)
        if not npc:
            return None

        line = npc.get_current_dialogue()
        self.active_dialogue = {
            "name": npc.name,
            "role": npc.role,
            "avatar": npc.avatar_img,
            "text": line,
        }
        self.dialogue_timer = 5.0
        return f"{npc.name}: \"{line}\""

    def update(self, dt: float, player_world_pos: pygame.Vector2) -> None:
        """Update NPC animations and active dialogue timeout."""
        for npc in self.npcs:
            npc.update(dt, player_world_pos)

        if self.dialogue_timer > 0:
            self.dialogue_timer -= dt
            if self.dialogue_timer <= 0:
                self.active_dialogue = None

    def render(self, surface: pygame.Surface, camera: Any, player_world_pos: pygame.Vector2) -> None:
        """Render all NPCs and active 8-bit retro dialogue box."""
        # 1. Render NPC sprites
        for npc in self.npcs:
            dist = math.hypot(player_world_pos.x - npc.world_x, player_world_pos.y - npc.world_y)
            is_near = (dist <= 65.0)
            npc.render(surface, camera, is_near=is_near)

        # 2. Render 8-Bit Retro Dialogue Box if active
        if self.active_dialogue:
            d = self.active_dialogue
            w = 820
            h = 75
            x = (surface.get_width() - w) // 2
            y = surface.get_height() - 130

            # Retro solid black/navy box with cyan 8-bit border
            box_surf = pygame.Surface((w, h))
            box_surf.fill((8, 12, 18))
            pygame.draw.rect(box_surf, (0, 255, 200), (0, 0, w, h), width=2)
            pygame.draw.rect(box_surf, (0, 180, 140), (3, 3, w - 6, h - 6), width=1)

            # Avatar portrait
            if d.get("avatar"):
                av = d["avatar"]
                box_surf.blit(av, (8, 8))
                pygame.draw.rect(box_surf, (0, 255, 200), (7, 7, 38, 38), width=1)
                text_x = 56
            else:
                text_x = 16

            # Name header
            font_title = pygame.font.SysFont("Consolas", 13, bold=True)
            font_body = pygame.font.SysFont("Consolas", 12)
            title = font_title.render(f">> {d['name'].upper()} // {d['role'].upper()}", True, (255, 220, 0))
            box_surf.blit(title, (text_x, 8))

            # Dialogue body
            body = font_body.render(f"\"{d['text']}\"", True, (240, 245, 250))
            box_surf.blit(body, (text_x, 28))

            hint = font_body.render("[E] Next  |  [ESC] Close", True, (100, 130, 160))
            box_surf.blit(hint, (w - 180, 52))

            surface.blit(box_surf, (x, y))
