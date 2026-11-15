"""MARS SURVIVAL — Crew NPC & Interactive Dialogue System.

Places the other 3 astronaut crew members from the user sprite sheet into the base
as living interactive NPCs:
- Amal (Sprite 3, Comms): Communications Specialist at Deep Space Telemetry / Comms Hub
- Gowri (Sprite 2, Research Fellow): Astrobiologist in Hydroponic Greenhouse & Medbay
- Christy (Sprite 4, Engineer): Chief Robotics & Systems Engineer in Workshop & Reactor

Commander Suso (Sprite 1) is the active main player character.

Supports:
- Proximity dialogue & advice
- Autonomous station patrolling during calm periods
- Emergency evacuation: When a catastrophe strikes, NPCs shout and sprint inside to the central habitat shelter
- Emergency repair guidance dialogues during catastrophes until 100% space health is restored

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
import os
import random
from typing import List, Optional, Tuple, Any, Dict
import pygame
from config import WORLD_SCALE
from ui.font_manager import FontManager


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
        shelter_x: float,
        shelter_y: float,
        dialogues: List[str],
        emergency_dialogues: Optional[List[str]] = None,
        corridor_waypoints: Optional[List[Tuple[float, float]]] = None,
    ) -> None:
        self.npc_id = npc_id
        self.name = name
        self.role = role
        self.sprite_id = sprite_id
        self.world_x = world_x
        self.world_y = world_y
        self.nominal_x = world_x
        self.nominal_y = world_y
        self.shelter_x = shelter_x
        self.shelter_y = shelter_y
        self.dialogues = dialogues
        self.emergency_dialogues = emergency_dialogues or [
            f"{name}: EMERGENCY! Station integrity compromised! Repair the grid challenges to restore 100% Space Health!",
            f"{name}: Pressure and radiation alarms are screaming! Get to the damaged modules and complete repairs!",
        ]
        self.dialogue_index = 0
        self.emergency_dialogue_index = 0

        # Corridors to shelter
        self.corridor_waypoints = corridor_waypoints or []
        self.current_waypoints: List[Tuple[float, float]] = []

        # State: "NOMINAL", "FLEEING_INSIDE", "SHELTERED", "RETURNING"
        self.state = "NOMINAL"
        self.move_speed = 180.0
        self.is_moving = False
        self.wander_timer = 0.0

        # Animation states
        self.idle_frames: List[pygame.Surface] = []
        self.walk_frames: List[pygame.Surface] = []
        self.avatar_img: Optional[pygame.Surface] = None
        self.idle_frame_index = 0
        self.walk_frame_index = 0
        self.anim_timer = 0.0
        self.facing_right = False

        # Shouting bubble
        self.shout_text: Optional[str] = None
        self.shout_timer: float = 0.0

        self._load_sprites()

    def _load_sprites(self) -> None:
        """Load character idle frames, walk frames, and avatar portrait."""
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
            surf = pygame.Surface((32, 56), pygame.SRCALPHA)
            surf.fill((60, 120, 200, 200))
            self.idle_frames = [surf]

        walk_files = [f"{base_dir}/char_{self.sprite_id}_walk_{i}.png" for i in range(4)]
        self.walk_frames = [_load(f) for f in walk_files if os.path.exists(f)]
        if not self.walk_frames:
            self.walk_frames = self.idle_frames

        self.avatar_img = _load(av)

        # Pre-bake static visual surfaces to eliminate per-frame allocations
        self.shadow_surf = pygame.Surface((22, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow_surf, (0, 0, 0, 90), (0, 0, 22, 6))

        # Badges
        font_badge = FontManager.get(10, bold=True)

        # 1. Nominal Badge [NAME]
        tag_text = f"[{self.name.upper()}]"
        tag_surf = font_badge.render(tag_text, True, (0, 255, 200))
        self.badge_surf = pygame.Surface((tag_surf.get_width() + 6, tag_surf.get_height() + 2))
        self.badge_surf.fill((10, 15, 25))
        pygame.draw.rect(self.badge_surf, (0, 255, 200), (0, 0, self.badge_surf.get_width(), self.badge_surf.get_height()), width=1)
        self.badge_surf.blit(tag_surf, (3, 1))

        # 2. Fleeing Badge [EVACUATING!]
        flee_surf = font_badge.render("[EVACUATING!]", True, (255, 60, 60))
        self.flee_badge_surf = pygame.Surface((flee_surf.get_width() + 6, flee_surf.get_height() + 2))
        self.flee_badge_surf.fill((30, 8, 8))
        pygame.draw.rect(self.flee_badge_surf, (255, 60, 60), (0, 0, self.flee_badge_surf.get_width(), self.flee_badge_surf.get_height()), width=1)
        self.flee_badge_surf.blit(flee_surf, (3, 1))

        # 3. Sheltered Badge [SHELTERED]
        sh_surf = font_badge.render("[SHELTERED]", True, (255, 190, 40))
        self.shelter_badge_surf = pygame.Surface((sh_surf.get_width() + 6, sh_surf.get_height() + 2))
        self.shelter_badge_surf.fill((25, 18, 10))
        pygame.draw.rect(self.shelter_badge_surf, (255, 190, 40), (0, 0, self.shelter_badge_surf.get_width(), self.shelter_badge_surf.get_height()), width=1)
        self.shelter_badge_surf.blit(sh_surf, (3, 1))

        # Proximity prompt
        prompt_font = FontManager.get(11, bold=True)
        p_surf = prompt_font.render("[E] TALK", True, (255, 220, 0))
        self.prompt_surf = pygame.Surface((p_surf.get_width() + 8, p_surf.get_height() + 2))
        self.prompt_surf.fill((20, 24, 34))
        pygame.draw.rect(self.prompt_surf, (255, 220, 0), (0, 0, self.prompt_surf.get_width(), self.prompt_surf.get_height()), width=1)
        self.prompt_surf.blit(p_surf, (4, 1))

    def trigger_flee(self, catastrophe_title: str) -> None:
        """Put NPC inside the habitat shelter at first during the storm and begin wandering randomly."""
        self.state = "SHELTERED"
        # Instantly put NPC inside the safe habitat shelter at first
        self.world_x = self.shelter_x + random.uniform(-30, 30)
        self.world_y = self.shelter_y + random.uniform(-25, 25)
        self.current_waypoints = []
        self.is_moving = False
        self.wander_timer = random.uniform(0.2, 1.0)
        self.shout_text = f"STORM LOCKDOWN! {catastrophe_title.upper()}!"
        self.shout_timer = 4.5

    def resolve_emergency(self) -> None:
        """Return to nominal duties once base health is 100%."""
        if self.state in ("FLEEING_INSIDE", "SHELTERED"):
            self.state = "RETURNING"
            # Reverse waypoints back to nominal post
            reversed_wp = list(reversed(self.corridor_waypoints))
            self.current_waypoints = reversed_wp + [(self.nominal_x, self.nominal_y)]
            self.is_moving = True
            self.shout_text = "Habitat restored! 100% Space Health! Returning to station."
            self.shout_timer = 3.5

    def get_current_dialogue(self) -> str:
        """Get dialogue and cycle to next line."""
        if self.state in ("FLEEING_INSIDE", "SHELTERED"):
            text = self.emergency_dialogues[self.emergency_dialogue_index % len(self.emergency_dialogues)]
            self.emergency_dialogue_index += 1
            return text
        text = self.dialogues[self.dialogue_index % len(self.dialogues)]
        self.dialogue_index += 1
        return text

    def update(self, dt: float, player_world_pos: pygame.Vector2) -> None:
        """Update animation, random wandering inside shelter, movement pathing, and active shout timers."""
        if self.shout_timer > 0:
            self.shout_timer -= dt
            if self.shout_timer <= 0:
                self.shout_text = None

        # 1. Random wandering inside habitat shelter during storm / emergency ("they should go randomly")
        if self.state == "SHELTERED":
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(2.5, 5.0)
                # Pick a random destination inside Central Rotunda & Airlock (930 - 1070, 770 - 890)
                rx = random.uniform(930.0, 1070.0)
                ry = random.uniform(770.0, 890.0)
                self.current_waypoints = [(rx, ry)]
                self.is_moving = True

        # 2. Navigation / Movement
        if self.is_moving and self.current_waypoints:
            target_x, target_y = self.current_waypoints[0]
            dx = target_x - self.world_x
            dy = target_y - self.world_y
            dist = math.hypot(dx, dy)

            speed = 85.0 if self.state == "SHELTERED" else (self.move_speed if self.state == "FLEEING_INSIDE" else 110.0)
            step = speed * dt

            if dist <= max(8.0, step):
                self.world_x = target_x
                self.world_y = target_y
                self.current_waypoints.pop(0)
                if not self.current_waypoints:
                    # Arrived at waypoint
                    self.is_moving = False
                    if self.state == "FLEEING_INSIDE":
                        self.state = "SHELTERED"
                    elif self.state == "RETURNING":
                        self.state = "NOMINAL"
            else:
                self.world_x += (dx / dist) * step
                self.world_y += (dy / dist) * step
                self.facing_right = (dx > 0)

        # 2. Facing direction when standing still
        if not self.is_moving:
            self.facing_right = (player_world_pos.x > self.world_x)

        # 3. Animation stepping
        self.anim_timer += dt
        if self.is_moving:
            if self.anim_timer >= 0.10:
                self.anim_timer = 0.0
                self.walk_frame_index = (self.walk_frame_index + 1) % len(self.walk_frames)
        else:
            if self.anim_timer >= 0.45:
                self.anim_timer = 0.0
                self.idle_frame_index = (self.idle_frame_index + 1) % len(self.idle_frames)

    def render(self, surface: pygame.Surface, camera: Any, is_near: bool = False) -> None:
        """Render NPC sprite, ground shadow, dynamic status badge, and speech bubble."""
        sp = camera.world_to_screen(self.world_x, self.world_y)
        # Viewport culling
        if not (-60 <= sp.x <= surface.get_width() + 60 and -60 <= sp.y <= surface.get_height() + 60):
            return

        cx, cy = int(sp.x), int(sp.y)

        # 1. Ground shadow (pre-baked)
        surface.blit(self.shadow_surf, (cx - 11, cy + 24))

        # 2. Main character frame (walk vs idle)
        if self.is_moving:
            frame = self.walk_frames[self.walk_frame_index]
        else:
            frame = self.idle_frames[self.idle_frame_index]

        if self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        frame_rect = frame.get_rect(center=(cx, cy))
        surface.blit(frame, frame_rect.topleft)

        # 3. 8-Bit Retro Status Badge
        if self.state == "FLEEING_INSIDE":
            badge = self.flee_badge_surf
        elif self.state == "SHELTERED":
            badge = self.shelter_badge_surf
        else:
            badge = self.badge_surf
        surface.blit(badge, (cx - badge.get_width() // 2, cy - 38))

        # 4. Proximity "[E] TALK" Prompt
        if is_near and not self.is_moving:
            surface.blit(self.prompt_surf, (cx - self.prompt_surf.get_width() // 2, cy - 54))

        # 5. Shouting Bubble if emergency panic active
        if self.shout_text and self.shout_timer > 0:
            font_shout = FontManager.get(10, bold=True)
            shout_surf = font_shout.render(self.shout_text, True, (255, 240, 200))
            bubble_w = shout_surf.get_width() + 10
            bubble_h = shout_surf.get_height() + 4
            bubble = pygame.Surface((bubble_w, bubble_h))
            bubble.fill((20, 10, 10) if self.state == "FLEEING_INSIDE" else (10, 25, 20))
            border_col = (255, 70, 70) if self.state == "FLEEING_INSIDE" else (0, 255, 180)
            pygame.draw.rect(bubble, border_col, (0, 0, bubble_w, bubble_h), width=1)
            bubble.blit(shout_surf, (5, 2))
            surface.blit(bubble, (cx - bubble_w // 2, cy - 62))


class NPCSystem:
    """Manages base crew NPCs, proximity dialogue, emergency evacuation, and rendering."""

    def __init__(self) -> None:
        self.all_npcs: List[CrewNPC] = [
            CrewNPC(
                npc_id="npc_suso",
                name="Commander Suso",
                role="Mission Commander",
                sprite_id=1,
                world_x=450 * WORLD_SCALE,
                world_y=410 * WORLD_SCALE,
                shelter_x=470 * WORLD_SCALE,
                shelter_y=390 * WORLD_SCALE,
                corridor_waypoints=[(460 * WORLD_SCALE, 400 * WORLD_SCALE)],
                dialogues=[
                    "Commander Suso here! Great to see you on station. All habitat telemetry and ECLSS reserves are green.",
                    "Keep the exterior solar arrays clear of ferric dust and monitor battery charge levels.",
                    "Proceed with your research and engineering operations. Jezero base is running smoothly.",
                    "Radio comms to mission control are open. Outstanding work keeping the expedition on track!",
                ],
                emergency_dialogues=[
                    "Commander Suso: CATASTROPHE LOCKDOWN! Space Health is critical! Recalibrate the grid challenges immediately!",
                    "Commander Suso: Prioritize oxygen and power grid stations to restore the habitat back to 100%!",
                ],
            ),
            CrewNPC(
                npc_id="npc_amal",
                name="Amal",
                role="Comms Specialist",
                sprite_id=3,
                world_x=340 * WORLD_SCALE,
                world_y=210 * WORLD_SCALE,
                shelter_x=530 * WORLD_SCALE,
                shelter_y=390 * WORLD_SCALE,
                corridor_waypoints=[(360 * WORLD_SCALE, 320 * WORLD_SCALE)],
                dialogues=[
                    "Commander Suso! Amal here at telemetry comms. Deep space relays to Earth are nominal and green!",
                    "Orbital downlink is tracking solar wind velocity. Let me know if you need satellite packet synchronization.",
                    "Radio bursts across Jezero are within background limits. All comms channels are listening for your transmission, Commander!",
                    "Keep that EVA suit transceiver powered. If an emergency arises, my relay channel is always open!",
                ],
                emergency_dialogues=[
                    "Amal: Telemetry sensors are off the charts! We're sheltering in the rotunda! Complete repairs to hit 100%!",
                    "Amal: Deep Space relays confirm external catastrophic event! Fix the damaged modules, Commander!",
                ],
            ),
            CrewNPC(
                npc_id="npc_gowri",
                name="Gowri",
                role="Research Fellow",
                sprite_id=2,
                world_x=280 * WORLD_SCALE,
                world_y=560 * WORLD_SCALE,
                shelter_x=470 * WORLD_SCALE,
                shelter_y=440 * WORLD_SCALE,
                corridor_waypoints=[(340 * WORLD_SCALE, 460 * WORLD_SCALE)],
                dialogues=[
                    "Commander Suso! Gowri reporting from the research lab. The extraterrestrial crop samples and spirulina cultures are thriving!",
                    "Atmospheric CO2 scrubbers and hydroponic beds are balancing ECLSS oxygen reserves nicely.",
                    "I'm analyzing ancient hydrated silica clay cores from the Jezero river delta. Fascinating microbial fossil markers!",
                    "If your EVA vitals drop or suit integrity takes a hit, visit the Medbay bio-scanner for regenerative biocell dressings!",
                ],
                emergency_dialogues=[
                    "Gowri: Greenhouse and bio-cultures are taking extreme stress! Redo the challenge stations to save the base!",
                    "Gowri: I ran inside as fast as I could! We need 100% Space Health before the life-support fails!",
                ],
            ),
            CrewNPC(
                npc_id="npc_christy",
                name="Christy",
                role="Chief Engineer",
                sprite_id=4,
                world_x=660 * WORLD_SCALE,
                world_y=560 * WORLD_SCALE,
                shelter_x=530 * WORLD_SCALE,
                shelter_y=440 * WORLD_SCALE,
                corridor_waypoints=[(580 * WORLD_SCALE, 460 * WORLD_SCALE)],
                dialogues=[
                    "Commander Suso! Christy on engineering duty. I've tuned the workshop 3D milling arm and checked the reactor bus.",
                    "Ferric basalt dust is always blowing across the solar arrays. Press [C] or use the wiper to keep power flowing!",
                    "Subsurface perchlorate drill motors are primed. Hit the grid challenge markers when you need regolith excavation cores.",
                    "The fission power grid is holding strong at 2.7 kW. Let me know if you need emergency circuits routed!",
                ],
                emergency_dialogues=[
                    "Christy: Multiple circuit breakers tripped in the workshop! Repair the stations to push Space Health back to 100%!",
                    "Christy: Structural shockwave hit the base! I'm holding down the central console—go seal those breaches!",
                ],
            ),
        ]
        self.active_player_id: int = 1
        # Default: Suso is playable character, so NPCs are Amal, Gowri, Christy
        self.npcs: List[CrewNPC] = [npc for npc in self.all_npcs if npc.sprite_id != 1]

        # Active dialogue overlay state
        self.active_dialogue: Optional[Dict[str, Any]] = None
        self.dialogue_timer: float = 0.0

    def trigger_emergency(self, catastrophe_title: str) -> None:
        """Order all active NPCs to shout and sprint inside to the central habitat shelter."""
        for npc in self.npcs:
            npc.trigger_flee(catastrophe_title)

    def resolve_emergency(self) -> None:
        """Signal all active NPCs that 100% space health is restored and they can return to post."""
        for npc in self.npcs:
            npc.resolve_emergency()

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

        # 2. Render dialogue popup if active (at right side down with NO additional background whatsoever)
        if self.active_dialogue:
            d = self.active_dialogue
            font_title = FontManager.get(12, bold=True)
            font_body = FontManager.get(11)
            font_hint = FontManager.get(10)

            pop_w = 420
            pop_x = surface.get_width() - pop_w - 20
            pop_y = surface.get_height() - 95

            # NO background box/fill whatsoever
            text_x = pop_x
            if d.get("avatar"):
                av = d["avatar"]
                surface.blit(av, (pop_x, pop_y))
                text_x = pop_x + 44

            # Header with shadow
            title_str = f">> {d['name'].upper()} // {d['role'].upper()}"
            t_shad = font_title.render(title_str, True, (0, 0, 0))
            t_surf = font_title.render(title_str, True, (255, 220, 0))
            surface.blit(t_shad, (text_x + 1, pop_y + 1))
            surface.blit(t_surf, (text_x, pop_y))

            # Dialogue text with shadow (wrap text if needed)
            body_str = f"\"{d['text']}\""
            if len(body_str) > 50:
                mid = body_str.rfind(" ", 0, 48)
                if mid == -1:
                    mid = 48
                line1 = body_str[:mid]
                line2 = body_str[mid:].strip()
                b1_shad = font_body.render(line1, True, (0, 0, 0))
                b1_surf = font_body.render(line1, True, (240, 245, 250))
                surface.blit(b1_shad, (text_x + 1, pop_y + 19))
                surface.blit(b1_surf, (text_x, pop_y + 18))

                b2_shad = font_body.render(line2, True, (0, 0, 0))
                b2_surf = font_body.render(line2, True, (240, 245, 250))
                surface.blit(b2_shad, (text_x + 1, pop_y + 35))
                surface.blit(b2_surf, (text_x, pop_y + 34))
                hint_y = pop_y + 52
            else:
                b_shad = font_body.render(body_str, True, (0, 0, 0))
                b_surf = font_body.render(body_str, True, (240, 245, 250))
                surface.blit(b_shad, (text_x + 1, pop_y + 20))
                surface.blit(b_surf, (text_x, pop_y + 19))
                hint_y = pop_y + 38

            # Hint
            h_shad = font_hint.render("[E] Next  |  [ESC] Close", True, (0, 0, 0))
            h_surf = font_hint.render("[E] Next  |  [ESC] Close", True, (130, 160, 190))
            surface.blit(h_shad, (text_x + 1, hint_y + 1))
            surface.blit(h_surf, (text_x, hint_y))
