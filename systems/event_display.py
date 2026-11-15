"""MARS SURVIVAL — Event Notification Display System.

Processes, filters, and formats emergent environmental warnings and
catastrophe alerts received from MARS-EIS.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import time


@dataclass
class FormattedEvent:
    """Formatted representation of a simulation hazard or anomaly."""
    event_id: str
    event_type: str
    severity: int
    severity_label: str
    description: str
    affected_systems: List[str]
    confidence_pct: Optional[float] = None
    received_time: float = 0.0


class EventDisplayManager:
    """Manages active simulation events and alert banners."""

    def __init__(self) -> None:
        self.active_events: Dict[str, FormattedEvent] = {}
        self.transient_notifications: List[Dict[str, Any]] = []

    def update_events(self, raw_events: List[Dict[str, Any]]) -> None:
        """Update active event map from backend event list, avoiding duplicates."""
        current_ids = set()

        for ev in raw_events:
            ev_id = str(ev.get("event_id", ev.get("id", f"ev_{len(current_ids)}")))
            current_ids.add(ev_id)

            sev = int(ev.get("severity", 1))
            sev_label = "LOW"
            if sev == 2:
                sev_label = "MODERATE"
            elif sev == 3:
                sev_label = "HIGH"
            elif sev >= 4:
                sev_label = "CRITICAL"

            formatted = FormattedEvent(
                event_id=ev_id,
                event_type=str(ev.get("event_type", "hazard")),
                severity=sev,
                severity_label=sev_label,
                description=str(ev.get("description", ev.get("title", "Environmental anomaly detected"))),
                affected_systems=list(ev.get("affected_systems", [])),
                confidence_pct=round(float(ev.get("confidence", 1.0)) * 100.0, 1) if "confidence" in ev else None,
                received_time=time.time()
            )
            self.active_events[ev_id] = formatted

        # Remove resolved events that are no longer returned by MARS-EIS
        resolved = [eid for eid in self.active_events if eid not in current_ids]
        for eid in resolved:
            del self.active_events[eid]

    def add_notification(self, title: str, message: str, level: str = "info", duration: float = 5.0) -> None:
        """Post a transient notification message to display banner."""
        self.transient_notifications.append({
            "title": title,
            "message": message,
            "level": level,
            "expires_at": time.time() + duration,
        })

    def get_active_notifications(self) -> List[Dict[str, Any]]:
        """Return non-expired notifications."""
        now = time.time()
        self.transient_notifications = [n for n in self.transient_notifications if n["expires_at"] > now]
        return self.transient_notifications
