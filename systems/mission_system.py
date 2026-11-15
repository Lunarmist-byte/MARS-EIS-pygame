"""MARS SURVIVAL — Base Mission & Infrastructure Progression System.

Manages active missions, facility work orders, objective tracking,
and applies authoritative stat boosts (Oxygen, Water, Food, Battery SOC,
Solar Efficiency, Suit Health, Structural Integrity) when completed.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from world.world_state import WorldState
from world.player_state import PlayerState


@dataclass
class Mission:
    """Represents a specific facility survival mission."""
    mission_id: str
    facility_id: str
    facility_name: str
    title: str
    objective: str
    reward_desc: str
    action_type: str
    stat_type: str
    stat_boost_amount: float
    completed: bool = False
    times_completed: int = 0


class MissionSystem:
    """Coordinates base missions, facility engagements, and stat increments."""

    def __init__(self) -> None:
        self.missions: List[Mission] = [
            Mission(
                mission_id="m_oxygen",
                facility_id="oxygen_plant",
                facility_name="ECLSS Oxygen Plant",
                title="Purge Sabatier Catalysts",
                objective="Vent CO2 scrubbers and synthesize breathable O2.",
                reward_desc="+25.0 kg Oxygen Reserve",
                action_type="GENERATE_OXYGEN",
                stat_type="oxygen",
                stat_boost_amount=25.0,
            ),
            Mission(
                mission_id="m_water",
                facility_id="water_recycling",
                facility_name="Water Recycling Facility",
                title="Extract Glacial Perchlorate Brine",
                objective="Filter greywater and centrifuge subsurface ice cores.",
                reward_desc="+35.0 kg Water Reserve",
                action_type="EXTRACT_ICE",
                stat_type="water",
                stat_boost_amount=35.0,
            ),
            Mission(
                mission_id="m_greenhouse",
                facility_id="greenhouse",
                facility_name="Hydroponic Greenhouse",
                title="Harvest Spirulina Algae Biomass",
                objective="Re-irrigate hydroponic seedling trays with nutrients.",
                reward_desc="+15.0 Days Food Rations",
                action_type="HARVEST_CROPS",
                stat_type="food",
                stat_boost_amount=15.0,
            ),
            Mission(
                mission_id="m_solar",
                facility_id="solar_farm",
                facility_name="Photovoltaic Solar Farm",
                title="Electrostatic Dust De-Soiling",
                objective="Scrape ferric oxide regolith from solar arrays.",
                reward_desc="+25% Solar Panel Efficiency & +450W Power",
                action_type="CLEAN_PANELS",
                stat_type="solar",
                stat_boost_amount=25.0,
            ),
            Mission(
                mission_id="m_reactor",
                facility_id="power_generator",
                facility_name="Electrical Grid Generator",
                title="Rebalance Surface Microgrid",
                objective="Route fission core emergency feed into battery banks.",
                reward_desc="+30% Battery SOC (+1500 Wh Storage)",
                action_type="ROUTE_EMERGENCY_POWER",
                stat_type="battery",
                stat_boost_amount=30.0,
            ),
            Mission(
                mission_id="m_medbay",
                facility_id="medbay",
                facility_name="Medical Bay & Bio-Scanner",
                title="Crew Bio-Diagnostics & Sterilization",
                objective="Perform medical triage and replenish astronaut vitals.",
                reward_desc="100% Suit Health & Medical Vitals",
                action_type="TREAT_CREW",
                stat_type="health",
                stat_boost_amount=100.0,
            ),
            Mission(
                mission_id="m_workshop",
                facility_id="engineering_workshop",
                facility_name="Robotics Workshop",
                title="Fabricate Titanium Structural Sealants",
                objective="Engage 3D robotic arm to machine hull patch braces.",
                reward_desc="Base Structural Integrity & 101.3 kPa ECLSS",
                action_type="FABRICATE_PARTS",
                stat_type="hull",
                stat_boost_amount=1.0,
            ),
            Mission(
                mission_id="m_comms",
                facility_id="comm_center",
                facility_name="Deep Space Telemetry Comms",
                title="Orbital Dish Synchronization",
                objective="Align phased antenna array to downlink scientific packets.",
                reward_desc="Orbital DSN Telemetry Synchronized",
                action_type="TRANSMIT_TELEMETRY",
                stat_type="comms",
                stat_boost_amount=1.0,
            ),
            Mission(
                mission_id="m_command",
                facility_id="command_lab",
                facility_name="Mission Operations Command Lab",
                title="Jezero Multi-Spectral Atmospheric Model",
                objective="Process atmospheric optical depth simulation forecast.",
                reward_desc="Predictive Storm Forecast Decoded",
                action_type="ANALYZE_ATMOSPHERE",
                stat_type="forecast",
                stat_boost_amount=1.0,
            ),
        ]

        self.active_index: int = 0
        self.total_completed: int = 0

    @property
    def current_mission(self) -> Mission:
        """Get the currently highlighted active mission."""
        return self.missions[self.active_index % len(self.missions)]

    def complete_mission_for_facility(
        self,
        facility_id: str,
        world_state: WorldState,
        player_state: PlayerState,
    ) -> Optional[Tuple[str, str]]:
        """Process facility interaction, boost tracked stats, and progress objectives.
        
        Returns:
            Tuple of (feedback_message, reward_summary) if successful, None otherwise.
        """
        # Find matching mission for this facility
        target_mission: Optional[Mission] = None
        for m in self.missions:
            if m.facility_id == facility_id:
                target_mission = m
                break

        if not target_mission:
            # Fallback generic facility boost
            return None

        # Apply stat increments to WorldState and PlayerState
        st = target_mission.stat_type

        if st == "oxygen":
            current_o2 = world_state.oxygen_reserve if world_state.oxygen_reserve is not None else 45.0
            world_state.oxygen_reserve = round(min(100.0, current_o2 + target_mission.stat_boost_amount), 1)
            world_state.habitat_pressure_pa = 101325.0
            world_state.habitat_temp_c = 21.5

        elif st == "water":
            current_w = world_state.water_reserve if world_state.water_reserve is not None else 40.0
            world_state.water_reserve = round(min(100.0, current_w + target_mission.stat_boost_amount), 1)

        elif st == "food":
            current_f = world_state.food_reserve if world_state.food_reserve is not None else 18.0
            world_state.food_reserve = round(min(60.0, current_f + target_mission.stat_boost_amount), 1)

        elif st == "solar":
            current_eff = world_state.solar_panel_efficiency if world_state.solar_panel_efficiency is not None else 65.0
            world_state.solar_panel_efficiency = round(min(98.0, current_eff + target_mission.stat_boost_amount), 1)
            world_state.dust_soiling_ratio = 0.0
            current_gen = world_state.power_generation_w if world_state.power_generation_w is not None else 2500.0
            world_state.power_generation_w = round(current_gen + 450.0, 1)

        elif st == "battery":
            current_soc = world_state.battery_soc if world_state.battery_soc is not None else 65.0
            world_state.battery_soc = round(min(100.0, current_soc + target_mission.stat_boost_amount), 1)
            current_lvl = world_state.battery_level_wh if world_state.battery_level_wh is not None else 3500.0
            world_state.battery_level_wh = round(min(5000.0, current_lvl + 1500.0), 1)
            world_state.battery_capacity_wh = 5000.0

        elif st == "health":
            player_state.health = 100.0
            world_state.habitat_pressure_pa = 101325.0
            world_state.habitat_temp_c = 22.0

        elif st == "hull":
            # Clear hull breach catastrophes if present
            world_state.catastrophes = [
                c for c in world_state.catastrophes
                if c.get("type") not in ("HABITAT_HULL_BREACH", "HULL_DECOMPRESSION")
            ]
            world_state.habitat_pressure_pa = 101325.0
            world_state.habitat_temp_c = 21.0

        elif st == "comms":
            world_state.elapsed_seconds += 20.0

        elif st == "forecast":
            # Reduce dust opacity through active filtration
            if world_state.environment.dust_opacity_tau is not None:
                world_state.environment.dust_opacity_tau = round(max(0.15, world_state.environment.dust_opacity_tau - 0.1), 2)

        # Mark completed and cycle active index if this was the highlighted mission
        target_mission.completed = True
        target_mission.times_completed += 1
        self.total_completed += 1

        if target_mission == self.current_mission:
            self.active_index = (self.active_index + 1) % len(self.missions)

        fb = f"MISSION COMPLETE: {target_mission.title.upper()}!"
        reward = f"REWARD EARNED: {target_mission.reward_desc}"
        return fb, reward

    def get_distance_to_current(self, player_pos: Tuple[float, float], base_facilities: Dict[str, Any]) -> float:
        """Calculate direct distance in meters to active target facility."""
        m = self.current_mission
        fac_info = base_facilities.get(m.facility_id)
        if not fac_info:
            return 0.0
        rect_t = fac_info.get("rect", (0, 0, 10, 10))
        cx = rect_t[0] + rect_t[2] / 2.0
        cy = rect_t[1] + rect_t[3] / 2.0
        dist_px = math.hypot(player_pos[0] - cx, player_pos[1] - cy)
        return dist_px * 0.25  # 0.25m per pixel
