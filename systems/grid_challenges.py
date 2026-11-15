"""MARS SURVIVAL — Grid Challenge Stations System.

Scatters 20 interactive 8-bit challenge stations across all habitat rooms,
outdoor solar arrays, satellite dishes, rover bay, reactor facilities, and
supply crates:
- Modes: "SWEET_SPOT" (precision timing) and "RAPID_TAP" (button-mashing frenzy)
- Pulsing retro 8-bit icons: [ ★ ] (Ready) / [ ✓ ] (Done)
- Proximity detection with floating [E] START CHALLENGE prompts
- Integrates with ChallengeMinigame and authoritative stat rewards.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any, Dict
import pygame
from config import WORLD_SCALE
from ui.font_manager import FontManager
from world.world_state import WorldState
from world.player_state import PlayerState


@dataclass
class GridStation:
    """An interactive challenge terminal located on the Mars base grid."""
    station_id: str
    name: str
    facility_name: str
    world_x: float
    world_y: float
    objective: str
    reward_desc: str
    stat_type: str
    stat_boost: float
    mode: str = "SWEET_SPOT"
    completed: bool = False


class GridChallengeSystem:
    """Manages active challenge stations across the entire Mars base grid."""

    def __init__(self) -> None:
        self.stations: List[GridStation] = [
            # 1. MOXIE Oxygen Room
            GridStation(
                station_id="st_moxie",
                name="MOXIE Solid Oxide Electrolyzer",
                facility_name="ECLSS Oxygen Room",
                world_x=890 * WORLD_SCALE,
                world_y=580 * WORLD_SCALE,
                objective="Regulate solid oxide electrolysis pressure chamber to produce O2.",
                reward_desc="+25.0 kg Oxygen Reserve",
                stat_type="oxygen",
                stat_boost=25.0,
                mode="PRESSURE_VALVE",
            ),
            # 2. Water Recycling
            GridStation(
                station_id="st_water_filter",
                name="Multi-Stage Catalytic Filter",
                facility_name="Water Recycling",
                world_x=710 * WORLD_SCALE,
                world_y=400 * WORLD_SCALE,
                objective="Balance catalytic filter pressure to flush perchlorate brine.",
                reward_desc="+35.0 kg Water Reserve",
                stat_type="water",
                stat_boost=35.0,
                mode="PRESSURE_VALVE",
            ),
            # 3. Mark Watney Space Potatoes (Greenhouse)
            GridStation(
                station_id="st_potato_bed",
                name="Mark Watney Space Potatoes",
                facility_name="Greenhouse Hydroponics",
                world_x=240 * WORLD_SCALE,
                world_y=560 * WORLD_SCALE,
                objective="Mash button rapidly to harvest fertile space potatoes!",
                reward_desc="+25.0 Days Space Potato Rations",
                stat_type="food",
                stat_boost=25.0,
                mode="RAPID_TAP",
            ),
            # 4. Spirulina Hydroponics Feeder
            GridStation(
                station_id="st_greenhouse",
                name="Hydroponic Seedling Feeder",
                facility_name="Food Greenhouse",
                world_x=320 * WORLD_SCALE,
                world_y=580 * WORLD_SCALE,
                objective="Target and strike illuminated seedling nodes to irrigate nutrients!",
                reward_desc="+15.0 Days Food Rations",
                stat_type="food",
                stat_boost=15.0,
                mode="TARGET_STRIKE",
            ),
            # 5. Solar Wiper Array West
            GridStation(
                station_id="st_solar_1",
                name="Primary Solar Array Sweep",
                facility_name="Solar Field West",
                world_x=80 * WORLD_SCALE,
                world_y=70 * WORLD_SCALE,
                objective="Target and strike basalt dust deposition clusters on solar panels!",
                reward_desc="+20% Solar Efficiency",
                stat_type="solar",
                stat_boost=20.0,
                mode="TARGET_STRIKE",
            ),
            # 6. Solar Wiper Array East
            GridStation(
                station_id="st_solar_2",
                name="Secondary Solar Array Sweep",
                facility_name="Solar Field East",
                world_x=170 * WORLD_SCALE,
                world_y=110 * WORLD_SCALE,
                objective="Input 5-step servo angle sequence to track midday sun vector!",
                reward_desc="+15% Solar Efficiency",
                stat_type="solar",
                stat_boost=15.0,
                mode="CIRCUIT_SEQUENCE",
            ),
            # 7. Contractor Tool Chest (Outdoor Supply Crate Near Solar Field)
            GridStation(
                station_id="st_crate_solar",
                name="Contractor Tool Chest",
                facility_name="North Exterior Trail",
                world_x=35 * WORLD_SCALE,
                world_y=200 * WORLD_SCALE,
                objective="Pry open rusted tool chest! Mash key to pop the lock!",
                reward_desc="+20% Wiper Speed & Spare Hardware",
                stat_type="solar",
                stat_boost=20.0,
                mode="RAPID_TAP",
            ),
            # 8. Main Turbine Bus Synchronizer
            GridStation(
                station_id="st_power_grid",
                name="Main Turbine Bus Synchronizer",
                facility_name="Power Generator",
                world_x=500 * WORLD_SCALE,
                world_y=550 * WORLD_SCALE,
                objective="Wire turbine phase load sequence to capacitor bank breakers!",
                reward_desc="+30% Battery SOC",
                stat_type="battery",
                stat_boost=30.0,
                mode="CIRCUIT_SEQUENCE",
            ),
            # 9. Quantum Muon Trap (Nuclear Reactor)
            GridStation(
                station_id="st_reactor",
                name="Quantum Muon Particle Deflector",
                facility_name="Nuclear Reactor Core",
                world_x=500 * WORLD_SCALE,
                world_y=70 * WORLD_SCALE,
                objective="Stabilize muon core coolant loop pressure before reactor scrams!",
                reward_desc="Base Grid Power Overclocked (+600W)",
                stat_type="power",
                stat_boost=600.0,
                mode="PRESSURE_VALVE",
            ),
            # 10. Automedic Bio-Scanner (Medbay)
            GridStation(
                station_id="st_medbay",
                name="Automedic Bio-Scanner",
                facility_name="Medical Bay",
                world_x=180 * WORLD_SCALE,
                world_y=410 * WORLD_SCALE,
                objective="Target and neutralize cellular anomalies in automedic bio-scanner!",
                reward_desc="100% Suit Health & Medical Vitals",
                stat_type="health",
                stat_boost=100.0,
                mode="TARGET_STRIKE",
            ),
            # 11. Robo-Arm Epic Fist Bump (Workshop)
            GridStation(
                station_id="st_workshop_arm",
                name="Robo-Arm Epic Fist Bump",
                facility_name="Robotics Workshop",
                world_x=680 * WORLD_SCALE,
                world_y=580 * WORLD_SCALE,
                objective="Program 5-step kinematic routing to execute robotic fist bump!",
                reward_desc="Robotics Overclocked (+25% Efficiency)",
                stat_type="hull",
                stat_boost=1.0,
                mode="CIRCUIT_SEQUENCE",
            ),
            # 12. Alien Phobos Radio Beacon (Giant Satellite Dish)
            GridStation(
                station_id="st_dish_exterior",
                name="Alien Phobos Radio Beacon",
                facility_name="Top-Left Giant Dish",
                world_x=290 * WORLD_SCALE,
                world_y=80 * WORLD_SCALE,
                objective="Tune carrier wave with [A]/[D] to match Phobos radio harmonic resonance!",
                reward_desc="Alien Signal Decoded: 'WE SEE YOU' (+250 Sci)",
                stat_type="science",
                stat_boost=250.0,
                mode="FREQUENCY_TUNE",
            ),
            # 13. Mission Telemetry Downlink (Comms Operations)
            GridStation(
                station_id="st_comms_lab",
                name="Mission Telemetry Downlink",
                facility_name="Comms Operations",
                world_x=340 * WORLD_SCALE,
                world_y=210 * WORLD_SCALE,
                objective="Tune deep space Earth transceiver frequency and lock downlink with [SPACE]!",
                reward_desc="High-Frequency Telemetry Active",
                stat_type="comms",
                stat_boost=1.0,
                mode="FREQUENCY_TUNE",
            ),
            # 14. Retro Asteroid Blaster (Command Holo-Globe)
            GridStation(
                station_id="st_holo_globe",
                name="Holo-Globe Asteroid Blaster",
                facility_name="Command Holo-Table",
                world_x=650 * WORLD_SCALE,
                world_y=230 * WORLD_SCALE,
                objective="Input tactical intercept trajectory vector to vaporize micro-meteorites!",
                reward_desc="Planetary Defense Shield Online (+200 Sci)",
                stat_type="science",
                stat_boost=200.0,
                mode="CIRCUIT_SEQUENCE",
            ),
            # 15. Rover RTG Turbo Jumpstart
            GridStation(
                station_id="st_rover_bay",
                name="Rover RTG Turbo Jumpstart",
                facility_name="Rover Staging Bay",
                world_x=105 * WORLD_SCALE,
                world_y=575 * WORLD_SCALE,
                objective="Crank 6-wheel rover RTG alternator to turbocharge drive motors!",
                reward_desc="Rover Turbo Active (+500 Science)",
                stat_type="science",
                stat_boost=500.0,
                mode="RAPID_TAP",
            ),
            # 16. Mystery Supply Crate Near Rover
            GridStation(
                station_id="st_crate_rover",
                name="NASA Supply Loot Crate",
                facility_name="Rover Bay Perimeter",
                world_x=255 * WORLD_SCALE,
                world_y=630 * WORLD_SCALE,
                objective="Pry open sealed supply crate! Mash key to pop the lid!",
                reward_desc="Loot Claimed: Freeze-Dried Space Ice Cream",
                stat_type="food",
                stat_boost=10.0,
                mode="RAPID_TAP",
            ),
            # 17. Atmospheric Thermal Kite (East Airpad)
            GridStation(
                station_id="st_east_airpad",
                name="Atmospheric Thermal Kite",
                facility_name="East Landing Pad",
                world_x=900 * WORLD_SCALE,
                world_y=260 * WORLD_SCALE,
                objective="Mash button to launch stratospheric sampling kite!",
                reward_desc="Upper Atmosphere Aerosol Logged (+180 Sci)",
                stat_type="science",
                stat_boost=180.0,
                mode="RAPID_TAP",
            ),
            # 18. Subsurface Brine Geyser (Water Room)
            GridStation(
                station_id="st_water_geyser",
                name="Subsurface Ice Geyser Valve",
                facility_name="Water Treatment Hub",
                world_x=760 * WORLD_SCALE,
                world_y=410 * WORLD_SCALE,
                objective="Pump high-pressure thermal ice geyser valve before greywater floods!",
                reward_desc="+40.0 kg Pure Glacial Water",
                stat_type="water",
                stat_boost=40.0,
                mode="PRESSURE_VALVE",
            ),
            # 19. Central Life-Support Master Console
            GridStation(
                station_id="st_rotunda_hub",
                name="Central Life-Support Console",
                facility_name="Central Rotunda Hub",
                world_x=500 * WORLD_SCALE,
                world_y=420 * WORLD_SCALE,
                objective="Input airlock master pressure routing sequence to cycle ECLSS!",
                reward_desc="Base ECLSS Fully Recalibrated",
                stat_type="oxygen",
                stat_boost=20.0,
                mode="CIRCUIT_SEQUENCE",
            ),
            # 20. Supply Crate Central Hallway
            GridStation(
                station_id="st_crate_hall",
                name="Airlock Storage Locker",
                facility_name="Central Rotunda Airlock",
                world_x=370 * WORLD_SCALE,
                world_y=370 * WORLD_SCALE,
                objective="Enter airlock digital cipher sequence to open storage locker!",
                reward_desc="Found 5x Emergency O2 Ampoules (+15 kg O2)",
                stat_type="oxygen",
                stat_boost=15.0,
                mode="CIRCUIT_SEQUENCE",
            ),
        ]
        self.anim_time: float = 0.0

    @property
    def total_completed(self) -> int:
        return sum(1 for s in self.stations if s.completed)

    def get_nearby_station(self, player_world_pos: pygame.Vector2, radius: float = 70.0) -> Optional[GridStation]:
        """Find closest station within interaction radius."""
        for s in self.stations:
            dist = math.hypot(player_world_pos.x - s.world_x, player_world_pos.y - s.world_y)
            if dist <= radius:
                return s
        return None

    def complete_station(self, station_id: str, world_state: WorldState, player_state: PlayerState) -> Optional[Tuple[str, str]]:
        """Apply challenge reward and boost stats."""
        st: Optional[GridStation] = None
        for s in self.stations:
            if s.station_id == station_id:
                st = s
                break

        if not st:
            return None

        st.completed = True

        # Apply stat boost
        if st.stat_type == "oxygen":
            cur = world_state.oxygen_reserve if world_state.oxygen_reserve is not None else 45.0
            world_state.oxygen_reserve = min(100.0, cur + st.stat_boost)
        elif st.stat_type == "water":
            cur = world_state.water_reserve if world_state.water_reserve is not None else 40.0
            world_state.water_reserve = min(100.0, cur + st.stat_boost)
        elif st.stat_type == "food":
            cur = world_state.food_reserve if world_state.food_reserve is not None else 18.0
            world_state.food_reserve = min(60.0, cur + st.stat_boost)
        elif st.stat_type == "solar":
            cur = world_state.solar_panel_efficiency if world_state.solar_panel_efficiency is not None else 65.0
            world_state.solar_panel_efficiency = min(100.0, cur + st.stat_boost)
        elif st.stat_type == "battery":
            cur = world_state.battery_soc if world_state.battery_soc is not None else 60.0
            world_state.battery_soc = min(100.0, cur + st.stat_boost)
        elif st.stat_type == "health":
            player_state.health = 100.0
        elif st.stat_type == "power":
            cur = world_state.power_generation_w if world_state.power_generation_w is not None else 2500.0
            world_state.power_generation_w = cur + st.stat_boost

        return (st.name, st.reward_desc)

    def update(self, dt: float) -> None:
        self.anim_time += dt

    def render(self, surface: pygame.Surface, camera: Any, player_world_pos: pygame.Vector2) -> None:
        """Render retro 8-bit pulsing challenge markers [ ★ ] on the base grid."""
        font_marker = FontManager.get(11, bold=True)
        pulse = 0.5 + 0.5 * math.sin(self.anim_time * 6.0)

        for s in self.stations:
            sp = camera.world_to_screen(s.world_x, s.world_y)
            if not (-30 <= sp.x <= surface.get_width() + 30 and -30 <= sp.y <= surface.get_height() + 30):
                continue

            dist = math.hypot(player_world_pos.x - s.world_x, player_world_pos.y - s.world_y)
            is_near = (dist <= 70.0)

            cx = int(sp.x)
            cy = int(sp.y)

            # 8-bit marker icon: [ ★ ] or [ ✓ ]
            if s.completed:
                badge_text = "[ ✓ ]"
                border_col = (0, 255, 120)
                bg_col = (8, 20, 12)
                text_col = (0, 255, 120)
            else:
                badge_text = "[ ★ ]"
                border_col = (255, int(190 + pulse * 65), 0)
                bg_col = (22, 18, 8)
                text_col = (255, 220, 0)

            surf_txt = font_marker.render(badge_text, True, text_col)
            w, h = surf_txt.get_width() + 6, surf_txt.get_height() + 2
            badge = pygame.Surface((w, h))
            badge.fill(bg_col)
            pygame.draw.rect(badge, border_col, (0, 0, w, h), width=1)
            badge.blit(surf_txt, (3, 1))

            surface.blit(badge, (cx - w // 2, cy - h // 2))

            # Proximity prompt: "[E] CHALLENGE"
            if is_near and not s.completed:
                p_font = FontManager.get(10, bold=True)
                mode_tag = "MASH" if s.mode == "RAPID_TAP" else "TIMING"
                p_txt = p_font.render(f"[E] {s.name.upper()} ({mode_tag})", True, (255, 255, 255))
                pw, ph = p_txt.get_width() + 8, p_txt.get_height() + 2
                p_box = pygame.Surface((pw, ph))
                p_box.fill((12, 16, 24))
                pygame.draw.rect(p_box, (0, 229, 255), (0, 0, pw, ph), width=1)
                p_box.blit(p_txt, (4, 1))
                surface.blit(p_box, (cx - pw // 2, cy - 24))
