# DUSTFALL — Mars Environmental Intelligence & Survival Interface
Client for the MARS-EIS Planetary Environmental Simulation Engine

DUSTFALL is a 2D top-down simulation client and survival game built with Python and Pygame. It couples directly with MARS-EIS (Mars Environmental Intelligence & Simulation Engine), an authoritative scientific backend simulating Martian planetary conditions, atmospheric dynamics, optical depth, solar irradiance, power grids, and ECLSS life-support infrastructure.

---

## Made for NASA Space Apps Kochi

Developed for the NASA Space Apps Challenge (Kochi Local Event).

---

## 1. System Architecture

The project is structured into two decoupled processes communicating over local networking:

```
+--------------------------------------------------------------------+
|                         DUSTFALL CLIENT                            |
|  - 60 FPS Delta-time Game Loop (main.py)                           |
|  - 2D Viewport & Camera Controller (systems/camera.py)             |
|  - Planetary Surface & Habitat Collision Mask (scenes/mars_base.py)|
|  - Multi-tier Ferric Dust Particle FX (systems/particle_fx.py)     |
|  - Crew NPC System & Rotunda Sheltering (systems/npc_system.py)    |
|  - Procedural Catastrophe Director (systems/catastrophe_manager.py)|
|  - 20 Grid Challenge Stations & Minigames (systems/grid_challenges)|
|  - Cinematic Video Player & NASA Hyperlink (scenes/intro_scene.py) |
+---------------------------------+----------------------------------+
                                  |
                HTTP REST (8000)  |  WebSocket Feed (8000)
                Telemetry & Evt   |  1.0 Hz Live State
                                  v
+--------------------------------------------------------------------+
|                        MARS-EIS ENGINE                             |
|  - Atmospheric Dynamics (Pressure, Temp, Density)                  |
|  - Solar Radiation & Optical Depth (tau) Modeling                  |
|  - Fission & Photovoltaic Power Grid Simulation                    |
|  - ECLSS Life Support & Consumable Depletion Tracking              |
|  - NASA Curiosity / Perseverance In-Situ Assimilation              |
+--------------------------------------------------------------------+
```

### Architectural Separation
* **DUSTFALL (Client Layer):** Handles user input, rendering, audio synthesis, camera positioning, NPC autonomous pathfinding, and interactive challenge minigames. Does not compute Mars physics locally; consumes authoritative state from the backend.
* **MARS-EIS (Authoritative Engine):** Simulates planetary atmospheric thermodynamics, diurnal solar radiation, dust lifting flux, and habitat infrastructure loads. Exposes state through FastAPI REST and WebSocket endpoints.

---

## 2. Directory Structure

```text
pygame/
|-- main.py                    # Client entry point and main display loop
|-- launch.py                  # Integrated full-stack launcher (backend daemon + client)
|-- start.sh                   # Linux/macOS full-stack startup script
|-- start.ps1                  # Windows PowerShell full-stack startup script
|-- run.sh                     # Bash launcher alias
|-- run.ps1                    # PowerShell launcher alias
|-- config.py                  # Centralized client configuration, display, and theme
|-- requirements.txt           # Python dependencies
|-- README.md                  # Technical documentation
|
|-- backend/                   # Network synchronization layer
|   |-- api_client.py          # HTTP client for REST API endpoints
|   |-- live_feed.py           # WebSocket client for 1.0 Hz telemetry streaming
|   |-- simulation_sync.py     # Dual-channel synchronizer with automatic failover
|   `-- backend_config.py      # Network endpoints, timeouts, and ports
|
|-- scenes/                    # Scene graphs and renderers
|   |-- intro_scene.py         # OpenCV video decoder with Mariner 9 NASA popup
|   |-- main_scene.py          # Primary world manager, event bus, and render pass
|   `-- mars_base.py           # Base layout, collision mask, and facility definitions
|
|-- systems/                   # Game mechanics and physics simulation helpers
|   |-- catastrophe_manager.py # Procedural disaster engine and space health manager
|   |-- npc_system.py          # Crew NPC behavior, sheltering, and autonomous wander
|   |-- grid_challenges.py     # 20 repair challenge stations and 5 gameplay modes
|   |-- mission_system.py      # Facility mission progression and reward pipeline
|   |-- particle_fx.py         # Multi-tiered ferric dust, thrusters, and sparks
|   |-- audio_synthesizer.py   # Pure-Python procedural sound effects synthesizer
|   |-- camera.py              # Clamped 2D tracking camera
|   `-- input_handler.py       # Input normalization, sprint, and action triggers
|
|-- player/                    # Astronaut entity
|   |-- player.py              # Player composition and state management
|   |-- movement.py            # Normalized vector movement and regolith telemetry
|   `-- animation.py           # Directional sprite selection and flipping
|
|-- world/                     # State containers
|   |-- world_state.py         # Thread-safe simulation snapshot container
|   |-- environmental_state.py # Formatted Mars environmental telemetry
|   `-- player_state.py        # Client-side player coordinates and inventory
|
|-- ui/                        # User interface
|   |-- hud.py                 # Telemetry HUD, status meters, and help overlay
|   |-- situation_modal.py     # Interactive emergency injector and catastrophe panel
|   |-- challenge_minigame.py  # Modal UI for active station minigames
|   `-- font_manager.py        # Cached typography engine
|
|-- assets/                    # Media assets
|   |-- backgrounds/           # Mars base environment art and collision masks
|   |-- characters/            # Crew member sprite sheets and avatar portraits
|   `-- intro/                 # Intro video, WAV audio, and Mariner 9 graphics
|
`-- tests/
    `-- test_client.py         # 20-unit automated test suite
```

---

## 3. Core Mechanics

### Procedural Catastrophe Director
Catastrophes trigger randomly every 5 minutes (randomized between 280 and 320 seconds).
* **Hazard Types:**
  1. Global Ferric Dust Storm (Atmospheric opacity tau increases to 3.5; severe PV attenuation)
  2. Magnitude 5.4 Jezero Marsquake (Structural vibration, severed coolant lines)
  3. Habitat Hull Breach Decompression (Airlock seal loss, rapid O2 venting)
  4. Solar Cosmic Particle Flare (High electronic static, communication blackouts)
  5. Polar Cryogenic Flash Freeze (Thermal regulation drop to -118 C)
* **Hazard Lifespan:** Active catastrophe hazard conditions strictly last 15.0 seconds.
* **Integrity Drop & Repairs:** Space Health drops to between 20% and 35%. Completing grid challenge stations restores +20% health; completing facility missions restores +25% health. Reaching 100% health clears the crisis.
* **Failure Condition:** If 90 seconds (1.30 minutes) elapse without reaching 100% Space Health, the habitat collapses, ending the expedition with an arcade mission-failure screen and a one-key revival mechanism ([R]).

### Living Crew NPC System
Four distinct crew members inhabit Jezero base:
* **Commander Suso (Sprite 1):** Mission Commander & Systems Architect (Active Player)
* **Amal (Sprite 3):** Communications Specialist (Stationed at Deep Space Comms)
* **Gowri (Sprite 2):** Research Fellow in Astrobiology (Stationed at Hydroponic Greenhouse)
* **Christy (Sprite 4):** Chief Robotics Engineer (Stationed at Engineering Workshop)

During calm periods, NPCs occupy their assigned stations with proximity dialogue ([E]). During an emergency:
* NPCs are immediately placed inside the Central Rotunda & Airlock habitat shelter.
* Inside the shelter, NPCs autonomously wander between random waypoints within the rotunda perimeter, running walking animations and displaying emergency status speech bubbles.
* Once 100% Space Health is restored, NPCs celebrate and walk along corridor routes back to their nominal stations.

### 20 Grid Challenge Stations & 5 Gameplay Modes
1. **Circuit Wiring Sequence (CIRCUIT_SEQUENCE):** 5-step arrow input matching illuminated cues.
2. **Pressure Chamber Regulation (PRESSURE_VALVE):** Pulsed input maintaining pressure inside a fluctuating safety band.
3. **Oscilloscope Wave Tuning (FREQUENCY_TUNE):** Carrier frequency adjustment matching target radio waveforms.
4. **Radar Reticle Strike (TARGET_STRIKE):** Sweeping crosshairs striking target nodes.
5. **Turbo Charge Mash (RAPID_TAP):** Rapid cadence tapping to reach 100% capacitor charge.

### Cinematic Video Intro & NASA Mariner 9 Integration
At startup, an intro cinematic plays with audio synchronization:
* Monotonic frame decoding avoids OpenCV keyframe-seeking jitter.
* Strictly between 15.00s and 20.00s, an interactive NASA Mariner 9 spacecraft hologram appears at the bottom-right of the screen with no obstructing background box.
* Clicking the satellite or pressing [ENTER] opens the official NASA Mariner 9 Mission Archive in the default web browser:
  https://science.nasa.gov/mission/mariner-9/
* Pressing [SPACE] skips the intro directly to gameplay.

---

## 4. Installation and Setup

### Prerequisites
* Python 3.10, 3.11, or 3.12
* Git
* Sound card / audio output device supported by SDL

### One-Command Full Stack Startup

#### Windows (PowerShell)
```powershell
.\start.ps1
```
Optional flags:
```powershell
.\start.ps1 -SkipIntro     # Skip video intro directly to gameplay
.\start.ps1 -Port 8000     # Custom port for MARS-EIS backend
```

#### Linux / macOS / Git Bash
```bash
chmod +x start.sh
./start.sh
```
Optional flags:
```bash
./start.sh --skip-intro    # Skip video intro directly to gameplay
./start.sh --port=8000     # Custom port for MARS-EIS backend
```

The script automatically:
1. Clones the backend repository (https://github.com/Lunarmist-byte/drsosospaceadventure.git) if not present.
2. Installs dependencies from `requirements.txt`.
3. Starts the backend on `http://127.0.0.1:8000` in the background.
4. Launches the DUSTFALL Pygame client.
5. Terminates the backend background process upon client exit.

---

## 5. Manual Setup

If you prefer running services manually in separate terminals:

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the MARS-EIS Backend
Clone and start the engine:
```bash
git clone https://github.com/Lunarmist-byte/drsosospaceadventure.git ssosalien
cd ssosalien
pip install -r requirements.txt
python main.py --serve-api --port 8000
```

### Step 3: Launch DUSTFALL
In the pygame directory:
```bash
python main.py
```
Or use the Python launcher directly (which auto-spawns an internal backend worker if port 8000 is free):
```bash
python launch.py
```

---

## 6. Controls Reference

| Input | Function |
|---|---|
| W, A, S, D / Arrow Keys | 8-Directional Normalized Astronaut Movement |
| Shift (Hold) | EVA Sprint / Cold Gas Thruster Boost (1.45x speed) |
| Space | Low-Gravity Martian Hop (0.38g float arc and dust landing ring) |
| E | Interact with Crew NPCs / Calibrate Grid Challenge Stations |
| C | Clean Solar Panels (CLEAN_PANELS action + clears dust opacity) |
| X | Subsurface Regolith Core Excavation (EXCAVATE action) |
| 1, 2, 3, 4, 5 | Trigger Catastrophe on Demand (Dust Storm, Marsquake, Hull Breach, Solar Flare, Freeze) |
| H | Toggle Minimalist 8-Bit Ribbon HUD vs Detailed Telemetry |
| T / F4 | Open MARS-EIS Emergency Situation Injector Modal |
| F1 | Open System Manual & Shortcuts Overlay |
| F2 | Force Immediate Network Reconnect to MARS-EIS Backend |
| F3 | Toggle Debug Frame Rate and Telemetry Overlay |
| F5 | Toggle WebSocket Live Stream Telemetry Inspector |
| Esc | Close Active Modal / Exit Station Minigame / Quit Application |

---

## 7. Verification & Automated Test Suite

A comprehensive 20-unit test suite covers simulation synchronization, coordinate clamping, camera math, NPC state machines, catastrophe lifecycle, and video timeline triggers:

```bash
python tests/test_client.py
```

Expected result:
```text
Ran 20 tests in 1.10s
OK
```

---

## 8. Credits and Project Info

Made for NASA Space Apps Kochi.

Made by Lunarmist-byte
* GitHub: https://github.com/Lunarmist-byte
* LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
