"""DUSTFALL — Pygame Simulation Client Configuration.

Centralized configuration for display settings, backend API parameters,
world dimensions, player dynamics, facility landmark coordinates, and theme styling.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import Dict, Any, Tuple

# ==============================================================================
# DISPLAY & ENGINE SETTINGS
# ==============================================================================
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 720
WINDOW_TITLE: str = "DUSTFALL — MARS-EIS Environmental Interface"
TARGET_FPS: int = 60

# ==============================================================================
# MARS-EIS SIMULATION BACKEND CONFIGURATION
# ==============================================================================
BACKEND_CONFIG: Dict[str, Any] = {
    "base_url": "http://127.0.0.1:8000",
    "ws_url": "ws://127.0.0.1:8000/ws/telemetry",  # Real-time WebSocket live feed
    "sync_interval_seconds": 2.0,       # Polling interval for world state
    "request_timeout_seconds": 5.0,     # HTTP connection timeout
    "reconnect_interval_seconds": 3.0,  # Delay between reconnect attempts
    "delta_simulation_seconds": 10.0,   # Seconds to advance simulation per step
    "automatic_advance": True,          # Periodically advance simulation clock
}

# ==============================================================================
# WORLD & ENVIRONMENT CONFIGURATION
# ==============================================================================
BACKGROUND_PATH: str = "assets/backgrounds/mars_base_background.jpg"
# Original background resolution is 1024 x 682.
# WORLD_SCALE preserves exact aspect ratio while expanding playable world coordinates.
WORLD_SCALE: float = 2.0
BASE_WIDTH: int = 1024
BASE_HEIGHT: int = 682
WORLD_WIDTH: int = int(BASE_WIDTH * WORLD_SCALE)    # 2048 px
WORLD_HEIGHT: int = int(BASE_HEIGHT * WORLD_SCALE)  # 1364 px

# Planetary coordinate mapping: 1 pixel in world space = ~0.25 meters
METERS_PER_PIXEL: float = 0.25

# Default spawn location for player in world coordinates (central rotunda hub)
DEFAULT_SPAWN_X: float = 500.0 * WORLD_SCALE  # 1000.0 px
DEFAULT_SPAWN_Y: float = 420.0 * WORLD_SCALE  # 840.0 px

# Base facility landmark coordinates mapped to user's Mars base background
BASE_FACILITIES = {
    "central_hub": {
        "name": "Central Rotunda & Airlock",
        "rect": (int(450 * WORLD_SCALE), int(370 * WORLD_SCALE), int(100 * WORLD_SCALE), int(100 * WORLD_SCALE)),
        "interaction_action": "SEAL_HULL_BREACH",
        "label": "AIRLOCK HUB",
        "challenge_mode": "CIRCUIT_SEQUENCE",
    },
    "solar_farm": {
        "name": "Photovoltaic Solar Farm",
        "rect": (int(40 * WORLD_SCALE), int(30 * WORLD_SCALE), int(200 * WORLD_SCALE), int(140 * WORLD_SCALE)),
        "interaction_action": "CLEAN_PANELS",
        "label": "SOLAR ARRAYS",
        "challenge_mode": "TARGET_STRIKE",
    },
    "nuclear_reactor": {
        "name": "Fission Surface Power Reactor",
        "rect": (int(430 * WORLD_SCALE), int(20 * WORLD_SCALE), int(140 * WORLD_SCALE), int(100 * WORLD_SCALE)),
        "interaction_action": "ROUTE_EMERGENCY_POWER",
        "label": "NUCLEAR REACTOR",
        "challenge_mode": "PRESSURE_VALVE",
    },
    "comm_center": {
        "name": "Deep Space Telemetry & Comms",
        "rect": (int(260 * WORLD_SCALE), int(160 * WORLD_SCALE), int(140 * WORLD_SCALE), int(110 * WORLD_SCALE)),
        "interaction_action": "ROUTE_EMERGENCY_POWER",
        "label": "COMMUNICATIONS",
        "challenge_mode": "FREQUENCY_TUNE",
    },
    "command_lab": {
        "name": "Mission Operations & Holo-Globe",
        "rect": (int(580 * WORLD_SCALE), int(160 * WORLD_SCALE), int(160 * WORLD_SCALE), int(120 * WORLD_SCALE)),
        "interaction_action": "SEAL_HULL_BREACH",
        "label": "COMMAND LAB",
        "challenge_mode": "CIRCUIT_SEQUENCE",
    },
    "medbay": {
        "name": "Medical Bay & Bio-Scanner",
        "rect": (int(110 * WORLD_SCALE), int(350 * WORLD_SCALE), int(140 * WORLD_SCALE), int(130 * WORLD_SCALE)),
        "interaction_action": "SEAL_HULL_BREACH",
        "label": "MEDBAY",
        "challenge_mode": "TARGET_STRIKE",
    },
    "water_recycling": {
        "name": "Water Recycling & Purification",
        "rect": (int(650 * WORLD_SCALE), int(340 * WORLD_SCALE), int(150 * WORLD_SCALE), int(130 * WORLD_SCALE)),
        "interaction_action": "EXTRACT_ICE",
        "label": "WATER RECYCLING",
        "challenge_mode": "PRESSURE_VALVE",
    },
    "greenhouse": {
        "name": "Hydroponic Greenhouse",
        "rect": (int(200 * WORLD_SCALE), int(530 * WORLD_SCALE), int(170 * WORLD_SCALE), int(120 * WORLD_SCALE)),
        "interaction_action": "EXCAVATE",
        "label": "FOOD GREENHOUSE",
        "challenge_mode": "RAPID_TAP",
    },
    "power_generator": {
        "name": "Main Electrical Transformer & Grid",
        "rect": (int(420 * WORLD_SCALE), int(490 * WORLD_SCALE), int(160 * WORLD_SCALE), int(120 * WORLD_SCALE)),
        "interaction_action": "ROUTE_EMERGENCY_POWER",
        "label": "POWER GENERATOR",
        "challenge_mode": "CIRCUIT_SEQUENCE",
    },
    "engineering_workshop": {
        "name": "Robotics & Fabrication Workshop",
        "rect": (int(600 * WORLD_SCALE), int(530 * WORLD_SCALE), int(160 * WORLD_SCALE), int(110 * WORLD_SCALE)),
        "interaction_action": "DEPLOY_STORM_SHIELD",
        "label": "WORKSHOP",
        "challenge_mode": "CIRCUIT_SEQUENCE",
    },
    "oxygen_plant": {
        "name": "ECLSS Oxygen Generation Plant",
        "rect": (int(840 * WORLD_SCALE), int(530 * WORLD_SCALE), int(130 * WORLD_SCALE), int(120 * WORLD_SCALE)),
        "interaction_action": "SEAL_HULL_BREACH",
        "label": "O2 GENERATION",
        "challenge_mode": "PRESSURE_VALVE",
    },
    "rover_bay": {
        "name": "Exploration Rover Staging Bay",
        "rect": (int(50 * WORLD_SCALE), int(520 * WORLD_SCALE), int(140 * WORLD_SCALE), int(120 * WORLD_SCALE)),
        "interaction_action": "ROVER_DRIVE",
        "label": "ROVER BAY",
        "challenge_mode": "RAPID_TAP",
    },
}

# ==============================================================================
# PLAYER MOVEMENT & ANIMATION
# ==============================================================================
PLAYER_SPEED: float = 230.0  # Pixels per second
PLAYER_RADIUS: float = 16.0  # Visual radius for collision boundary readiness
MOVEMENT_SYNC_INTERVAL: float = 1.0  # Seconds of movement before sending batch telemetry
MOVEMENT_MIN_DISTANCE_M: float = 2.0  # Minimum meters before reporting movement

# Required animation names
ANIMATION_NAMES = [
    "idle",
    "walk_down",
    "walk_up",
    "walk_left",
    "walk_right",
]

# Astronaut crew members from uploaded sprite sheet
# Commander Suso (Sprite 1) is the sole playable field commander.
# Amal (Sprite 3, Comms), Gowri (Sprite 2, Research Fellow), and Christy (Sprite 4, Engineer) are living station NPCs.
CREW_MEMBERS = {
    1: {"name": "Commander Suso", "role": "Mission Commander", "sprite_id": 1},
    2: {"name": "Gowri", "role": "Research Fellow (Astrobiology)", "sprite_id": 2},
    3: {"name": "Amal", "role": "Communications Specialist", "sprite_id": 3},
    4: {"name": "Christy", "role": "Chief Engineer", "sprite_id": 4},
}

# ==============================================================================
# COLOR PALETTE & UI STYLING
# ==============================================================================
COLOR_BG: Tuple[int, int, int] = (15, 12, 18)
COLOR_PANEL_BG: Tuple[int, int, int, int] = (20, 24, 34, 215)
COLOR_PANEL_BORDER: Tuple[int, int, int] = (45, 55, 75)
COLOR_PANEL_BORDER_ACCENT: Tuple[int, int, int] = (217, 83, 43)

# Telemetry status colors
COLOR_NOMINAL: Tuple[int, int, int] = (46, 204, 113)
COLOR_WARNING: Tuple[int, int, int] = (243, 156, 18)
COLOR_CRITICAL: Tuple[int, int, int] = (231, 76, 60)
COLOR_INFO: Tuple[int, int, int] = (52, 152, 219)
COLOR_ACCENT_MARS: Tuple[int, int, int] = (217, 83, 43)

# Typography
COLOR_TEXT_PRIMARY: Tuple[int, int, int] = (240, 243, 246)
COLOR_TEXT_SECONDARY: Tuple[int, int, int] = (156, 172, 192)
COLOR_TEXT_MUTED: Tuple[int, int, int] = (100, 116, 139)
COLOR_TEXT_HIGHLIGHT: Tuple[int, int, int] = (255, 204, 0)

# ==============================================================================
# AUTHOR CREDITS
# ==============================================================================
CREDIT_INFO = {
    "author": "Lunarmist-byte",
    "github": "https://github.com/Lunarmist-byte",
    "linkedin": "https://www.linkedin.com/in/amal-s-kumar-ba69a1290/",
    "text": "Made by Lunarmist-byte",
}
