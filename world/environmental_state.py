"""MARS SURVIVAL — Environmental State Model.

Encapsulates environmental readings received from MARS-EIS.
Implements strict formatting and missing measurement handling ('N/A'/'--').

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class EnvironmentalState:
    """Environmental parameters authoritative to MARS-EIS."""
    air_temperature_c: Optional[float] = None
    surface_temperature_c: Optional[float] = None
    pressure_pa: Optional[float] = None
    wind_speed_m_s: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    dust_opacity_tau: Optional[float] = None
    radiation_rate_ush_hr: Optional[float] = None
    solar_irradiance_w_m2: Optional[float] = None
    ice_stability: Optional[str] = None
    atmospheric_density_kg_m3: Optional[float] = None

    @classmethod
    def from_backend_dict(cls, data: Dict[str, Any]) -> EnvironmentalState:
        """Parse raw dictionary from MARS-EIS state API response.
        
        Handles both nested MARS-EIS structure:
          - thermal (air_temp_k, surface_temp_k)
          - atmosphere (pressure_pa, wind_speed_ms, wind_direction_deg, density_kg_m3)
          - dust (optical_depth_tau)
          - radiation (surface_dose_rate_ush_hr)
          - solar (net_flux_wm2)
        and flattened format if available.
        """
        if not data or not isinstance(data, dict):
            return cls()

        instance = cls()

        # 1. Thermal readings (Convert Kelvin to Celsius if given in Kelvin)
        thermal = data.get("thermal", {})
        if isinstance(thermal, dict) and thermal:
            air_k = thermal.get("air_temp_k")
            if air_k is not None:
                instance.air_temperature_c = round(float(air_k) - 273.15, 2)
            surf_k = thermal.get("surface_temp_k")
            if surf_k is not None:
                instance.surface_temperature_c = round(float(surf_k) - 273.15, 2)
        else:
            if "air_temp_k" in data and data["air_temp_k"] is not None:
                instance.air_temperature_c = round(float(data["air_temp_k"]) - 273.15, 2)
            elif "air_temperature_c" in data and data["air_temperature_c"] is not None:
                instance.air_temperature_c = round(float(data["air_temperature_c"]), 2)

            if "surface_temp_k" in data and data["surface_temp_k"] is not None:
                instance.surface_temperature_c = round(float(data["surface_temp_k"]) - 273.15, 2)
            elif "surface_temperature_c" in data and data["surface_temperature_c"] is not None:
                instance.surface_temperature_c = round(float(data["surface_temperature_c"]), 2)

        # 2. Atmospheric readings
        atmosphere = data.get("atmosphere", {})
        if isinstance(atmosphere, dict) and atmosphere:
            p = atmosphere.get("pressure_pa")
            if p is not None:
                instance.pressure_pa = round(float(p), 1)
            ws = atmosphere.get("wind_speed_ms", atmosphere.get("wind_speed_m_s"))
            if ws is not None:
                instance.wind_speed_m_s = round(float(ws), 2)
            wd = atmosphere.get("wind_direction_deg")
            if wd is not None:
                instance.wind_direction_deg = round(float(wd), 1)
            rho = atmosphere.get("density_kg_m3")
            if rho is not None:
                instance.atmospheric_density_kg_m3 = round(float(rho), 5)
        else:
            if "pressure_pa" in data and data["pressure_pa"] is not None:
                instance.pressure_pa = round(float(data["pressure_pa"]), 1)
            ws = data.get("wind_speed_ms", data.get("wind_speed_m_s"))
            if ws is not None:
                instance.wind_speed_m_s = round(float(ws), 2)
            if "wind_direction_deg" in data and data["wind_direction_deg"] is not None:
                instance.wind_direction_deg = round(float(data["wind_direction_deg"]), 1)

        # 3. Dust readings
        dust = data.get("dust", {})
        if isinstance(dust, dict) and dust:
            tau = dust.get("optical_depth_tau", dust.get("dust_opacity"))
            if tau is not None:
                instance.dust_opacity_tau = round(float(tau), 3)
        else:
            tau = data.get("optical_depth_tau", data.get("dust_opacity"))
            if tau is not None:
                instance.dust_opacity_tau = round(float(tau), 3)

        # 4. Radiation readings
        radiation = data.get("radiation", {})
        if isinstance(radiation, dict) and radiation:
            rate = radiation.get("surface_dose_rate_ush_hr", radiation.get("radiation_rate"))
            if rate is not None:
                instance.radiation_rate_ush_hr = round(float(rate), 2)
        else:
            rate = data.get("surface_dose_rate_ush_hr", data.get("radiation_rate"))
            if rate is not None:
                instance.radiation_rate_ush_hr = round(float(rate), 2)

        # 5. Solar irradiance
        solar = data.get("solar", {})
        if isinstance(solar, dict) and solar:
            flux = solar.get("net_flux_wm2", solar.get("solar_irradiance_w_m2"))
            if flux is not None:
                instance.solar_irradiance_w_m2 = round(float(flux), 1)
        else:
            flux = data.get("solar_flux_wm2", data.get("net_flux_wm2", data.get("solar_irradiance_w_m2")))
            if flux is not None:
                instance.solar_irradiance_w_m2 = round(float(flux), 1)

        # 6. Miscellaneous
        if "ice_stability" in data and data["ice_stability"] is not None:
            instance.ice_stability = str(data["ice_stability"])

        return instance

    # -------------------------------------------------------------------------
    # Formatting Helpers — strictly handle missing measurements with 'N/A'
    # -------------------------------------------------------------------------
    def format_air_temp(self) -> str:
        """Format atmospheric temperature or return 'N/A'."""
        if self.air_temperature_c is None:
            return "N/A"
        return f"{self.air_temperature_c:+.1f} °C"

    def format_surface_temp(self) -> str:
        """Format ground surface temperature or return 'N/A'."""
        if self.surface_temperature_c is None:
            return "N/A"
        return f"{self.surface_temperature_c:+.1f} °C"

    def format_pressure(self) -> str:
        """Format atmospheric pressure in Pa or return 'N/A'."""
        if self.pressure_pa is None:
            return "N/A"
        return f"{self.pressure_pa:.1f} Pa"

    def format_wind(self) -> str:
        """Format wind speed and direction or return 'N/A'."""
        if self.wind_speed_m_s is None:
            return "N/A"
        dir_str = f" @ {self.wind_direction_deg:.0f}°" if self.wind_direction_deg is not None else ""
        return f"{self.wind_speed_m_s:.1f} m/s{dir_str}"

    def format_dust_opacity(self) -> str:
        """Format optical depth (tau) or return 'N/A'."""
        if self.dust_opacity_tau is None:
            return "N/A"
        return f"τ {self.dust_opacity_tau:.2f}"

    def format_radiation(self) -> str:
        """Format surface radiation rate or return 'N/A'."""
        if self.radiation_rate_ush_hr is None:
            return "N/A"
        return f"{self.radiation_rate_ush_hr:.1f} μSv/h"

    def format_solar(self) -> str:
        """Format net solar flux or return 'N/A'."""
        if self.solar_irradiance_w_m2 is None:
            return "N/A"
        return f"{self.solar_irradiance_w_m2:.1f} W/m²"
