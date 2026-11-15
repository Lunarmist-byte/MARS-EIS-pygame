"""MARS SURVIVAL — MARS-EIS HTTP API Client.

Authoritative REST client for querying Martian environmental state,
advancing simulation time, sending movement records, and dispatching actions.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, Tuple, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .backend_config import BackendConfig

logger = logging.getLogger(__name__)


class ApiClient:
    """HTTP REST client for MARS-EIS simulation backend."""

    def __init__(self, config: BackendConfig) -> None:
        self.config = config
        self.session = requests.Session()
        # Disable system proxy routing for local simulation communication
        self.session.trust_env = False
        
        # Configure connection pooling and keepalive
        adapter = HTTPAdapter(
            pool_connections=5,
            pool_maxsize=10,
            max_retries=Retry(total=1, backoff_factor=0.2, status_forcelist=[502, 503, 504])
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _url(self, path: str) -> str:
        """Construct full URL from base URL and path."""
        base = self.config.base_url.rstrip("/")
        rel = path.lstrip("/")
        return f"{base}/{rel}"

    def _request_get_state(self, url: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        resp = self.session.get(url, timeout=self.config.request_timeout_seconds)
        if resp.status_code == 200:
            body = resp.json()
            if isinstance(body, dict) and body.get("success", False):
                return True, body.get("data", {}), body.get("message", "World state retrieved")
            elif isinstance(body, dict) and "sol" in body:
                return True, body, "World state retrieved (raw)"
            return False, None, f"API reported failure: {body.get('message', 'Unknown error')}"
        return False, None, f"HTTP {resp.status_code}: {resp.text[:100]}"

    def get_world_state(self) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Query GET /api/v1/world/state.
        
        Returns:
            Tuple of (success, state_dict, message)
        """
        url = self._url("/api/v1/world/state")
        try:
            return self._request_get_state(url)
        except requests.exceptions.Timeout:
            return False, None, f"Timeout after {self.config.request_timeout_seconds}s"
        except requests.exceptions.ConnectionError:
            # Fallback attempt switching between 127.0.0.1 and localhost
            alt_base = (
                self.config.base_url.replace("127.0.0.1", "localhost")
                if "127.0.0.1" in self.config.base_url
                else self.config.base_url.replace("localhost", "127.0.0.1")
            )
            if alt_base != self.config.base_url:
                try:
                    alt_url = f"{alt_base.rstrip('/')}/api/v1/world/state"
                    ok, data, msg = self._request_get_state(alt_url)
                    if ok:
                        self.config.base_url = alt_base
                        return ok, data, msg
                except Exception:
                    pass
            return False, None, f"Connection refused at {self.config.base_url}"
        except Exception as exc:
            return False, None, f"Request error: {str(exc)}"

    def get_region_info(self, region_id: str = "jezero_base") -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Query GET /api/v1/world/region/{region_id}."""
        url = self._url(f"/api/v1/world/region/{region_id}")
        try:
            resp = self.session.get(url, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                return True, body.get("data", {}), body.get("message", "Region data retrieved")
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)

    def advance_simulation(
        self,
        delta_simulation_seconds: float = 10.0,
        sols: float = 0.0,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """POST /api/v1/world/advance to step the Martian simulation clock.
        
        MARS-EIS AdvanceRequest expects { 'sols': float, 'dt_seconds': float }.
        """
        url = self._url("/api/v1/world/advance")
        payload = {
            "sols": sols,
            "dt_seconds": float(delta_simulation_seconds),
        }
        try:
            resp = self.session.post(url, json=payload, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                if body.get("success", False):
                    return True, body.get("data", {}), body.get("message", "Advanced simulation")
                return False, None, body.get("message", "Advance failed")
            return False, None, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as exc:
            return False, None, str(exc)

    def send_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """POST /api/v1/world/action to submit rover or habitat intervention.
        
        MARS-EIS ActionRequestSchema: { 'action_type': str, 'parameters': dict }.
        Valid ActionTypes in MARS-EIS:
          ROVER_DRIVE, CLEAN_PANELS, EXCAVATE, CONSTRUCT_BERM, EXTRACT_ICE,
          SEAL_HULL_BREACH, ROUTE_EMERGENCY_POWER, DEPLOY_STORM_SHIELD, SHELTER_IN_BUNKER
        """
        url = self._url("/api/v1/world/action")
        payload = {
            "action_type": action_type,
            "parameters": parameters,
        }
        try:
            resp = self.session.post(url, json=payload, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                return body.get("success", False), body.get("data", {}), body.get("message", "Action processed")
            return False, None, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as exc:
            return False, None, str(exc)

    def send_movement(
        self,
        distance_meters: float,
        speed_ms: float = 1.5,
        heading_deg: float = 0.0,
        slope_pct: float = 0.0,
        world_position: Optional[List[float]] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """POST /api/v1/world/movement to submit continuous traversed distance."""
        url = self._url("/api/v1/world/movement")
        payload = {
            "distance_meters": max(0.1, round(float(distance_meters), 2)),
            "speed_ms": round(float(speed_ms), 2),
            "heading_deg": round(float(heading_deg), 1),
            "slope_pct": round(float(slope_pct), 2),
            "world_position": world_position or [0.0, 0.0, 0.0],
        }
        try:
            resp = self.session.post(url, json=payload, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                return body.get("success", False), body.get("data", {}), body.get("message", "Movement processed")
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)

    def get_events(self) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """GET /api/v1/world/events for active emergent hazards and anomalies."""
        url = self._url("/api/v1/world/events")
        try:
            resp = self.session.get(url, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                return body.get("success", False), body.get("data", {}), body.get("message", "Events retrieved")
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)

    def trigger_catastrophe(
        self,
        catastrophe_type: str,
        severity: float = 0.8,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """POST /api/v1/world/catastrophe to inject extreme Martian environmental disasters."""
        url = self._url("/api/v1/world/catastrophe")
        payload = {
            "catastrophe_type": catastrophe_type,
            "severity": float(severity),
        }
        try:
            resp = self.session.post(url, json=payload, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                return body.get("success", False), body.get("data", {}), body.get("message", "Catastrophe triggered")
            return False, None, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as exc:
            return False, None, str(exc)

    def apply_scenario(
        self,
        scenario_id: str,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """POST /api/v1/world/scenario to load scientifically grounded scenario presets."""
        url = self._url("/api/v1/world/scenario")
        payload = {"scenario_id": scenario_id}
        try:
            resp = self.session.post(url, json=payload, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                return body.get("success", False), body.get("data", {}), body.get("message", "Scenario applied")
            return False, None, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as exc:
            return False, None, str(exc)

    def get_forecast(
        self,
        horizon_hours: float = 6.0,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """GET /api/v1/world/forecast for AI/ML meteorological forecasting."""
        url = self._url(f"/api/v1/world/forecast?horizon_hours={horizon_hours}")
        try:
            resp = self.session.get(url, timeout=self.config.request_timeout_seconds)
            if resp.status_code == 200:
                body = resp.json()
                return body.get("success", False), body.get("data", {}), body.get("message", "Forecast retrieved")
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)
