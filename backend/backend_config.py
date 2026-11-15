"""MARS SURVIVAL — Backend Configuration.

Encapsulates network parameters, endpoint routing, and timeout thresholds.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from config import BACKEND_CONFIG


@dataclass
class BackendConfig:
    """MARS-EIS HTTP & WebSocket connection settings."""
    base_url: str = BACKEND_CONFIG.get("base_url", "http://127.0.0.1:8000")
    ws_url: str = BACKEND_CONFIG.get("ws_url", "ws://127.0.0.1:8000/ws/telemetry")
    sync_interval_seconds: float = BACKEND_CONFIG.get("sync_interval_seconds", 2.0)
    request_timeout_seconds: float = BACKEND_CONFIG.get("request_timeout_seconds", 5.0)
    reconnect_interval_seconds: float = BACKEND_CONFIG.get("reconnect_interval_seconds", 3.0)
    delta_simulation_seconds: float = BACKEND_CONFIG.get("delta_simulation_seconds", 10.0)
    automatic_advance: bool = BACKEND_CONFIG.get("automatic_advance", True)

    def get_ws_url(self) -> str:
        """Derive WebSocket endpoint URL from base_url if ws_url is not explicitly specified."""
        if self.ws_url:
            return self.ws_url
        base = self.base_url.rstrip("/")
        if base.startswith("https://"):
            return "wss://" + base[8:] + "/ws/telemetry"
        elif base.startswith("http://"):
            return "ws://" + base[7:] + "/ws/telemetry"
        return f"ws://{base}/ws/telemetry"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BackendConfig:
        return cls(
            base_url=str(data.get("base_url", "http://127.0.0.1:8000")),
            ws_url=str(data.get("ws_url", "ws://127.0.0.1:8000/ws/telemetry")),
            sync_interval_seconds=float(data.get("sync_interval_seconds", 2.0)),
            request_timeout_seconds=float(data.get("request_timeout_seconds", 5.0)),
            reconnect_interval_seconds=float(data.get("reconnect_interval_seconds", 3.0)),
            delta_simulation_seconds=float(data.get("delta_simulation_seconds", 10.0)),
            automatic_advance=bool(data.get("automatic_advance", True)),
        )
