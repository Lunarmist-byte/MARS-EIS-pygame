"""MARS SURVIVAL — World State Model.

Central container for simulated Martian world state received from MARS-EIS.
Tracks environmental conditions, infrastructure metrics, Martian sol timing,
emergent events, and version tracking to prevent out-of-order state overwrites.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .environmental_state import EnvironmentalState


@dataclass
class WorldState:
    """Authoritative world representation populated from MARS-EIS simulation."""
    world_id: str = "jezero_base"
    site_name: str = "Jezero Crater"
    latitude_deg: float = 18.38
    longitude_deg: float = 77.58
    elevation_m: float = -2500.0

    # Connection and sync health
    simulation_status: str = "DISCONNECTED"
    connection_error: Optional[str] = "Backend not yet reached"
    last_sync_timestamp: float = 0.0
    state_version: int = 0
    is_live_feed: bool = False
    live_feed_packets: int = 0
    live_feed_rate_hz: float = 0.0

    # Time parameters
    sol: int = 0
    fractional_sol: float = 0.5
    local_solar_time: str = "12:00:00"
    solar_longitude_deg: float = 0.0
    elapsed_seconds: float = 0.0

    # Environmental readings
    environment: EnvironmentalState = field(default_factory=EnvironmentalState)

    # Infrastructure status
    battery_soc: Optional[float] = None
    battery_level_wh: Optional[float] = None
    battery_capacity_wh: Optional[float] = None
    power_generation_w: Optional[float] = None
    power_consumption_w: Optional[float] = None
    solar_panel_efficiency: Optional[float] = None
    dust_soiling_ratio: Optional[float] = None
    habitat_pressure_pa: Optional[float] = None
    habitat_temp_c: Optional[float] = None

    # Missing from backend infrastructure state (explicitly handled as N/A)
    oxygen_reserve: Optional[float] = None
    water_reserve: Optional[float] = None
    food_reserve: Optional[float] = None

    # Emergent simulation events and catastrophes
    active_events: List[Dict[str, Any]] = field(default_factory=list)
    catastrophes: List[Dict[str, Any]] = field(default_factory=list)
    catastrophe_duration: float = 0.0  # Exact 15-second active catastrophe countdown
    issues: List[Dict[str, Any]] = field(default_factory=list)
    emergency_level: str = "NOMINAL"
    station_health: float = 100.0  # Overall base & habitat integrity (0 - 100%)
    collapse_countdown: float = 90.0  # Seconds until total habitat collapse during active issue (1.30 minutes / 90s)
    godot_visuals: Dict[str, Any] = field(default_factory=dict)

    def update_from_backend(self, data: Dict[str, Any], version: Optional[int] = None) -> bool:
        """Update state from MARS-EIS response dictionary.
        
        Guards against applying stale responses with lower version numbers.
        """
        if version is not None:
            if version < self.state_version:
                return False  # Discard out-of-order stale packet
            self.state_version = version
        else:
            self.state_version += 1

        self.last_sync_timestamp = time.time()
        self.simulation_status = "CONNECTED"
        self.connection_error = None

        # 1. Site info
        site = data.get("site", {})
        if isinstance(site, dict):
            self.site_name = site.get("name", self.site_name)
            self.latitude_deg = float(site.get("latitude_deg", self.latitude_deg))
            self.longitude_deg = float(site.get("longitude_deg", self.longitude_deg))
            self.elevation_m = float(site.get("elevation_m", self.elevation_m))

        # 2. Clock & Planetary coordinates
        if "sol" in data and data["sol"] is not None:
            self.sol = int(data["sol"])
        if "fractional_sol" in data and data["fractional_sol"] is not None:
            self.fractional_sol = float(data["fractional_sol"])
            # Calculate Local True Solar Time (LTST) in HH:MM:SS
            total_hours = self.fractional_sol * 24.0
            hours = int(total_hours) % 24
            minutes = int((total_hours - int(total_hours)) * 60)
            seconds = int((((total_hours - int(total_hours)) * 60) - minutes) * 60)
            self.local_solar_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        if "solar_longitude_deg" in data and data["solar_longitude_deg"] is not None:
            self.solar_longitude_deg = round(float(data["solar_longitude_deg"]), 2)
        if "elapsed_seconds" in data and data["elapsed_seconds"] is not None:
            self.elapsed_seconds = round(float(data["elapsed_seconds"]), 1)

        # 3. Environment readings
        self.environment = EnvironmentalState.from_backend_dict(data)

        # 4. Infrastructure readings
        infra = data.get("infrastructure", {})
        if isinstance(infra, dict) and infra:
            if "battery_soc" in infra and infra["battery_soc"] is not None:
                self.battery_soc = round(float(infra["battery_soc"]) * 100.0, 1)  # percentage
            elif "battery_charge_wh" in infra and "battery_capacity_wh" in infra:
                cap = float(infra["battery_capacity_wh"])
                chg = float(infra["battery_charge_wh"])
                self.battery_soc = round((chg / cap * 100.0) if cap > 0 else 0.0, 1)

            if "battery_level_wh" in infra and infra["battery_level_wh"] is not None:
                self.battery_level_wh = round(float(infra["battery_level_wh"]), 1)
            elif "battery_charge_wh" in infra and infra["battery_charge_wh"] is not None:
                self.battery_level_wh = round(float(infra["battery_charge_wh"]), 1)

            if "battery_capacity_wh" in infra and infra["battery_capacity_wh"] is not None:
                self.battery_capacity_wh = round(float(infra["battery_capacity_wh"]), 1)

            if "power_generation_watts" in infra and infra["power_generation_watts"] is not None:
                self.power_generation_w = round(float(infra["power_generation_watts"]), 1)
            elif "power_generation_w" in infra and infra["power_generation_w"] is not None:
                self.power_generation_w = round(float(infra["power_generation_w"]), 1)

            if "power_consumption_watts" in infra and infra["power_consumption_watts"] is not None:
                self.power_consumption_w = round(float(infra["power_consumption_watts"]), 1)

            if "solar_panel_efficiency" in infra and infra["solar_panel_efficiency"] is not None:
                self.solar_panel_efficiency = round(float(infra["solar_panel_efficiency"]) * 100.0, 1)

            if "dust_soiling_ratio" in infra and infra["dust_soiling_ratio"] is not None:
                self.dust_soiling_ratio = round(float(infra["dust_soiling_ratio"]) * 100.0, 1)

            if "habitat_pressure_pa" in infra and infra["habitat_pressure_pa"] is not None:
                self.habitat_pressure_pa = round(float(infra["habitat_pressure_pa"]), 1)

            if "habitat_temp_k" in infra and infra["habitat_temp_k"] is not None:
                self.habitat_temp_c = round(float(infra["habitat_temp_k"]) - 273.15, 1)

            # Consumables (if provided)
            if "oxygen_reserve" in infra and infra["oxygen_reserve"] is not None:
                self.oxygen_reserve = round(float(infra["oxygen_reserve"]), 1)
            if "water_reserve" in infra and infra["water_reserve"] is not None:
                self.water_reserve = round(float(infra["water_reserve"]), 1)
            if "food_reserve" in infra and infra["food_reserve"] is not None:
                self.food_reserve = round(float(infra["food_reserve"]), 1)

        # Check flat fields from WebSocket live telemetry
        if "battery_soc" in data and data["battery_soc"] is not None:
            val = float(data["battery_soc"])
            self.battery_soc = round(val * 100.0 if val <= 1.0 else val, 1)
        if "battery_level_wh" in data and data["battery_level_wh"] is not None:
            self.battery_level_wh = round(float(data["battery_level_wh"]), 1)
        if "power_gen_w" in data and data["power_gen_w"] is not None:
            self.power_generation_w = round(float(data["power_gen_w"]), 1)
        if "power_load_w" in data and data["power_load_w"] is not None:
            self.power_consumption_w = round(float(data["power_load_w"]), 1)

        # 5. Events, Catastrophes & Live Visuals
        if "active_events" in data and isinstance(data["active_events"], list):
            self.active_events = data["active_events"]
        elif "events" in data and isinstance(data["events"], list):
            self.active_events = data["events"]

        if "catastrophes" in data and isinstance(data["catastrophes"], list):
            # Only update catastrophes if actively in hazard window (15.0s)
            if self.catastrophe_duration > 0.0 or not self.catastrophes:
                if self.catastrophe_duration > 0.0:
                    for c in data["catastrophes"]:
                        if isinstance(c, dict):
                            c["duration"] = self.catastrophe_duration
                    self.catastrophes = data["catastrophes"]

        if "issues" in data and isinstance(data["issues"], list):
            self.issues = data["issues"]

        if "emergency_level" in data and data["emergency_level"] is not None:
            self.emergency_level = str(data["emergency_level"])

        if "godot_visuals" in data and isinstance(data["godot_visuals"], dict):
            self.godot_visuals = data["godot_visuals"]

        return True

    # -------------------------------------------------------------------------
    # Infrastructure Formatters (handles missing measurements with 'N/A')
    # -------------------------------------------------------------------------
    def format_battery(self) -> str:
        """Format battery SOC and capacity or return 'N/A'."""
        if self.battery_soc is None:
            return "N/A"
        cap_str = f" ({self.battery_level_wh:.0f}/{self.battery_capacity_wh:.0f} Wh)" if self.battery_level_wh is not None and self.battery_capacity_wh is not None else ""
        return f"{self.battery_soc:.1f}%{cap_str}"

    def format_power(self) -> str:
        """Format power generation and consumption or return 'N/A'."""
        gen_str = f"+{self.power_generation_w:.0f} W" if self.power_generation_w is not None else "--"
        con_str = f"-{self.power_consumption_w:.0f} W" if self.power_consumption_w is not None else "--"
        if self.power_generation_w is None and self.power_consumption_w is None:
            return "N/A"
        return f"{gen_str} / {con_str}"

    def format_habitat_cabin(self) -> str:
        """Format habitat internal pressure and temperature or return 'N/A'."""
        p_str = f"{self.habitat_pressure_pa / 1000.0:.1f} kPa" if self.habitat_pressure_pa is not None else "--"
        t_str = f"{self.habitat_temp_c:+.1f} °C" if self.habitat_temp_c is not None else "--"
        if self.habitat_pressure_pa is None and self.habitat_temp_c is None:
            return "N/A"
        return f"{p_str}, {t_str}"

    def format_solar_panels(self) -> str:
        """Format solar panel efficiency and dust soiling or return 'N/A'."""
        if self.solar_panel_efficiency is None:
            return "N/A"
        soil_str = f" (Soil: {self.dust_soiling_ratio:.1f}%)" if self.dust_soiling_ratio is not None else ""
        return f"{self.solar_panel_efficiency:.1f}% eff{soil_str}"

    def format_oxygen(self) -> str:
        """Format oxygen reserve or return 'N/A (unsimulated)'."""
        if self.oxygen_reserve is None:
            return "N/A"
        return f"{self.oxygen_reserve:.1f} kg"

    def format_water(self) -> str:
        """Format water reserve or return 'N/A (unsimulated)'."""
        if self.water_reserve is None:
            return "N/A"
        return f"{self.water_reserve:.1f} kg"

    def format_food(self) -> str:
        """Format food reserve or return 'N/A (unsimulated)'."""
        if self.food_reserve is None:
            return "N/A"
        return f"{self.food_reserve:.1f} days"
