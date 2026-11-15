"""MARS SURVIVAL — Interactive Situation & Scenario Modal.

Permits testing and triggering authoritative MARS-EIS scientific scenarios
and extreme environmental catastrophes directly from the game client.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_BORDER_ACCENT,
    COLOR_ACCENT_MARS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_HIGHLIGHT,
    COLOR_TEXT_MUTED,
    COLOR_NOMINAL,
    COLOR_WARNING,
    COLOR_CRITICAL,
    COLOR_INFO,
)
from world.world_state import WorldState
from ui.components import UIComponents


class SituationModal:
    """In-game modal dialog for injecting MARS-EIS scenarios and catastrophes."""

    def __init__(self, ui_components: UIComponents) -> None:
        self.ui = ui_components
        self.is_open: bool = False
        self.feedback_message: str = ""
        self.feedback_color: tuple = COLOR_NOMINAL
        self.feedback_timer: float = 0.0

        # Scenario Registry mapped to MARS-EIS
        self.scenarios = [
            ("1", "2018 Global Dust Storm (MY34)", "global_dust_storm_2018", "Planet-encircling dust event (tau > 2.2), solar blackout, PV degradation"),
            ("2", "Perihelion Convective Lifting", "perihelion_convective_lifting", "High thermal gradients (delta T > 25K), convective dust devils, wind gusts"),
            ("3", "Winter Polar Cold Snap", "winter_polar_condensation", "CO2 polar condensation, barometric minimum (580 Pa), deep freeze (-115 C)"),
            ("4", "Cerberus Fossae Marsquake", "insight_marsquake_seismic", "InSight Mag 4.7 broadband quake, ground trauma, regolith displacement"),
            ("5", "Nominal Jezero Spring", "nominal_jezero_spring", "Clean skies (tau 0.35), moderate diurnal winds, optimal PV power generation"),
        ]

        # Catastrophe Registry mapped to MARS-EIS
        self.catastrophes = [
            ("6", "Global Dust Storm Blackout", "GLOBAL_DUST_STORM", "Total solar extinction, PV failure, dune mobility loss"),
            ("7", "Severe Marsquake & Hull Shock", "SEVERE_MARSQUAKE", "Structural hull breach, decompression leaks, camera trauma"),
            ("8", "Solar Particle Event (Cosmic Radiation)", "SOLAR_PARTICLE_EVENT", "Lethal radiation surge, electronic static glitch lines"),
            ("9", "Cryogenic Flash Freeze", "CRYOGENIC_FLASH_FREEZE", "Thermal runaway, battery electrolyte freeze, frost vignette"),
            ("0", "Habitat Hull Breach Decompression", "HABITAT_HULL_BREACH", "Rapid depressurization, oxygen drain, emergency klaxon"),
        ]

    def toggle(self) -> bool:
        """Toggle modal visibility."""
        self.is_open = not self.is_open
        return self.is_open

    def set_feedback(self, msg: str, success: bool = True) -> None:
        """Display momentary status feedback."""
        self.feedback_message = msg
        self.feedback_color = COLOR_NOMINAL if success else COLOR_CRITICAL
        self.feedback_timer = 3.5

    def update(self, dt: float) -> None:
        """Update timer for feedback text."""
        if self.feedback_timer > 0:
            self.feedback_timer -= dt

    def handle_key(self, key: int, sync: Any, world_state: Optional[WorldState] = None) -> bool:
        """Handle numeric shortcut keys while modal is active. Returns True if handled."""
        if not self.is_open:
            return False

        # Close keys
        if key in (pygame.K_ESCAPE, pygame.K_t, pygame.K_F4):
            self.is_open = False
            return True

        # Check Scenarios (1-5)
        for num_str, title, scen_id, _ in self.scenarios:
            k = getattr(pygame, f"K_{num_str}", None)
            if key == k:
                sync.apply_scenario(scen_id)
                self.set_feedback(f"Dispatched Scenario: {title} to MARS-EIS...", True)
                if world_state:
                    if scen_id == "global_dust_storm_2018":
                        world_state.catastrophes = [
                            {"type": "GLOBAL_DUST_STORM", "name": "2018 Global Dust Storm", "severity": 0.95, "active": True}
                        ]
                        world_state.environment.dust_opacity_tau = 2.45
                        world_state.environment.wind_speed_m_s = 24.0
                        world_state.environment.wind_direction_deg = 135.0
                    elif scen_id == "nominal_jezero_spring":
                        world_state.catastrophes.clear()
                        world_state.environment.dust_opacity_tau = 0.35
                        world_state.environment.wind_speed_m_s = 6.0
                    elif scen_id == "insight_marsquake_seismic":
                        world_state.catastrophes = [
                            {"type": "SEVERE_MARSQUAKE", "name": "Cerberus Fossae Marsquake", "severity": 0.90, "screen_shake_intensity": 1.4, "active": True}
                        ]
                return True

        # Check Catastrophes (6-9, 0)
        for num_str, title, cat_type, _ in self.catastrophes:
            k = getattr(pygame, f"K_{num_str}", None)
            if key == k:
                sync.trigger_catastrophe(cat_type, severity=0.85)
                self.set_feedback(f"Injected Catastrophe: {title} into MARS-EIS!", False)
                if world_state:
                    if cat_type == "GLOBAL_DUST_STORM":
                        world_state.catastrophes = [
                            {"type": "GLOBAL_DUST_STORM", "name": "Global Dust Storm Blackout", "severity": 0.95, "duration": 18.0, "active": True}
                        ]
                        world_state.environment.dust_opacity_tau = 2.5
                        world_state.environment.wind_speed_m_s = 25.0
                    else:
                        world_state.catastrophes = [
                            {
                                "type": cat_type,
                                "name": title,
                                "severity": 0.85,
                                "duration": 18.0,
                                "screen_shake_intensity": 1.3 if "MARSQUAKE" in cat_type else 0.0,
                                "active": True
                            }
                        ]
                return True

        return False

    def render(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render situation injector dialog overlay."""
        if not self.is_open:
            return

        modal_w = 760
        modal_h = 520
        rect = pygame.Rect(
            (WINDOW_WIDTH - modal_w) // 2,
            (WINDOW_HEIGHT - modal_h) // 2,
            modal_w,
            modal_h,
        )

        # Modal backdrop & glass styling
        self.ui.draw_panel(
            surface,
            rect,
            bg_color=(14, 18, 26, 250),
            border_color=COLOR_ACCENT_MARS,
            border_width=2,
        )

        # Header
        hdr = self.ui.font_large.render("MARS-EIS // SITUATION INJECTOR & SCENARIOS", True, COLOR_ACCENT_MARS)
        surface.blit(hdr, (rect.x + 24, rect.y + 18))

        sub = self.ui.font_small.render("Trigger authoritative Martian physical events & extreme catastrophe cascades", True, COLOR_TEXT_SECONDARY)
        surface.blit(sub, (rect.x + 24, rect.y + 44))

        curr_y = rect.y + 70

        # Section 1: Scientific Scenario Presets
        sec1 = self.ui.font_medium.render("PRESET SCIENTIFIC SCENARIOS (Press [1] - [5]):", True, COLOR_TEXT_HIGHLIGHT)
        surface.blit(sec1, (rect.x + 24, curr_y))
        curr_y += 24

        for num_str, title, _, desc in self.scenarios:
            line_txt = f"[{num_str}] {title} — {desc}"
            surf = self.ui.font_tiny.render(line_txt, True, COLOR_TEXT_PRIMARY)
            surface.blit(surf, (rect.x + 36, curr_y))
            curr_y += 20

        curr_y += 10
        pygame.draw.line(surface, (45, 55, 75), (rect.x + 24, curr_y), (rect.right - 24, curr_y))
        curr_y += 12

        # Section 2: Catastrophes
        sec2 = self.ui.font_medium.render("EXTREME CATASTROPHE INJECTIONS (Press [6] - [0]):", True, COLOR_CRITICAL)
        surface.blit(sec2, (rect.x + 24, curr_y))
        curr_y += 24

        for num_str, title, _, desc in self.catastrophes:
            line_txt = f"[{num_str}] {title} — {desc}"
            surf = self.ui.font_tiny.render(line_txt, True, COLOR_TEXT_PRIMARY)
            surface.blit(surf, (rect.x + 36, curr_y))
            curr_y += 20

        curr_y += 10
        pygame.draw.line(surface, (45, 55, 75), (rect.x + 24, curr_y), (rect.right - 24, curr_y))
        curr_y += 12

        # Section 3: Active Status in Simulation
        active_cats = world_state.catastrophes
        if active_cats:
            cat_names = ", ".join(c.get("name", c.get("type", "HAZARD")) for c in active_cats)
            stat_str = f"ACTIVE BACKEND CATASTROPHE: {cat_names.upper()}"
            stat_surf = self.ui.font_small.render(stat_str, True, COLOR_CRITICAL)
            surface.blit(stat_surf, (rect.x + 24, curr_y))
        else:
            stat_str = "CURRENT STATUS: Nominal Jezero Baseline (No active catastrophe)"
            stat_surf = self.ui.font_small.render(stat_str, True, COLOR_NOMINAL)
            surface.blit(stat_surf, (rect.x + 24, curr_y))
        curr_y += 22

        # Feedback banner (if user triggered an event)
        if self.feedback_timer > 0 and self.feedback_message:
            fb = self.ui.font_small.render(f">> {self.feedback_message}", True, self.feedback_color)
            surface.blit(fb, (rect.x + 24, curr_y))

        # Bottom dismiss prompt
        close_txt = "Press [1-0] to trigger  |  Press [T], [F4], or [ESC] to return to simulation"
        close_surf = self.ui.font_small.render(close_txt, True, COLOR_TEXT_MUTED)
        surface.blit(close_surf, (rect.x + 24, rect.bottom - 26))
