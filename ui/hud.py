"""MARS SURVIVAL — Heads-Up Display (HUD).

Renders telemetry, Martian environmental conditions, habitat infrastructure,
player telemetry, action status, and author credits.
Maintains screen-space positioning independent of camera movement.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
from typing import Optional, Dict, Any, List
import pygame
from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_NOMINAL,
    COLOR_WARNING,
    COLOR_CRITICAL,
    COLOR_INFO,
    COLOR_ACCENT_MARS,
    COLOR_PANEL_BORDER_ACCENT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_HIGHLIGHT,
    CREDIT_INFO,
    CREW_MEMBERS,
)
from .components import UIComponents
from .event_panel import EventPanel
from world.world_state import WorldState
from world.player_state import PlayerState


class HUD:
    """Manages full screen-space telemetry interface."""

    def __init__(self) -> None:
        self.ui = UIComponents()
        self.event_panel = EventPanel(self.ui)
        self.avatars: Dict[int, pygame.Surface] = {}
        for cid in range(1, 5):
            av_path = f"assets/characters/avatar_{cid}.png"
            if os.path.exists(av_path):
                self.avatars[cid] = pygame.image.load(av_path).convert_alpha()

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
        nearby_door: Optional[Any] = None,
        active_crew_id: int = 1,
        mission_system: Optional[Any] = None,
        base_facilities: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Render all HUD overlays to target screen surface."""
        # 1. Top Status Bar
        self._render_top_bar(surface, world_state, backend_url)

        # 2. Environmental Readings Panel (Top-Left)
        self._render_environmental_panel(surface, world_state)

        # 3. Infrastructure & Life Support Panel (Top-Right)
        self._render_infrastructure_panel(surface, world_state)

        # 4. Active Missions Panel (Right side below Infrastructure)
        self._render_mission_panel(surface, mission_system, nearby_facility, (player_state.x, player_state.y), base_facilities)

        # 5. Active Events & Hazards Panel (Bottom-Left)
        self._render_events_panel(surface, world_state)

        # 6. Player Status & Action Feedback (Bottom-Center / Bottom-Left)
        self._render_player_panel(surface, player_state, world_state, backend_url, nearby_facility, nearby_door, active_crew_id)

        # 7. Bottom Controls Bar & Author Credit
        self._render_bottom_bar(surface)

        # 8. Optional Overlays (Help dialog, Debug overlay, Live Feed Monitor)
        if show_help:
            self._render_help_overlay(surface)
        if show_debug:
            self._render_debug_overlay(surface, world_state, player_state)
        if show_live_feed:
            self._render_live_feed_overlay(surface, world_state, backend_url)

    def _render_top_bar(self, surface: pygame.Surface, world_state: WorldState, backend_url: str) -> None:
        """Render top telemetry banner with Sol clock and backend connection status."""
        bar_rect = pygame.Rect(10, 10, WINDOW_WIDTH - 20, 36)
        self.ui.draw_panel(surface, bar_rect)

        # Base site & Mission title
        title_str = f"MARS-EIS // {world_state.site_name.upper()} BASE"
        title_surf = self.ui.font_medium.render(title_str, True, COLOR_ACCENT_MARS)
        surface.blit(title_surf, (bar_rect.x + 14, bar_rect.y + 10))

        # Sol and Martian Local Time
        time_str = f"SOL {world_state.sol:03d} | {world_state.local_solar_time} MTC | Ls {world_state.solar_longitude_deg:.1f}°"
        time_surf = self.ui.font_medium.render(time_str, True, COLOR_TEXT_PRIMARY)
        surface.blit(time_surf, (bar_rect.centerx - time_surf.get_width() // 2, bar_rect.y + 10))

        # Emergency Level Indicator if elevated
        if world_state.emergency_level in ("WARNING", "CRITICAL"):
            alert_color = COLOR_CRITICAL if world_state.emergency_level == "CRITICAL" else COLOR_WARNING
            alert_surf = self.ui.font_small.render(f"[{world_state.emergency_level} HAZARD]", True, alert_color)
            surface.blit(alert_surf, (bar_rect.centerx + time_surf.get_width() // 2 + 15, bar_rect.y + 11))

        # Connection status badge
        status = world_state.simulation_status
        if world_state.is_live_feed:
            badge_color = COLOR_NOMINAL
            status_text = f"LIVE FEED {world_state.live_feed_rate_hz:.1f} Hz"
            badge_width = 150
        elif status == "REST FALLBACK":
            badge_color = COLOR_WARNING
            status_text = "REST FALLBACK"
            badge_width = 135
        elif status == "CONNECTED":
            badge_color = COLOR_NOMINAL
            status_text = "SIM ONLINE"
            badge_width = 120
        elif status == "CONNECTING":
            badge_color = COLOR_INFO
            status_text = "CONNECTING..."
            badge_width = 125
        elif status == "SYNCING":
            badge_color = COLOR_WARNING
            status_text = "SYNCING"
            badge_width = 110
        else:
            badge_color = COLOR_CRITICAL
            status_text = "DISCONNECTED"
            badge_width = 130

        badge_x = bar_rect.right - badge_width - 10
        self.ui.draw_badge(surface, status_text, badge_x, bar_rect.y + 9, badge_color, (0, 0, 0), self.ui.font_small)

        # If live feed is streaming, draw a bright pulsating beacon circle
        if world_state.is_live_feed:
            pulse = int((pygame.time.get_ticks() / 300) % 2)
            dot_color = (0, 255, 120) if pulse else (0, 180, 80)
            pygame.draw.circle(surface, dot_color, (badge_x - 12, bar_rect.y + 18), 4)

        # Backend URL label
        clean_url = backend_url.replace("http://", "").replace("https://", "").replace("ws://", "")
        url_surf = self.ui.font_tiny.render(clean_url, True, COLOR_TEXT_MUTED)
        surface.blit(url_surf, (badge_x - url_surf.get_width() - 25, bar_rect.y + 12))

    def _render_environmental_panel(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render authoritative environmental measurements from MARS-EIS."""
        env = world_state.environment
        panel_rect = pygame.Rect(10, 52, 280, 210)
        self.ui.draw_panel(surface, panel_rect)

        # Header
        hdr = self.ui.font_medium.render("ENVIRONMENTAL CONDITIONS", True, COLOR_TEXT_PRIMARY)
        surface.blit(hdr, (panel_rect.x + 12, panel_rect.y + 10))

        curr_y = panel_rect.y + 34
        w = panel_rect.width - 24

        curr_y += self.ui.draw_key_value(surface, "Atmospheric Temp:", env.format_air_temp(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Surface Temp:", env.format_surface_temp(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Surface Pressure:", env.format_pressure(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Wind Velocity:", env.format_wind(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Dust Opacity (Tau):", env.format_dust_opacity(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Radiation Dose Rate:", env.format_radiation(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Solar Irradiance:", env.format_solar(), panel_rect.x + 12, curr_y, w)

        # Subtitle note if backend disconnected
        if world_state.is_live_feed:
            note = self.ui.font_tiny.render("● 1.0 Hz Live Feed Streaming", True, COLOR_NOMINAL)
            surface.blit(note, (panel_rect.x + 12, panel_rect.bottom - 18))
        elif world_state.simulation_status != "CONNECTED":
            note = self.ui.font_tiny.render("State preserved from last sync", True, COLOR_WARNING)
            surface.blit(note, (panel_rect.x + 12, panel_rect.bottom - 18))

    def _render_infrastructure_panel(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render authoritative habitat and energy systems telemetry from MARS-EIS."""
        panel_rect = pygame.Rect(WINDOW_WIDTH - 290, 52, 280, 260)
        self.ui.draw_panel(surface, panel_rect)

        # Header
        hdr = self.ui.font_medium.render("BASE INFRASTRUCTURE", True, COLOR_TEXT_PRIMARY)
        surface.blit(hdr, (panel_rect.x + 12, panel_rect.y + 10))

        curr_y = panel_rect.y + 34
        w = panel_rect.width - 24

        # Battery Bar
        soc = world_state.battery_soc
        soc_val = soc if soc is not None else 0.0
        soc_color = COLOR_NOMINAL if soc_val > 50.0 else (COLOR_WARNING if soc_val > 25.0 else COLOR_CRITICAL)
        
        self.ui.draw_key_value(surface, "Main Storage Battery:", world_state.format_battery(), panel_rect.x + 12, curr_y, w)
        curr_y += 18
        self.ui.draw_progress_bar(surface, pygame.Rect(panel_rect.x + 12, curr_y, w, 8), soc_val / 100.0, soc_color)
        curr_y += 14

        curr_y += self.ui.draw_key_value(surface, "Power (Gen / Load):", world_state.format_power(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Photovoltaic Arrays:", world_state.format_solar_panels(), panel_rect.x + 12, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Hab Cabin ECLSS:", world_state.format_habitat_cabin(), panel_rect.x + 12, curr_y, w)

        # Separator line
        pygame.draw.line(surface, (45, 55, 75), (panel_rect.x + 12, curr_y + 4), (panel_rect.right - 12, curr_y + 4))
        curr_y += 10

        # Consumables (explicitly marked as unsimulated / N/A when not in backend)
        lbl_cons = self.ui.font_tiny.render("CONSUMABLES & STORES (ECLSS)", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_cons, (panel_rect.x + 12, curr_y))
        curr_y += 14

        o2_col = COLOR_NOMINAL if world_state.oxygen_reserve is not None else COLOR_TEXT_MUTED
        w_col = COLOR_NOMINAL if world_state.water_reserve is not None else COLOR_TEXT_MUTED
        f_col = COLOR_NOMINAL if world_state.food_reserve is not None else COLOR_TEXT_MUTED
        curr_y += self.ui.draw_key_value(surface, "Oxygen Reserve:", world_state.format_oxygen(), panel_rect.x + 12, curr_y, w, value_color=o2_col)
        curr_y += self.ui.draw_key_value(surface, "Water Reserve:", world_state.format_water(), panel_rect.x + 12, curr_y, w, value_color=w_col)
        curr_y += self.ui.draw_key_value(surface, "Food Rations:", world_state.format_food(), panel_rect.x + 12, curr_y, w, value_color=f_col)

    def _render_mission_panel(
        self,
        surface: pygame.Surface,
        mission_system: Optional[Any],
        nearby_facility: Optional[Dict[str, Any]],
        player_pos: Tuple[float, float],
        base_facilities: Optional[Dict[str, Any]],
    ) -> None:
        """Render active survival mission tracker and stat boost incentives."""
        if not mission_system:
            return

        panel_rect = pygame.Rect(WINDOW_WIDTH - 290, 318, 280, 136)
        self.ui.draw_panel(surface, panel_rect, border_color=(0, 210, 160))

        # Header with pulse
        hdr_surf = self.ui.font_small.render("ACTIVE SURVIVAL MISSION", True, (0, 240, 180))
        surface.blit(hdr_surf, (panel_rect.x + 10, panel_rect.y + 8))

        # Counter badge
        comp_str = f"{mission_system.total_completed} Done"
        comp_surf = self.ui.font_tiny.render(comp_str, True, COLOR_TEXT_MUTED)
        surface.blit(comp_surf, (panel_rect.right - comp_surf.get_width() - 10, panel_rect.y + 10))

        m = mission_system.current_mission
        curr_y = panel_rect.y + 28

        # Target Facility
        target_name = m.facility_name.upper()
        t_surf = self.ui.font_small.render(f"Target: {target_name}", True, COLOR_TEXT_HIGHLIGHT)
        surface.blit(t_surf, (panel_rect.x + 10, curr_y))
        curr_y += 18

        # Title / Task
        task_surf = self.ui.font_tiny.render(f"Task: {m.title}", True, COLOR_TEXT_PRIMARY)
        surface.blit(task_surf, (panel_rect.x + 10, curr_y))
        curr_y += 16

        # Stat Reward
        rew_surf = self.ui.font_tiny.render(f"Reward: {m.reward_desc}", True, COLOR_NOMINAL)
        surface.blit(rew_surf, (panel_rect.x + 10, curr_y))
        curr_y += 18

        # Proximity Prompt or Distance
        is_at_facility = nearby_facility and nearby_facility.get("facility_id") == m.facility_id
        if is_at_facility:
            p_text = "● IN FACILITY — Press [E] to Complete!"
            p_color = (0, 255, 120)
        else:
            dist_m = mission_system.get_distance_to_current(player_pos, base_facilities or {})
            p_text = f">> Range: {dist_m:.1f}m | Proceed to Room"
            p_color = COLOR_INFO

        p_surf = self.ui.font_small.render(p_text, True, p_color)
        surface.blit(p_surf, (panel_rect.x + 10, curr_y))

    def _render_events_panel(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render active hazards and emergent events panel."""
        rect = pygame.Rect(10, WINDOW_HEIGHT - 170, 380, 115)
        self.event_panel.render(surface, rect, world_state)

    def _render_player_panel(
        self,
        surface: pygame.Surface,
        player_state: PlayerState,
        world_state: WorldState,
        backend_url: str = "",
        nearby_facility: Optional[Dict[str, Any]] = None,
        nearby_door: Optional[Any] = None,
        active_crew_id: int = 1,
    ) -> None:
        """Render astronaut health, action state, avatar, and contextual interaction prompts."""
        panel_rect = pygame.Rect(400, WINDOW_HEIGHT - 170, WINDOW_WIDTH - 410, 115)
        self.ui.draw_panel(surface, panel_rect)

        # Avatar portrait
        av_x = panel_rect.x + 12
        av_y = panel_rect.y + 12
        if active_crew_id in self.avatars:
            surface.blit(self.avatars[active_crew_id], (av_x, av_y))
            pygame.draw.rect(surface, COLOR_PANEL_BORDER_ACCENT, (av_x - 1, av_y - 1, 38, 38), width=1, border_radius=3)
        else:
            pygame.draw.rect(surface, (45, 55, 75), (av_x, av_y, 36, 36), border_radius=3)

        crew_info = CREW_MEMBERS.get(active_crew_id, {"name": f"Astronaut #{active_crew_id}", "role": "EVA Operator"})
        hdr_text = f"{crew_info['name'].upper()} // {crew_info['role']}"
        hdr = self.ui.font_medium.render(hdr_text, True, COLOR_TEXT_PRIMARY)
        surface.blit(hdr, (av_x + 46, panel_rect.y + 10))

        # Health bar
        hp_rect = pygame.Rect(av_x + 46, panel_rect.y + 30, 150, 8)
        self.ui.draw_progress_bar(surface, hp_rect, player_state.health / 100.0, COLOR_NOMINAL)
        hp_lbl = self.ui.font_tiny.render(f"Suit Health: {player_state.health:.0f}%", True, COLOR_TEXT_SECONDARY)
        surface.blit(hp_lbl, (hp_rect.right + 10, panel_rect.y + 27))

        # Position metrics
        coords_m = player_state.get_planetary_coords_m()
        pos_str = f"Grid: X: {coords_m[0]:.1f}m | Y: {coords_m[1]:.1f}m | Action: {player_state.current_action} (Facing: {player_state.facing_direction.upper()})"
        pos_surf = self.ui.font_tiny.render(pos_str, True, COLOR_TEXT_MUTED)
        surface.blit(pos_surf, (panel_rect.x + 14, panel_rect.y + 53))

        # Action feedback / Backend response banner
        is_online = world_state.is_live_feed or world_state.simulation_status in ("CONNECTED", "SYNCING", "REST FALLBACK")
        if not is_online:
            fb_msg = f"SIM OFFLINE: MARS-EIS not reached on {backend_url} | Run 'python launch.py' | [F2] Retry"
            fb_color = COLOR_WARNING
        else:
            if player_state.last_action_message and not player_state.last_action_message.startswith("SIM OFFLINE"):
                fb_msg = player_state.last_action_message
            elif world_state.is_live_feed:
                fb_msg = f"LIVE FEED ACTIVE ({world_state.live_feed_rate_hz:.1f} Hz) // All Habitat Modules Operational"
            else:
                fb_msg = "Base Telemetry Online // Authoritative Telemetry Synchronized"
            fb_color = COLOR_NOMINAL if player_state.last_action_success else COLOR_CRITICAL
        fb_surf = self.ui.font_small.render(f">> {fb_msg}", True, fb_color)
        surface.blit(fb_surf, (panel_rect.x + 14, panel_rect.y + 70))

        # Contextual proximity prompt (if astronaut is near a base facility or blast door)
        if nearby_facility:
            fac_name = nearby_facility.get("name", "Facility")
            fac_act = nearby_facility.get("interaction_action", "INTERACT")
            prompt_str = f"NEARBY: {fac_name.upper()} — Press [E] to engage {fac_act}"
            prompt_surf = self.ui.font_small.render(prompt_str, True, COLOR_TEXT_HIGHLIGHT)
            surface.blit(prompt_surf, (panel_rect.x + 14, panel_rect.y + 90))
        elif nearby_door:
            d_name = getattr(nearby_door, "name", "Blast Door").upper()
            d_state = getattr(nearby_door, "state", "CLOSED")
            pct = int(getattr(nearby_door, "open_ratio", 0.0) * 100)
            if getattr(nearby_door, "is_blocking", lambda: False)():
                d_col = COLOR_WARNING
                prompt_str = f"DOOR SENSOR: {d_name} — {d_state} ({pct}%)"
            else:
                d_col = COLOR_NOMINAL
                prompt_str = f"DOOR SENSOR: {d_name} — ACCESS GRANTED ({d_state})"
            prompt_surf = self.ui.font_small.render(prompt_str, True, d_col)
            surface.blit(prompt_surf, (panel_rect.x + 14, panel_rect.y + 90))

    def _render_bottom_bar(self, surface: pygame.Surface) -> None:
        """Render controls shortcut bar."""
        bar_rect = pygame.Rect(10, WINDOW_HEIGHT - 45, WINDOW_WIDTH - 20, 35)
        self.ui.draw_panel(surface, bar_rect)

        # Controls shortcuts across bottom bar
        ctrl_str = "[WASD / Arrows] Move  |  [E] Engage Facility  |  [C] Clean Panels  |  [X] Drill Regolith  |  [T / F4] Situations  |  [F5] Live Feed  |  [1-4 / Tab] Crew  |  [Space] +10s  |  [F1] Help"
        ctrl_surf = self.ui.font_small.render(ctrl_str, True, COLOR_TEXT_SECONDARY)
        surface.blit(ctrl_surf, (bar_rect.x + 14, bar_rect.y + 9))

    def _render_help_overlay(self, surface: pygame.Surface) -> None:
        """Render help & system documentation dialog."""
        modal_rect = pygame.Rect(WINDOW_WIDTH // 2 - 320, WINDOW_HEIGHT // 2 - 200, 640, 400)
        self.ui.draw_panel(surface, modal_rect, bg_color=(15, 18, 25, 245), border_color=COLOR_ACCENT_MARS, border_width=2)

        hdr = self.ui.font_large.render("MARS SURVIVAL // SYSTEM MANUAL & CONTROLS", True, COLOR_ACCENT_MARS)
        surface.blit(hdr, (modal_rect.x + 24, modal_rect.y + 20))

        lines = [
            "ARCHITECTURE:",
            "  - Presentation Client: Pygame 2.x top-down 2D Mars base engine.",
            "  - Authoritative Backend: MARS-EIS independent physics simulation.",
            "  - WebSocket Live Feed: ws://127.0.0.1:8000/ws/telemetry (1.0 Hz).",
            "",
            "CONTROLS & SHORTCUTS:",
            "  - W / A / S / D or Arrow Keys : Smooth normalized astronaut movement.",
            "  - 1 / 2 / 3 / 4 or Tab Key : Switch active astronaut crew member.",
            "  - E key : Engage habitat module or inspect closest facility landmark.",
            "  - C key : Dispatch solar panel dust clearing action to MARS-EIS.",
            "  - X key : Execute subsurface regolith core drilling / excavation.",
            "  - Spacebar : Request immediate +10s simulation advance step.",
            "  - T / F4 key : Open MARS-EIS Situation Injector (Scenarios & Catastrophes).",
            "  - F5 key : Toggle Real-Time WebSocket Live Feed Monitor overlay.",
            "  - F1 key : Toggle this system manual overlay.",
            "  - F2 key : Force immediate backend API reconnect handshake.",
            "  - F3 key : Toggle debug camera coordinates and performance statistics.",
            "",
            "Press [F1] or [ESC] to close."
        ]

        curr_y = modal_rect.y + 55
        for line in lines:
            color = COLOR_TEXT_HIGHLIGHT if line.endswith(":") else COLOR_TEXT_PRIMARY
            surf = self.ui.font_small.render(line, True, color)
            surface.blit(surf, (modal_rect.x + 24, curr_y))
            curr_y += 18

    def _render_debug_overlay(self, surface: pygame.Surface, world_state: WorldState, player_state: PlayerState) -> None:
        """Render debug coordinates and state versions overlay."""
        dbg_rect = pygame.Rect(10, 270, 280, 110)
        self.ui.draw_panel(surface, dbg_rect)

        hdr = self.ui.font_small.render("DEBUG TELEMETRY [F3]", True, COLOR_TEXT_HIGHLIGHT)
        surface.blit(hdr, (dbg_rect.x + 10, dbg_rect.y + 8))

        w = dbg_rect.width - 20
        y = dbg_rect.y + 28
        y += self.ui.draw_key_value(surface, "World Coordinates:", f"{player_state.x:.0f}, {player_state.y:.0f} px", dbg_rect.x + 10, y, w)
        y += self.ui.draw_key_value(surface, "State Version:", str(world_state.state_version), dbg_rect.x + 10, y, w)
        y += self.ui.draw_key_value(surface, "Sync Timestamp:", f"{world_state.last_sync_timestamp:.2f}", dbg_rect.x + 10, y, w)
        y += self.ui.draw_key_value(surface, "Elapsed Sim Secs:", f"{world_state.elapsed_seconds:.1f}s", dbg_rect.x + 10, y, w)

    def _render_live_feed_overlay(self, surface: pygame.Surface, world_state: WorldState, backend_url: str) -> None:
        """Render dedicated real-time WebSocket live feed inspector overlay."""
        modal_rect = pygame.Rect(WINDOW_WIDTH // 2 - 320, WINDOW_HEIGHT // 2 - 210, 640, 420)
        self.ui.draw_panel(surface, modal_rect, bg_color=(14, 18, 26, 245), border_color=(0, 200, 150), border_width=2)

        # Header with live pulse icon
        hdr = self.ui.font_large.render("MARS-EIS // REAL-TIME WEBSOCKET LIVE FEED MONITOR", True, (0, 255, 180))
        surface.blit(hdr, (modal_rect.x + 20, modal_rect.y + 16))

        # Status indicator
        curr_y = modal_rect.y + 50
        w = modal_rect.width - 40
        feed_status = "STREAMING ACTIVE" if world_state.is_live_feed else "DISCONNECTED / REST FALLBACK"
        feed_col = COLOR_NOMINAL if world_state.is_live_feed else COLOR_WARNING

        curr_y += self.ui.draw_key_value(surface, "Live Telemetry Status:", feed_status, modal_rect.x + 20, curr_y, w, value_color=feed_col)
        curr_y += self.ui.draw_key_value(surface, "Live WebSocket Endpoint:", "ws://127.0.0.1:8000/ws/telemetry", modal_rect.x + 20, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Packets Received:", f"{world_state.live_feed_packets:,} packets", modal_rect.x + 20, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Streaming Frequency:", f"{world_state.live_feed_rate_hz:.2f} Hz (1.0 Hz target)", modal_rect.x + 20, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Engine Emergency Level:", world_state.emergency_level, modal_rect.x + 20, curr_y, w,
                                         value_color=COLOR_CRITICAL if world_state.emergency_level == "CRITICAL" else COLOR_NOMINAL)

        # Separator line
        pygame.draw.line(surface, (45, 55, 75), (modal_rect.x + 20, curr_y + 4), (modal_rect.right - 20, curr_y + 4), 1)
        curr_y += 12

        # Godot 4.x Visual Rendering State section
        sub_hdr = self.ui.font_small.render("AUTHORITATIVE OPTICAL & ATMOSPHERIC RENDERING FEED", True, COLOR_ACCENT_MARS)
        surface.blit(sub_hdr, (modal_rect.x + 20, curr_y))
        curr_y += 20

        gv = world_state.godot_visuals
        fog = f"{gv.get('fog_density', 0.0018):.5f}" if 'fog_density' in gv else "0.0018 (Nominal)"
        sun_e = f"{gv.get('sun_energy', 1.0):.3f}" if 'sun_energy' in gv else "1.000"
        pitch = f"{gv.get('sun_pitch_deg', 45.0):.1f}°" if 'sun_pitch_deg' in gv else "45.0°"
        twilight = "TRUE (Forward Mie Scattering 78°-96°)" if gv.get("is_blue_twilight") else "FALSE (Normal Illumination)"
        wind_p = f"{gv.get('wind_particle_scale', 1.0):.2f}x" if 'wind_particle_scale' in gv else "1.00x"

        curr_y += self.ui.draw_key_value(surface, "Volumetric Fog Density:", fog, modal_rect.x + 20, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Sun Solar Irradiance / Pitch:", f"{sun_e} net | {pitch}", modal_rect.x + 20, curr_y, w)
        curr_y += self.ui.draw_key_value(surface, "Martian Blue Twilight State:", twilight, modal_rect.x + 20, curr_y, w,
                                         value_color=COLOR_INFO if gv.get("is_blue_twilight") else COLOR_TEXT_PRIMARY)
        curr_y += self.ui.draw_key_value(surface, "Wind Particle Scale Multiplier:", wind_p, modal_rect.x + 20, curr_y, w)

        # Active Hazards / Catastrophes count
        cats_str = ", ".join([c.get("name", str(c)) for c in world_state.catastrophes]) if world_state.catastrophes else "None (Nominal Operations)"
        curr_y += self.ui.draw_key_value(surface, "Active Catastrophe Hazards:", cats_str, modal_rect.x + 20, curr_y, w,
                                         value_color=COLOR_CRITICAL if world_state.catastrophes else COLOR_NOMINAL)

        # Close instruction
        close_surf = self.ui.font_small.render("Press [F5] or [ESC] to dismiss live feed monitor.", True, COLOR_TEXT_MUTED)
        surface.blit(close_surf, (modal_rect.centerx - close_surf.get_width() // 2, modal_rect.bottom - 26))
