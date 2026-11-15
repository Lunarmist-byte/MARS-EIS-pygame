"""DUSTFALL — 8-Bit Retro Heads-Up Display (HUD).

Clean, crisp 8-bit arcade telemetry interface with zero fluff:
- Collapsible info panels ([H] Toggle Full Telemetry / Minimal 8-Bit Mode)
- Default minimal 8-bit top/bottom HUD bars for 100% unobstructed screen view
- Commander Suso EVA operator badge
- Compact retro monospace key-value readout
- Base grid challenge progress tracking ([ ★ ] 15 stations)

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
from typing import Optional, Dict, Any, List, Tuple
import pygame
from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_NOMINAL,
    COLOR_WARNING,
    COLOR_CRITICAL,
    COLOR_INFO,
    COLOR_ACCENT_MARS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_HIGHLIGHT,
    CREDIT_INFO,
    CREW_MEMBERS,
)
from .components import UIComponents
from .event_panel import EventPanel
from .font_manager import FontManager
from world.world_state import WorldState
from world.player_state import PlayerState


class HUD:
    """Manages 8-bit retro collapsible telemetry interface."""

    def __init__(self) -> None:
        self.ui = UIComponents()
        self.event_panel = EventPanel(self.ui)
        self.is_collapsed: bool = True  # Default to minimal, clean 8-bit view

        self.avatars: Dict[int, pygame.Surface] = {}
        for cid in range(1, 5):
            av_path = f"assets/characters/avatar_{cid}.png"
            if os.path.exists(av_path):
                self.avatars[cid] = pygame.image.load(av_path).convert_alpha()

    def toggle_collapse(self) -> bool:
        """Toggle between minimal 8-bit mode and expanded telemetry."""
        self.is_collapsed = not self.is_collapsed
        return self.is_collapsed

    def render(
        self,
        surface: pygame.Surface,
        world_state: WorldState,
        player_state: PlayerState,
        backend_url: str,
        show_help: bool = False,
        show_debug: bool = False,
        show_live_feed: bool = False,
        nearby_facility: Optional[Dict[str, Any]] = None,
        active_crew_id: int = 1,
        mission_system: Optional[Any] = None,
        base_facilities: Optional[Dict[str, Any]] = None,
        collectibles: Optional[Any] = None,
        grid_challenges: Optional[Any] = None,
        nearby_npc: Optional[Any] = None,
        nearby_station: Optional[Any] = None,
    ) -> None:
        """Render 8-bit retro HUD overlays."""
        if self.is_collapsed:
            # -------------------------------------------------------------
            # MINIMAL 8-BIT COLLAPSED HUD (Zero Fluff, 100% Screen Clarity)
            # -------------------------------------------------------------
            self._render_minimal_top_bar(surface, world_state, player_state, grid_challenges, active_crew_id)
            self._render_minimal_bottom_bar(surface, player_state, nearby_facility, nearby_npc, nearby_station)
        else:
            # -------------------------------------------------------------
            # EXPANDED 8-BIT TELEMETRY PANELS
            # -------------------------------------------------------------
            self._render_top_bar(surface, world_state, backend_url, active_crew_id)
            self._render_environmental_panel(surface, world_state)
            self._render_infrastructure_panel(surface, world_state)
            self._render_mission_panel(surface, mission_system, nearby_facility, (player_state.x, player_state.y), base_facilities, world_state, collectibles, grid_challenges)
            self._render_events_panel(surface, world_state)
            self._render_player_panel(surface, player_state, world_state, backend_url, nearby_facility, active_crew_id)
            self._render_bottom_bar(surface)

        # Overlays
        if show_help:
            self._render_help_overlay(surface)
        if show_debug:
            self._render_debug_overlay(surface, world_state, player_state)
        if show_live_feed:
            self._render_live_feed_overlay(surface, world_state, backend_url)

    # -------------------------------------------------------------------------
    # MINIMAL 8-BIT RETRO INTERFACE
    # -------------------------------------------------------------------------
    def _render_minimal_top_bar(
        self,
        surface: pygame.Surface,
        world_state: WorldState,
        player_state: PlayerState,
        grid_challenges: Optional[Any] = None,
        active_crew_id: int = 1,
    ) -> None:
        """Render single compact 8-bit top telemetry ribbon."""
        bar_h = 28
        bar_rect = pygame.Rect(8, 8, WINDOW_WIDTH - 16, bar_h)

        # Sharp solid retro black panel with 1px cyan border
        pygame.draw.rect(surface, (8, 12, 18), bar_rect)
        pygame.draw.rect(surface, (0, 229, 255), bar_rect, width=1)

        font = FontManager.get(11, bold=True)

        # Telemetry chunks:
        # Dynamic active crew member name
        crew_info = CREW_MEMBERS.get(active_crew_id, CREW_MEMBERS[1])
        name_surf = font.render(f"[ {crew_info['name'].upper()} ]", True, (255, 215, 0))
        surface.blit(name_surf, (bar_rect.x + 8, bar_rect.y + 7))

        curr_x = bar_rect.x + name_surf.get_width() + 10

        # Location & EVA status badge
        if getattr(player_state, "is_outside", False):
            loc_label = f"[ ⚡ EVA: {player_state.location_name.upper()} ]"
            loc_col = (255, 140, 40)
        else:
            loc_label = f"[ {player_state.location_name.upper()} ]"
            loc_col = (0, 229, 255)
        loc_surf = font.render(loc_label, True, loc_col)
        surface.blit(loc_surf, (curr_x, bar_rect.y + 7))
        curr_x += loc_surf.get_width() + 10

        # [ HP: 100% ]
        hp_col = COLOR_NOMINAL if player_state.health > 40 else COLOR_CRITICAL
        hp_surf = font.render(f"[ HP: {player_state.health:.0f}% ]", True, hp_col)
        surface.blit(hp_surf, (curr_x, bar_rect.y + 7))
        curr_x += hp_surf.get_width() + 10

        # [ SPACE HEALTH: 100% ]
        sh_val = getattr(world_state, "station_health", 100.0)
        cd_val = getattr(world_state, "collapse_countdown", 90.0)
        cd_m = int(cd_val // 60)
        cd_s = int(cd_val % 60)
        cd_str = f"{cd_m:02d}:{cd_s:02d}"
        sh_col = COLOR_NOMINAL if sh_val >= 90 else (COLOR_WARNING if sh_val >= 50 else COLOR_CRITICAL)
        sh_label = f"[ SPACE: {sh_val:.0f}% ]" if sh_val >= 100 else f"[ ⚠ SPACE: {sh_val:.0f}% | DIE IN: {cd_str} ]"
        sh_surf = font.render(sh_label, True, sh_col)
        surface.blit(sh_surf, (curr_x, bar_rect.y + 7))
        curr_x += sh_surf.get_width() + 10

        # [ O2: 70kg ]
        o2_val = f"{world_state.oxygen_reserve:.1f}kg" if world_state.oxygen_reserve is not None else "N/A"
        o2_surf = font.render(f"[ O2: {o2_val} ]", True, (0, 255, 200))
        surface.blit(o2_surf, (curr_x, bar_rect.y + 7))
        curr_x += o2_surf.get_width() + 10

        # [ H2O: 75kg ]
        h2o_val = f"{world_state.water_reserve:.1f}kg" if world_state.water_reserve is not None else "N/A"
        h2o_surf = font.render(f"[ H2O: {h2o_val} ]", True, (80, 180, 255))
        surface.blit(h2o_surf, (curr_x, bar_rect.y + 7))
        curr_x += h2o_surf.get_width() + 10

        # [ BAT: 85% ]
        bat_val = f"{world_state.battery_soc:.0f}%" if world_state.battery_soc is not None else "N/A"
        bat_surf = font.render(f"[ BAT: {bat_val} ]", True, (255, 200, 50))
        surface.blit(bat_surf, (curr_x, bar_rect.y + 7))
        curr_x += bat_surf.get_width() + 10

        # [ SOL 000 12:00 ]
        sol_surf = font.render(f"[ SOL {world_state.sol:03d} {world_state.local_solar_time[:5]} ]", True, (240, 245, 250))
        surface.blit(sol_surf, (curr_x, bar_rect.y + 7))
        curr_x += sol_surf.get_width() + 10

        # Right side: Grid Challenges count & [H] Full HUD
        comp_count = grid_challenges.total_completed if grid_challenges else 0
        chall_str = f"[ ★ {comp_count}/20 CHALLENGES ]"
        chall_surf = font.render(chall_str, True, (0, 255, 120))
        surface.blit(chall_surf, (bar_rect.right - 240, bar_rect.y + 7))

        hud_toggle_surf = font.render("[ [H] EXPAND HUD ]", True, (150, 175, 200))
        surface.blit(hud_toggle_surf, (bar_rect.right - hud_toggle_surf.get_width() - 8, bar_rect.y + 7))

    def _render_minimal_bottom_bar(
        self,
        surface: pygame.Surface,
        player_state: PlayerState,
        nearby_facility: Optional[Dict[str, Any]] = None,
        nearby_npc: Optional[Any] = None,
        nearby_station: Optional[Any] = None,
    ) -> None:
        """Render single compact 8-bit bottom controls and interaction bar."""
        bar_h = 26
        bar_rect = pygame.Rect(8, WINDOW_HEIGHT - bar_h - 8, WINDOW_WIDTH - 16, bar_h)

        pygame.draw.rect(surface, (8, 12, 18), bar_rect)
        pygame.draw.rect(surface, (255, 179, 0), bar_rect, width=1)

        font = FontManager.get(10, bold=True)

        # Left: Controls shortcuts
        ctrl_str = "[WASD] Move  [Shift] Sprint  [Space] Low-G Hop  [E] Action  [C] Clean  [X] Drill  [T] Catastrophes  [H] Toggle HUD"
        ctrl_surf = font.render(ctrl_str, True, (180, 195, 210))
        surface.blit(ctrl_surf, (bar_rect.x + 8, bar_rect.y + 7))

        # Right: Dynamic Context Prompt
        prompt_text = ""
        prompt_color = (255, 220, 0)

        if nearby_npc:
            prompt_text = f">> PROXIMITY: [{nearby_npc.name.upper()}] — Press [E] to Talk!"
            prompt_color = (0, 255, 200)
        elif nearby_station:
            prompt_text = f">> PROXIMITY: [{nearby_station.name.upper()}] — Press [E] for Challenge!"
            prompt_color = (255, 215, 0)
        elif nearby_facility:
            fac_name = nearby_facility.get("name", "Facility")
            prompt_text = f">> FACILITY: [{fac_name.upper()}] — Press [E] to Calibrate!"
            prompt_color = (0, 255, 120)

        if prompt_text:
            p_surf = font.render(prompt_text, True, prompt_color)
            surface.blit(p_surf, (bar_rect.right - p_surf.get_width() - 8, bar_rect.y + 7))
        else:
            # Idle context hints: Airlock navigation directions or EVA action prompts
            if getattr(player_state, "is_outside", False):
                eva_hint = ">> EVA ACTIVE: [X] Drill Regolith  [C] Clean Solar  [Space] Low-G Hop  [Shift] Sprint"
                p_surf = font.render(eva_hint, True, (255, 140, 40))
            else:
                nav_hint = ">> AIRLOCKS: ◄ West Rover  ▲ North Dish  ► East Pad  ▼ South Surface"
                p_surf = font.render(nav_hint, True, (0, 229, 255))
            surface.blit(p_surf, (bar_rect.right - p_surf.get_width() - 8, bar_rect.y + 7))

    # -------------------------------------------------------------------------
    # EXPANDED TELEMETRY INTERFACE (Clean 8-Bit Architecture)
    # -------------------------------------------------------------------------
    def _render_top_bar(
        self,
        surface: pygame.Surface,
        world_state: WorldState,
        backend_url: str,
        active_crew_id: int = 1,
    ) -> None:
        """Render expanded top telemetry banner."""
        bar_rect = pygame.Rect(8, 8, WINDOW_WIDTH - 16, 32)
        pygame.draw.rect(surface, (8, 12, 18), bar_rect)
        pygame.draw.rect(surface, COLOR_ACCENT_MARS, bar_rect, width=1)

        font = FontManager.get(12, bold=True)
        crew_info = CREW_MEMBERS.get(active_crew_id, CREW_MEMBERS[1])
        t_surf = font.render(f"MARS-EIS // {world_state.site_name.upper()} BASE — {crew_info['name'].upper()}", True, COLOR_ACCENT_MARS)
        surface.blit(t_surf, (bar_rect.x + 10, bar_rect.y + 8))

        time_str = f"SOL {world_state.sol:03d} | {world_state.local_solar_time} MTC | Ls {world_state.solar_longitude_deg:.1f}°"
        time_surf = font.render(time_str, True, COLOR_TEXT_PRIMARY)
        surface.blit(time_surf, (bar_rect.centerx - time_surf.get_width() // 2, bar_rect.y + 8))

        # Collapse shortcut
        col_surf = font.render("[H: MINIMIZE HUD]", True, (0, 229, 255))
        surface.blit(col_surf, (bar_rect.right - col_surf.get_width() - 10, bar_rect.y + 8))

    def _render_environmental_panel(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render environmental sensors box (Top-Left)."""
        panel_rect = pygame.Rect(8, 46, 260, 175)
        pygame.draw.rect(surface, (8, 12, 18), panel_rect)
        pygame.draw.rect(surface, (45, 60, 85), panel_rect, width=1)

        font_hdr = FontManager.get(11, bold=True)
        font_txt = FontManager.get(11)

        hdr = font_hdr.render("ENVIRONMENTAL CONDITIONS", True, (0, 229, 255))
        surface.blit(hdr, (panel_rect.x + 8, panel_rect.y + 8))

        env = world_state.environment
        lines = [
            ("Atmospheric Temp:", env.format_air_temp()),
            ("Surface Temp:", env.format_surface_temp()),
            ("Surface Pressure:", env.format_pressure()),
            ("Wind Velocity:", env.format_wind()),
            ("Dust Opacity (Tau):", env.format_dust_opacity()),
            ("Radiation Dose Rate:", env.format_radiation()),
            ("Solar Irradiance:", env.format_solar()),
        ]

        curr_y = panel_rect.y + 28
        for k, v in lines:
            ks = font_txt.render(k, True, COLOR_TEXT_SECONDARY)
            vs = font_txt.render(v, True, COLOR_TEXT_PRIMARY)
            surface.blit(ks, (panel_rect.x + 8, curr_y))
            surface.blit(vs, (panel_rect.right - vs.get_width() - 8, curr_y))
            curr_y += 18

    def _render_infrastructure_panel(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render power and ECLSS stores box (Top-Right)."""
        panel_rect = pygame.Rect(WINDOW_WIDTH - 278, 46, 270, 175)
        pygame.draw.rect(surface, (8, 12, 18), panel_rect)
        pygame.draw.rect(surface, (45, 60, 85), panel_rect, width=1)

        font_hdr = FontManager.get(11, bold=True)
        font_txt = FontManager.get(11)

        hdr = font_hdr.render("BASE INFRASTRUCTURE", True, (0, 255, 120))
        surface.blit(hdr, (panel_rect.x + 8, panel_rect.y + 8))

        curr_y = panel_rect.y + 28
        lines = [
            ("Main Battery (SOC):", world_state.format_battery(), COLOR_NOMINAL if world_state.battery_soc else COLOR_TEXT_MUTED),
            ("Power (Gen/Load):", world_state.format_power(), COLOR_TEXT_PRIMARY),
            ("PV Arrays Eff:", world_state.format_solar_panels(), COLOR_TEXT_PRIMARY),
            ("Oxygen Reserve:", world_state.format_oxygen(), COLOR_NOMINAL if world_state.oxygen_reserve else COLOR_TEXT_MUTED),
            ("Water Reserve:", world_state.format_water(), COLOR_NOMINAL if world_state.water_reserve else COLOR_TEXT_MUTED),
            ("Food Rations:", world_state.format_food(), COLOR_NOMINAL if world_state.food_reserve else COLOR_TEXT_MUTED),
            ("Cabin ECLSS:", world_state.format_habitat_cabin(), COLOR_TEXT_PRIMARY),
        ]

        for k, v, col in lines:
            ks = font_txt.render(k, True, COLOR_TEXT_SECONDARY)
            vs = font_txt.render(v, True, col)
            surface.blit(ks, (panel_rect.x + 8, curr_y))
            surface.blit(vs, (panel_rect.right - vs.get_width() - 8, curr_y))
            curr_y += 18

    def _render_mission_panel(
        self,
        surface: pygame.Surface,
        mission_system: Optional[Any],
        nearby_facility: Optional[Dict[str, Any]],
        player_pos: Tuple[float, float],
        base_facilities: Optional[Dict[str, Any]],
        world_state: Optional[WorldState] = None,
        collectibles: Optional[Any] = None,
        grid_challenges: Optional[Any] = None,
    ) -> None:
        """Render active mission and grid challenge tracker."""
        panel_rect = pygame.Rect(WINDOW_WIDTH - 278, 228, 270, 140)
        pygame.draw.rect(surface, (8, 12, 18), panel_rect)
        pygame.draw.rect(surface, (0, 210, 160), panel_rect, width=1)

        font_hdr = FontManager.get(11, bold=True)
        font_txt = FontManager.get(11)

        hdr = font_hdr.render("GRID CHALLENGES", True, (0, 240, 180))
        surface.blit(hdr, (panel_rect.x + 8, panel_rect.y + 8))

        done = grid_challenges.total_completed if grid_challenges else (mission_system.total_completed if mission_system else 0)
        cnt = font_hdr.render(f"[{done}/20 DONE]", True, (255, 215, 0))
        surface.blit(cnt, (panel_rect.right - cnt.get_width() - 8, panel_rect.y + 8))

        curr_y = panel_rect.y + 30
        if mission_system:
            m = mission_system.current_mission
            surface.blit(font_txt.render(f"Target: {m.facility_name}", True, COLOR_TEXT_HIGHLIGHT), (panel_rect.x + 8, curr_y))
            curr_y += 16
            surface.blit(font_txt.render(f"Task: {m.title}", True, COLOR_TEXT_PRIMARY), (panel_rect.x + 8, curr_y))
            curr_y += 16
            surface.blit(font_txt.render(f"Reward: {m.reward_desc}", True, COLOR_NOMINAL), (panel_rect.x + 8, curr_y))
            curr_y += 20

        # Science points
        if collectibles:
            sci = font_txt.render(f"Artifacts: {collectibles.total_collected}/6 ({collectibles.total_science_score} pts)", True, (240, 180, 80))
            surface.blit(sci, (panel_rect.x + 8, curr_y))

    def _render_events_panel(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render active hazards panel (Bottom-Left)."""
        panel_rect = pygame.Rect(8, WINDOW_HEIGHT - 130, 320, 85)
        pygame.draw.rect(surface, (8, 12, 18), panel_rect)
        pygame.draw.rect(surface, (45, 60, 85), panel_rect, width=1)

        font_hdr = FontManager.get(11, bold=True)
        font_txt = FontManager.get(10)

        hdr = font_hdr.render("ACTIVE HAZARDS", True, COLOR_TEXT_PRIMARY)
        surface.blit(hdr, (panel_rect.x + 8, panel_rect.y + 8))

        cats = world_state.catastrophes
        curr_y = panel_rect.y + 24
        sh_val = getattr(world_state, "station_health", 100.0)
        cd_val = getattr(world_state, "collapse_countdown", 60.0)

        if cats or sh_val < 100.0:
            if cats:
                for c in cats[:1]:
                    c_name = c.get("name", c.get("type", "Catastrophe"))
                    s = font_txt.render(f"ALERT: {c_name}", True, COLOR_CRITICAL)
                    surface.blit(s, (panel_rect.x + 8, curr_y))
                    curr_y += 14
            else:
                s = font_txt.render("ALERT: BASE DAMAGE DETECTED", True, COLOR_WARNING)
                surface.blit(s, (panel_rect.x + 8, curr_y))
                curr_y += 14

            cd_m = int(cd_val // 60)
            cd_s = int(cd_val % 60)
            cd_str = f"{cd_m:02d}:{cd_s:02d}"
            cd_col = (255, 60, 60) if cd_val < 25 else (255, 180, 40)
            cd_txt = font_txt.render(f"COLLAPSE TIMEOUT: {cd_str} [REPAIR NOW]", True, cd_col)
            surface.blit(cd_txt, (panel_rect.x + 8, curr_y))
            curr_y += 13

            # Mini health bar
            bar_w = 160
            bar_h = 5
            fill_w = int(bar_w * (sh_val / 100.0))
            pygame.draw.rect(surface, (30, 40, 50), (panel_rect.x + 8, curr_y + 2, bar_w, bar_h))
            sh_col = COLOR_WARNING if sh_val >= 50 else COLOR_CRITICAL
            pygame.draw.rect(surface, sh_col, (panel_rect.x + 8, curr_y + 2, fill_w, bar_h))
        else:
            nom = font_txt.render("NOMINAL // No active hazards or storm alerts.", True, COLOR_NOMINAL)
            surface.blit(nom, (panel_rect.x + 8, curr_y))
            curr_y += 16
            sh_txt = font_txt.render(f"Space Health: {sh_val:.0f}% [HABITAT SECURE]", True, COLOR_NOMINAL)
            surface.blit(sh_txt, (panel_rect.x + 8, curr_y))

    def _render_player_panel(
        self,
        surface: pygame.Surface,
        player_state: PlayerState,
        world_state: WorldState,
        backend_url: str = "",
        nearby_facility: Optional[Dict[str, Any]] = None,
        active_crew_id: int = 1,
    ) -> None:
        """Render Commander Suso player status box (Bottom-Center)."""
        panel_rect = pygame.Rect(336, WINDOW_HEIGHT - 130, WINDOW_WIDTH - 344, 85)
        pygame.draw.rect(surface, (8, 12, 18), panel_rect)
        pygame.draw.rect(surface, (45, 60, 85), panel_rect, width=1)

        font_hdr = FontManager.get(11, bold=True)
        font_txt = FontManager.get(10)

        # Avatar (Commander Suso is Sprite 1, main player)
        av_img = self.avatars.get(active_crew_id, self.avatars.get(1, self.avatars.get(3)))
        if av_img:
            surface.blit(av_img, (panel_rect.x + 8, panel_rect.y + 8))
            pygame.draw.rect(surface, (0, 229, 255), (panel_rect.x + 7, panel_rect.y + 7, 38, 38), width=1)
            text_x = panel_rect.x + 52
        else:
            text_x = panel_rect.x + 8

        crew_info = CREW_MEMBERS.get(active_crew_id, CREW_MEMBERS[1])
        hdr = font_hdr.render(f"{crew_info['name'].upper()} // {crew_info['role'].upper()}", True, (255, 215, 0))
        surface.blit(hdr, (text_x, panel_rect.y + 8))

        is_out = getattr(player_state, "is_outside", False)
        loc_txt = f"Zone: {getattr(player_state, 'location_name', 'Hab')} [{'EXTERIOR EVA' if is_out else 'INTERIOR'}]"
        hp_txt = font_txt.render(f"Suit Health: {player_state.health:.0f}%  |  {loc_txt}  |  Act: {player_state.current_action}", True, COLOR_NOMINAL)
        surface.blit(hp_txt, (text_x, panel_rect.y + 26))

        fb_msg = player_state.last_action_message or "Systems Operational // Nominal Telemetry"
        fb_surf = font_txt.render(f">> {fb_msg}", True, COLOR_TEXT_SECONDARY)
        surface.blit(fb_surf, (text_x, panel_rect.y + 44))

    def _render_bottom_bar(self, surface: pygame.Surface) -> None:
        """Render expanded controls shortcut bar."""
        bar_rect = pygame.Rect(8, WINDOW_HEIGHT - 36, WINDOW_WIDTH - 16, 28)
        pygame.draw.rect(surface, (8, 12, 18), bar_rect)
        pygame.draw.rect(surface, (45, 60, 85), bar_rect, width=1)

        font = FontManager.get(10, bold=True)
        ctrl_str = "[WASD] Move  [Shift] Sprint  [Space] Low-G Hop  [E] Interact  [C] Clean  [X] Drill  [T] Catastrophes  [H] Collapse HUD"
        surface.blit(font.render(ctrl_str, True, (160, 180, 200)), (bar_rect.x + 8, bar_rect.y + 8))

    def _render_help_overlay(self, surface: pygame.Surface) -> None:
        """Render retro help dialog."""
        rect = pygame.Rect(WINDOW_WIDTH // 2 - 280, WINDOW_HEIGHT // 2 - 180, 560, 360)
        pygame.draw.rect(surface, (8, 12, 18), rect)
        pygame.draw.rect(surface, (0, 229, 255), rect, width=2)

        font_large = FontManager.get(14, bold=True)
        font_small = FontManager.get(11)

        surface.blit(font_large.render("DUSTFALL // SYSTEM MANUAL & SHORTCUTS", True, (0, 229, 255)), (rect.x + 16, rect.y + 14))

        shortcuts = [
            ("WASD / Arrows", "8-Directional Normalized Astronaut Movement"),
            ("Shift (Hold)", "EVA Cold-Gas Thruster Sprint Boost (1.45x)"),
            ("Space", "Low-Gravity Martian Hop (0.38g float arc)"),
            ("E", "Interact / Launch Facility Challenge Minigame / Talk to NPCs"),
            ("C", "Electrostatic Photovoltaic Wiper Clean"),
            ("X", "Subsurface Regolith Core Excavation"),
            ("1 / 2 / 3 / 4", "Swap Astronaut (Suso, Gowri, Amal, Christy)"),
            ("Tab", "Cycle Active Crew Operator"),
            ("H", "Collapse / Expand 8-Bit Minimal HUD Telemetry"),
            ("T / F4", "MARS-EIS Situation Injector (Scenarios & Catastrophes)"),
            ("F5", "Toggle Real-Time WebSocket Live Feed Monitor"),
            ("ESC", "Close Overlays / Abort Active Minigame Challenge"),
        ]

        curr_y = rect.y + 42
        for k, d in shortcuts:
            ks = font_small.render(f"[{k}]", True, (255, 215, 0))
            ds = font_small.render(f"— {d}", True, COLOR_TEXT_PRIMARY)
            surface.blit(ks, (rect.x + 16, curr_y))
            surface.blit(ds, (rect.x + 150, curr_y))
            curr_y += 22

        surface.blit(font_small.render("Press [F1] or [ESC] to return to simulation.", True, (0, 229, 255)), (rect.x + 16, rect.bottom - 26))

    def _render_debug_overlay(self, surface: pygame.Surface, world_state: WorldState, player_state: PlayerState) -> None:
        pass

    def _render_live_feed_overlay(self, surface: pygame.Surface, world_state: WorldState, backend_url: str) -> None:
        pass
