"""MARS SURVIVAL — Procedural Catastrophe Director & Emergency Manager.

Manages randomized environmental disasters and base emergencies:
1. Procedural Stochastic Timer: Randomly injects extreme Martian catastrophes
   (Dust Storm Blackouts, Marsquakes, Hull Breaches, Solar Particle Flares, Cryo-Freezes).
2. Emergency Evacuation: Forces all station NPCs to shout warnings and retreat inside
   the central habitat rotunda shelter.
3. Challenge Invalidation: Damages base systems and resets facility/grid challenges.
4. Health Restoration Loop: Tracks overall Space Health (0-100%). Players must redo
   and solve damaged challenge stations to restore base integrity to 100%.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import random
from typing import List, Dict, Any, Optional
import pygame

from world.world_state import WorldState
from systems.audio_synthesizer import SoundSynthesizer
from systems.npc_system import NPCSystem
from systems.grid_challenges import GridChallengeSystem
from systems.mission_system import MissionSystem
from systems.particle_fx import ParticleFXSystem
from systems.floating_text import FloatingTextSystem


class CatastropheDirector:
    """Orchestrates random emergent catastrophes, NPC sheltering, and repair loops."""

    CATASTROPHE_CATALOG = [
        {
            "type": "GLOBAL_DUST_STORM",
            "name": "Global Ferric Dust Storm",
            "description": "Massive atmospheric dust veil (tau=3.5). Heavy ferric grit shear, PV failure, battery drain.",
            "health_drop": 35.0,
            "duration": 15.0,
            "affected_stats": ["solar", "power", "food", "battery"],
            "ambient_tau": 3.4,
        },
        {
            "type": "SEVERE_MARSQUAKE",
            "name": "Magnitude 5.4 Jezero Marsquake",
            "description": "Tectonic fault rupture! Violently shaking habitat structures, severed coolant lines.",
            "health_drop": 25.0,
            "duration": 15.0,
            "affected_stats": ["hull", "power", "water", "oxygen"],
            "ambient_tau": 1.2,
        },
        {
            "type": "HABITAT_HULL_BREACH",
            "name": "Habitat Hull Breach Decompression",
            "description": "Airlock seal rupture! Rapid atmospheric depressurization and oxygen venting.",
            "health_drop": 20.0,
            "duration": 15.0,
            "affected_stats": ["oxygen", "hull", "health", "battery"],
            "ambient_tau": 0.9,
        },
        {
            "type": "SOLAR_PARTICLE_EVENT",
            "name": "Solar Cosmic Particle Flare",
            "description": "Coronal mass ejection radiation surge! High electronic static, transceiver disruption.",
            "health_drop": 30.0,
            "duration": 15.0,
            "affected_stats": ["comms", "battery", "power", "science"],
            "ambient_tau": 1.5,
        },
        {
            "type": "CRYOGENIC_FLASH_FREEZE",
            "name": "Polar Cryogenic Flash Freeze",
            "description": "Barometric flash freeze (-118 C). Water recyclers frozen, thermal regulation failure.",
            "health_drop": 35.0,
            "duration": 15.0,
            "affected_stats": ["water", "food", "battery", "power"],
            "ambient_tau": 0.8,
        },
    ]

    def __init__(
        self,
        world_state: WorldState,
        audio: SoundSynthesizer,
        npc_system: NPCSystem,
        grid_challenges: GridChallengeSystem,
        mission_system: MissionSystem,
        particle_fx: ParticleFXSystem,
        floating_text: FloatingTextSystem,
        sync: Optional[Any] = None,
        initial_delay: float = 300.0,  # 5 minutes
    ) -> None:
        self.world_state = world_state
        self.audio = audio
        self.npc_system = npc_system
        self.grid_challenges = grid_challenges
        self.mission_system = mission_system
        self.particle_fx = particle_fx
        self.floating_text = floating_text
        self.sync = sync

        # Random catastrophe interval timer (seconds) — 5 minutes (300s)
        self.random_timer: float = initial_delay
        self.is_emergency: bool = False
        self.current_catastrophe_title: str = ""

        # Emergency inactivity failure countdown (1.30 minutes / 90 seconds)
        self.collapse_countdown: float = 90.0
        self.is_game_over: bool = False
        self.game_over_reason: str = ""

    def notify_repair_progress(self) -> None:
        """Called when a challenge station or facility is repaired. Grants bonus buffer time during crisis."""
        if self.is_emergency:
            self.collapse_countdown = min(90.0, self.collapse_countdown + 30.0)
            self.world_state.collapse_countdown = self.collapse_countdown

    def restart(self, player_pos: pygame.Vector2) -> None:
        """Revive crew and restart simulation after mission failure."""
        self.is_game_over = False
        self.is_emergency = False
        self.collapse_countdown = 90.0
        self.world_state.collapse_countdown = 90.0
        self.world_state.station_health = 100.0
        self.world_state.catastrophes.clear()
        if self.world_state.environment.dust_opacity_tau is not None:
            self.world_state.environment.dust_opacity_tau = 0.35
        self.npc_system.resolve_emergency()
        self.random_timer = random.uniform(280.0, 320.0)
        self.audio.play("success")
        self.particle_fx.spawn_celebration_burst(player_pos.x, player_pos.y, particle_type="spark")
        self.floating_text.spawn(
            "★ EXPEDITION RESTORED — ALL SYSTEMS NOMINAL ★",
            player_pos.x,
            player_pos.y - 50,
            color=(0, 255, 180),
            big=True,
        )

    def update(self, dt: float, player_pos: pygame.Vector2) -> None:
        """Advance disaster simulation, countdown 15s duration, check health restoration, and trigger 5-minute random events."""
        if self.is_game_over:
            return

        # 1. Countdown active catastrophe duration (15 seconds)
        if self.world_state.catastrophes:
            active_cats = []
            for c in self.world_state.catastrophes:
                dur = c.get("duration", 15.0) - dt
                c["duration"] = dur
                if dur > 0:
                    active_cats.append(c)
                else:
                    # Catastrophe finished its 15s duration
                    if self.world_state.environment.dust_opacity_tau is not None and self.world_state.environment.dust_opacity_tau > 1.5:
                        self.world_state.environment.dust_opacity_tau = 0.45
                    self.floating_text.spawn(
                        "Catastrophe hazard (15s) ended! Repair facilities to restore 100% Space Health!",
                        player_pos.x,
                        player_pos.y - 35,
                        color=(255, 200, 80),
                        big=False,
                    )
            self.world_state.catastrophes = active_cats

        # 2. Check emergency status & Space Health recovery
        has_active_cat = len(self.world_state.catastrophes) > 0 or self.world_state.station_health < 100.0

        if has_active_cat:
            self.is_emergency = True

            # Countdown 90-second (1.30 minutes) inactivity failure timer to take action and repair
            self.collapse_countdown -= dt
            self.world_state.collapse_countdown = max(0.0, self.collapse_countdown)

            if self.collapse_countdown <= 0.0:
                self.collapse_countdown = 0.0
                self.is_game_over = True
                self.world_state.station_health = 0.0
                self.game_over_reason = (
                    f"Catastrophe '{self.current_catastrophe_title or 'Disaster'}' left unaddressed for 1.30 minutes (90s)! "
                    "Habitat life support depleted and all crew perished on Mars."
                )
                self.audio.play("fail")
                return

            # Check if player has fully repaired the space back to 100%
            if self.world_state.station_health >= 100.0:
                self.world_state.station_health = 100.0
                self.world_state.catastrophes.clear()
                self.is_emergency = False
                self.collapse_countdown = 90.0
                self.world_state.collapse_countdown = 90.0

                # Resolution celebration!
                self.audio.play("success")
                self.particle_fx.spawn_celebration_burst(player_pos.x, player_pos.y, particle_type="spark")
                self.floating_text.spawn(
                    "★ 100% SPACE HEALTH RESTORED! HABITAT NOMINAL! ★",
                    player_pos.x,
                    player_pos.y - 50,
                    color=(0, 255, 180),
                    big=True,
                )

                # Signal NPCs to return to their normal station posts
                self.npc_system.resolve_emergency()

                # Schedule next randomized catastrophe after 5 minutes (280 - 320s)
                self.random_timer = random.uniform(280.0, 320.0)
            else:
                # Emergency still active, ensure NPCs are sheltering
                for npc in self.npc_system.npcs:
                    if npc.state == "NOMINAL":
                        npc.trigger_flee(self.current_catastrophe_title or "Catastrophe")

        else:
            self.is_emergency = False
            self.collapse_countdown = 60.0
            self.world_state.collapse_countdown = 60.0
            # Nominal calm period: count down 5 minutes to next random disaster
            self.random_timer -= dt
            if self.random_timer <= 0.0:
                self.trigger_random_catastrophe(player_pos)
                # Next catastrophe after 5 minutes
                self.random_timer = random.uniform(280.0, 320.0)

    def trigger_random_catastrophe(self, player_pos: Optional[pygame.Vector2] = None) -> Dict[str, Any]:
        """Procedurally choose and unleash a random catastrophe on Jezero base."""
        cat_def = random.choice(self.CATASTROPHE_CATALOG)
        return self.trigger_catastrophe(cat_def["type"], player_pos)

    def trigger_catastrophe(self, cat_type: str, player_pos: Optional[pygame.Vector2] = None) -> Dict[str, Any]:
        """Inject a specific catastrophe, damage space health, reset challenges, and evacuate NPCs."""
        match = next((c for c in self.CATASTROPHE_CATALOG if c["type"] == cat_type), self.CATASTROPHE_CATALOG[0])

        cat_dict = {
            "type": match["type"],
            "name": match["name"],
            "description": match["description"],
            "duration": match["duration"],
            "severity": 0.85,
        }

        # 1. Register in WorldState
        self.world_state.catastrophes = [cat_dict]
        self.current_catastrophe_title = match["name"]
        self.collapse_countdown = 90.0
        self.world_state.collapse_countdown = 90.0
        self.is_game_over = False
        self.is_emergency = True

        # Synchronize authoritative scientific disaster with MARS-EIS backend
        if self.sync:
            try:
                self.sync.trigger_catastrophe(match["type"], severity=0.85)
            except Exception:
                pass

        # 2. Damage Space / Station Health
        drop_health = match["health_drop"]
        self.world_state.station_health = drop_health

        # Dynamic environmental adjustments
        if match.get("ambient_tau") and self.world_state.environment.dust_opacity_tau is not None:
            self.world_state.environment.dust_opacity_tau = max(self.world_state.environment.dust_opacity_tau, match["ambient_tau"])

        # 3. Reset Grid Challenge Stations and Facility Missions
        reset_stations = self.grid_challenges.reset_for_catastrophe(match.get("affected_stats"))
        reset_missions = self.mission_system.reset_for_catastrophe()

        # 4. Trigger Audio Alarm & Visual Juice
        self.audio.play("alarm")

        # 5. Order all Crew NPCs to flee inside the habitat shelter
        self.npc_system.trigger_emergency(match["name"])

        # 6. Spawn High-Priority Emergency Floating Text
        px = player_pos.x if player_pos else 1000.0
        py = player_pos.y if player_pos else 800.0
        self.particle_fx.spawn_celebration_burst(px, py, particle_type="spark")
        self.floating_text.spawn(
            f"⚠ EMERGENCY: {match['name'].upper()}!",
            px,
            py - 55,
            color=(255, 60, 60),
            big=True,
        )
        self.floating_text.spawn(
            f"Space Health at {drop_health:.0f}%! NPCs evacuating! Redo challenges for 100% health!",
            px,
            py - 30,
            color=(255, 200, 60),
            big=False,
        )

        return cat_dict
