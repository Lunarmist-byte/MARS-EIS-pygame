"""MARS SURVIVAL — Active Events & Hazards HUD Panel.

Renders active emergent Martian environmental events, storm warnings,
catastrophe alerts, and anomaly diagnostics received from MARS-EIS.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import List, Dict, Any
import pygame
from config import (
    COLOR_NOMINAL,
    COLOR_WARNING,
    COLOR_CRITICAL,
    COLOR_INFO,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
)
from .components import UIComponents
from world.world_state import WorldState


class EventPanel:
    """Renders active events and catastrophe warnings."""

    def __init__(self, ui: UIComponents) -> None:
        self.ui = ui

    def render(self, surface: pygame.Surface, rect: pygame.Rect, world_state: WorldState) -> None:
        """Render event panel within the specified screen rectangle."""
        self.ui.draw_panel(surface, rect)

        # Header
        header_surf = self.ui.font_medium.render("ACTIVE HAZARDS & SIMULATION EVENTS", True, COLOR_TEXT_PRIMARY)
        surface.blit(header_surf, (rect.x + 12, rect.y + 10))

        events = world_state.active_events
        catastrophes = world_state.catastrophes

        all_items: List[Dict[str, Any]] = []
        for cat in catastrophes:
            all_items.append({"title": cat.get("title", "Catastrophe"), "severity": 4, "desc": cat.get("description", "Extreme planetary catastrophe active"), "type": "CATASTROPHE"})
        for ev in events:
            all_items.append({"title": ev.get("event_type", ev.get("title", "Event")), "severity": ev.get("severity", 2), "desc": ev.get("description", ""), "type": "EVENT"})

        curr_y = rect.y + 34
        max_y = rect.bottom - 12

        if not all_items:
            # Nominal state indicator
            self.ui.draw_badge(surface, "NOMINAL", rect.x + 12, curr_y, COLOR_NOMINAL, (0, 0, 0), self.ui.font_tiny)
            nom_surf = self.ui.font_small.render("No active hazards or emergent storm anomalies.", True, COLOR_TEXT_MUTED)
            surface.blit(nom_surf, (rect.x + 80, curr_y + 1))
            return

        for item in all_items[:4]:  # Show up to 4 active events
            if curr_y + 36 > max_y:
                break

            sev = item.get("severity", 1)
            if sev >= 4:
                badge_color = COLOR_CRITICAL
                badge_text = "CRITICAL"
            elif sev == 3:
                badge_color = COLOR_WARNING
                badge_text = "HIGH"
            elif sev == 2:
                badge_color = (230, 160, 40)
                badge_text = "MODERATE"
            else:
                badge_color = COLOR_INFO
                badge_text = "ADVISORY"

            badge_rect = self.ui.draw_badge(surface, badge_text, rect.x + 12, curr_y, badge_color, (0, 0, 0), self.ui.font_tiny)

            title_surf = self.ui.font_small.render(str(item["title"]).replace("_", " ").upper(), True, COLOR_TEXT_PRIMARY)
            surface.blit(title_surf, (badge_rect.right + 8, curr_y))

            desc_text = item["desc"]
            if len(desc_text) > 55:
                desc_text = desc_text[:52] + "..."
            desc_surf = self.ui.font_tiny.render(desc_text, True, COLOR_TEXT_SECONDARY)
            surface.blit(desc_surf, (rect.x + 12, curr_y + 18))

            curr_y += 38
