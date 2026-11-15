# PYGAME — MARS SURVIVAL GAME CLIENT
## MARS-EIS (Mars Environmental Intelligence & Simulation Engine) Integration

A top-down 2D Mars survival game client built with **Python 3.x** and **Pygame 2.x**, connected to **MARS-EIS**, an authoritative scientific Mars environmental simulation backend.

---

## Author & Credit Section

### Made by Lunarmist-byte
* **GitHub Profile:** [https://github.com/Lunarmist-byte](https://github.com/Lunarmist-byte)
* **LinkedIn Profile:** [https://www.linkedin.com/in/amal-s-kumar-ba69a1290/](https://www.linkedin.com/in/amal-s-kumar-ba69a1290/)

---

## 1. Architectural Philosophy

The Pygame client and MARS-EIS backend remain **logically and executionally separate**, even though both are written in Python:

* **Pygame Game Client (Presentation & Interaction Layer):**
  * Renders the Mars surface and base infrastructure using the provided background artwork.
  * Captures player movement (WASD and Arrow keys) with normalized diagonal vectors.
  * Manages directional character animation and smooth horizontal sprite flipping.
  * Operates a 2D camera following the player, clamped to world boundaries.
  * Renders a real-time HUD displaying Martian Sol, local solar time, environmental measurements, battery status, and hazard alerts.
  * Dispatches player actions and movement telemetry asynchronously to the backend.
  * **Never simulates Mars physics, atmospheric models, or weather locally.**

* **MARS-EIS Backend (Authoritative Environmental Engine):**
  * Computes Martian atmospheric density, surface/air temperature, and surface pressure.
  * Simulates dust transport, dust lifting flux, and atmospheric optical depth ($\tau$).
  * Calculates solar irradiance, diurnal cycles, and surface radiation doses.
  * Authoritatively calculates power generation, battery drain, and ECLSS life-support status.
  * Generates emergent environmental events (regional dust storms, anomalies, catastrophes).
  * Validates and processes player interventions (panel cleaning, rover traversal, core excavation).

Communication is handled over HTTP REST using non-blocking background worker threads, guaranteeing that the Pygame main game loop runs at a smooth, constant frame rate without networking freezes.

---

## 2. Project Structure

```text
pygame/
│
├── main.py                      # Main game entry point and 60 FPS delta-time loop
├── config.py                    # Centralized display, backend, world, and theme settings
├── requirements.txt             # Project dependencies (pygame, requests)
├── README.md                    # System documentation and operational guide
│
├── scenes/
│   ├── __init__.py
│   ├── mars_base.py             # Loads background artwork, scales with aspect preservation
│   └── main_scene.py            # Coordinates player, world, camera, and simulation sync
│
├── player/
│   ├── __init__.py
│   ├── player.py                # Player entity combining position, movement, and animation
│   ├── movement.py              # Delta-time normalized movement and telemetry batching
│   └── animation.py             # Configurable animation states, transitions, and flipping
│
├── ui/
│   ├── __init__.py
│   ├── components.py            # Stylized HUD drawing primitives (panels, badges, bars)
│   ├── hud.py                   # Full-screen telemetry HUD, status bars, and credits
│   └── event_panel.py           # Emergent hazards and active simulation events panel
│
├── backend/
│   ├── __init__.py
│   ├── backend_config.py        # Centralized REST & WebSocket network settings and timeouts
│   ├── api_client.py            # Authoritative HTTP REST client for MARS-EIS endpoints
│   ├── live_feed.py             # Non-blocking asynchronous WebSocket live feed client
│   └── simulation_sync.py       # Dual-channel synchronizer (1.0 Hz Live Feed + REST fallback)
│
├── world/
│   ├── __init__.py
│   ├── world_state.py           # Thread-safe simulation state container with versioning
│   ├── environmental_state.py   # Environmental telemetry model with strict 'N/A' formatting
│   └── player_state.py          # Client-side player coordinates and action feedback
│
├── systems/
│   ├── __init__.py
│   ├── camera.py                # 2D camera following player with boundary clamping
│   ├── input_handler.py         # Keyboard input mapping and interactive action triggers
│   └── event_display.py         # Event filtering, severity ratings, and notifications
│
├── assets/
│   ├── backgrounds/
│   │   └── mars_base_background.jpg  # Original base environment artwork (1024x682)
│   ├── characters/              # Designated directory for user-supplied sprite sheets
│   └── ui/
│
└── tests/
    └── test_client.py           # Comprehensive automated unit and integration tests
```

---

## 3. Game Environment & Background Artwork

* **Preservation of Original Artwork:** Uses the original `mars_base_background.jpg` (1024 $\times$ 682 px). The aspect ratio ($\approx 1.5015$) is strictly preserved.
* **World Scaling:** With a configurable `WORLD_SCALE = 2.0`, the world dimensions expand to $2048 \times 1364$ world coordinates, creating a large, explorable base perimeter.
* **Camera System:** The camera smoothly tracks the player's world position and clamps to the world bounds, ensuring that no void or black borders outside the map are ever rendered.
* **Wall Collision & Solid Boundaries:** A 1-bit high-precision collision mask ([assets/backgrounds/mars_base_collision_mask.png](file:///c:/Users/amals/Documents/Codeworks/pygame/assets/backgrounds/mars_base_collision_mask.png)) actively bounds the player. Solid exterior hull walls, interior room partitions, consoles, and heavy equipment block movement. Axis-separated movement allows smooth sliding along walls.
* **100% Walkable Corridors to All Rooms:** All corridors connecting the central rotunda to the 9 facility rooms (Oxygen Generation, Water Recycling, Greenhouse Hydroponics, Solar Array, Nuclear Reactor, Power Generator, Medbay, Robotics Workshop, and Comms Center) and external airlocks are carved open and 100% walkable with zero blocked bottlenecks.
* **Original Martian Catastrophe Dust Particles:** Features a multi-tiered, authentic ferric oxide dust particle engine rendered with true per-pixel alpha blending onto a dedicated translucent surface. Ambient conditions maintain a subtle, elegant atmospheric suspension; triggering a catastrophe (e.g. `[T / F4]` $\rightarrow$ `1` or `6`) unleashes up to 350 particles with dynamic wind streaks, organic sinusoidal eddy curls, atmospheric Mie scattering dust veils, and physical camera screen-shake.

---

## 4. 2D Platformer Polish & Interactive Challenge Systems

The game features comprehensive arcade/platformer-level responsiveness, game feel "juice", and interactive minigames:

### Game Feel & Tactile Movement Polish
* **Low-Gravity Martian Hop (`[Space]`):** Mars surface gravity ($0.38g$) allows floaty, parabolic EVA hops with dynamic vertical sprite displacement ($z(t)$) and ground shadow scaling that shrinks smoothly with elevation.
* **EVA Sprint & Cold Gas Thrusters (`[Shift]`):** Hold Shift to engage astronaut EVA thrusters for a $1.45\times$ speed boost, accompanied by animated cyan vapor plume particles.
* **Boot Regolith Footstep Puffs:** Walking or running kicks up subtle ferric regolith dust puffs in the opposite direction of motion, giving tangible ground traction and weight.
* **Landing Shockwave Rings:** Landing from a low-gravity hop spawns a 360-degree dust displacement ring with landing audio feedback.
* **Procedural Arcade Audio Synthesizer:** Pure Python mathematical sound generation via `pygame.mixer` (footstep taps, low-g liftoff sweeps, terminal interaction beeps, pickup musical arpeggios, and challenge victory fanfares).

### Interactive Facility Calibration Minigames
Entering a facility and pressing **`[E]`** opens the interactive calibration HUD:
* **Sweet-Spot Resonance Bar:** A dynamic oscillating needle moves across an animated calibration track.
* **Target Timing Zone:** Press `[Space]` or `[E]` when the needle enters the green resonance sweet spot.
* **Lock Progression:** Secure 3 successful alignment locks before the 20-second timer expires to successfully calibrate the facility.
* **Victory Celebration:** Winning triggers arpeggiated audio fanfares, bursts of facility-specific celebration particles (cyan oxygen vapor, blue water mist, green bio-spores, or electric sparks), and floating reward text popups (`+25.0 kg OXYGEN!`).

### Collectible Martian Science Artifacts
6 collectible geological and technological artifacts are scattered across Jezero Base:
1. **Ancient Jezero Olivine Crystal** (+100 pts)
2. **Chondritic Nickel-Iron Meteorite** (+150 pts)
3. **Subsurface Perchlorate Ice Core** (+120 pts)
4. **NASA Rover Telemetry Cache** (+200 pts)
5. **Sedimentary Delta Mudstone Shard** (+180 pts)
6. **Experimental Perovskite PV Cell** (+110 pts)
* Features vertical floating bob animations and glowing pulse auras.
* Walking over a sample collects it with a musical chime and floating `+100 SCIENCE!` text.

### Base Survival Efficiency Rating & Arcade Grade
The HUD continuously calculates overall base survival readiness:
$$\text{Readiness Score} = \frac{\text{O}_2 + \text{H}_2\text{O} + \text{Food} + \text{Battery} + \text{Solar Eff}}{5}$$
* **GRADE S (OPTIMAL 90%+):** High-efficiency fully restored life-support.
* **GRADE A (STABLE 70%+):** Safe operational margins.
* **GRADE B (MODERATE 50%+):** Depleting stores requiring crew intervention.
* **GRADE C (VULNERABLE <50%):** Critical ECLSS failure threat.

---

## 4. Player Character & Animation System

### Movement Controller
* **Controls:** `W`, `A`, `S`, `D` and Arrow keys.
* **Normalized Diagonal Movement:** When moving diagonally, input vectors are normalized to unit length so that diagonal movement speed ($|v| = 220.0$ px/s) is identical to horizontal and vertical speed.
* **Delta-Time Physics:** Movement displacement is multiplied by `dt` from `pygame.time.Clock.tick()`, maintaining consistent movement speed regardless of monitor refresh rate or frame fluctuations.
* **Telemetry Reporting:** Movement is accumulated and periodically dispatched to the backend (minimum every 1.0s or 2.0m) to calculate regolith disturbance and dust mobilization without spamming the network every frame.

### Active Crew & Living NPCs from Uploaded Sprites:
* **Primary Operator (Playable Character):** **Commander Suso** (Sprite 1 — Glasses & mustache, Mission Commander & Systems Architect)
* **Living Crew NPCs (Stationed across the Base):**
  * **Amal** (Sprite 3 — Bearded astronaut with thick wavy dark hair, Communications Specialist) — Located at Deep Space Telemetry & Comms Center (`[E]` Talk)
  * **Gowri** (Sprite 2 — Smiling astronaut with bindi, Research Fellow in Astrobiology) — Located in Hydroponic Greenhouse & Medbay (`[E]` Talk)
  * **Christy** (Sprite 4 — Wavy hair & goatee, Chief Robotics & Electrical Engineer) — Located in Robotics Workshop & Reactor (`[E]` Talk)
* **Interactive Dialogue System:** Approaching any crew NPC and pressing `[E]` opens an 8-bit dialogue box featuring their custom face portrait and station guidance.
* **20 Dynamic & Diverse Grid Challenge Minigames (5 Distinct Gameplay Modes):**
  * **Circuit Wiring QTE (`CIRCUIT_SEQUENCE`):** Input 5-step illuminated arrow sequence (`[↑][→][↓][←]` or `[WASD]`) with neon feedback (Power Grid, Solar Servos, Holo-Globe Defense, Robotics Arm, Airlock Master Hub).
  * **Pressure Chamber Regulation (`PRESSURE_VALVE`):** Pump valve with `[SPACE]` to keep fluctuating pressure inside the safety green zone until stability reaches 100% (MOXIE O2 Room, Water Catalytic Filter, Muon Core Reactor, Ice Geyser Valve).
  * **Oscilloscope Wave Tuning (`FREQUENCY_TUNE`):** Adjust radio carrier frequency with `[A]`/`[D]` until transceiver wave matches the target sine wave, then lock downlink with `[SPACE]` (Deep Space Comms, Phobos Alien Dish).
  * **Radar Reticle Strike (`TARGET_STRIKE`):** Sweep moving crosshairs across scanning field and strike ore/pathogen nodes with `[SPACE]` (Solar Dust Clusters, Medbay Bio-Scanner, Hydroponic Seedlings).
  * **High-Speed Turbo Mash (`RAPID_TAP`):** Mash `[SPACE]` or `[E]` to build charge to 100% (Mark Watney Space Potatoes, Rover RTG Turbo, NASA Loot Crates, Atmospheric Sampling Kite).
* **Collapsible 8-Bit Minimal HUD:** Press `[H]` to toggle between an unobstructed minimal 8-bit ribbon and expanded detailed telemetry.
* **100% Unobstructed Walkability:** Exterior pathways, airlocks, solar panel fields, rover bay, and east landing pad are completely unblocked and walkable.
* **Prepared Animation Names:**
  * `idle` (Standing still)
  * `walk_down` (Walking downward)
  * `walk_up` (Walking upward)
  * `walk_left` (Walking left)
  * `walk_right` (Walking right)
* **Horizontal Sprite Flipping:** When moving right, the controller plays `walk_left` and automatically applies `pygame.transform.flip(surface, True, False)`.
* **Facing Memory:** Preserves the last valid facing direction when movement stops.
* **HUD Avatar Badge:** Displays the active astronaut's face portrait, callsign, and mission role in the EVA telemetry panel.

---

## 5. MARS-EIS Backend Integration

### Centralized Configuration
Configured in `config.py` and `backend/backend_config.py`:
```python
BACKEND_CONFIG = {
    "base_url": "http://127.0.0.1:8000",
    "sync_interval_seconds": 2.0,
    "request_timeout_seconds": 5.0,
    "reconnect_interval_seconds": 3.0,
    "delta_simulation_seconds": 10.0,
    "automatic_advance": True,
}
```

### Endpoints Used

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/world/state` | GET | Retrieve full simulated Martian state (Sol, atmosphere, thermal, dust, radiation, solar, infrastructure) |
| `/api/v1/world/advance` | POST | Advance simulation clock by `dt_seconds` (and optional Sols) |
| `/api/v1/world/action` | POST | Execute player interventions (`CLEAN_PANELS`, `EXCAVATE`, `SEAL_HULL_BREACH`, `ROUTE_EMERGENCY_POWER`) |
| `/api/v1/world/movement` | POST | Submit continuous traversed distance to calculate regolith disturbance and dust lifting |
| `/api/v1/world/events` | GET | Query active emergent events and climatological anomalies |
| `/api/v1/world/region/{id}` | GET | Retrieve regional topographic and grid parameters |

### Missing Fields and Backend Discrepancies Handled

1. **Temperature Units:** MARS-EIS returns temperatures in Kelvin (`air_temp_k`, `surface_temp_k`). The client converts Kelvin to Celsius ($T_C = T_K - 273.15$) for the HUD.
2. **Missing Life-Support Consumables:** In the current MARS-EIS simulation engine, `oxygen_reserve`, `water_reserve`, and `food_reserve` are part of the internal `ResourceStore` but are not serialized in the `to_dict()` state dictionary. The HUD detects this and explicitly renders `"N/A"` (never displaying fake zero values).
3. **Player Health & Coordinates:** MARS-EIS tracks robotic rovers and habitat modules, but does not maintain player astronaut health or 2D screen coordinates in its world state. Player health and coordinates are authoritatively tracked on the client side and sent as action/movement parameters.
4. **Advance Request Schema:** MARS-EIS expects `{"sols": float, "dt_seconds": float}`. The client formats advance payloads to match this exact schema.

---

## 6. How to Run

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Start the MARS-EIS Backend Server
In a separate terminal, launch the MARS-EIS FastAPI server:
```powershell
cd C:\Users\amals\Documents\Codeworks\ssosalien
python main.py --serve-api --port 8000
```
The backend starts at `http://127.0.0.1:8000`.

### Step 3: Launch the Pygame Client
In this directory:
```powershell
cd C:\Users\amals\Documents\Codeworks\pygame
python main.py
```

Optional CLI flags:
```powershell
python main.py --backend-url http://127.0.0.1:8000 --fps 60 --sync-interval 2.0
```

### Step 4: Run Automated Tests
```powershell
python tests\test_client.py
```

---

## 7. Controls Summary

| Key | Action |
|---|---|
| `W`, `A`, `S`, `D` / Arrows | 8-Directional Normalized Movement |
| `Shift` (Hold) | EVA Sprint / Cold Gas Thruster Boost ($1.45\times$ speed) |
| `Space` | Low-Gravity Martian Hop ($0.38g$ float arc & landing ring) |
| `E` | Engage Facility Interactive Challenge Minigame |
| `C` | Clean Solar Panels (`CLEAN_PANELS` + Mission completion) |
| `X` | Subsurface Regolith Excavation (`EXCAVATE`) |
| `1`, `2`, `3`, `4` | Crew Station Comms Check (Commander Suso = Player [Sprite 1], Gowri = Research [Sprite 2], Amal = Comms [Sprite 3], Christy = Engineer [Sprite 4]) |
| `Tab` | Focus Field Commander Suso |
| `H` | Toggle Collapsible 8-Bit Minimalist HUD / Full Telemetry |
| `T` / `F4` | Toggle MARS-EIS Situation Injector (Scenarios & Catastrophes) |
| `F5` | Toggle Real-Time WebSocket Live Feed Monitor Overlay |
| `F1` | Toggle System Help & Manual Overlay |
| `F2` | Force Immediate Reconnect to MARS-EIS |
| `F3` | Toggle Debug Telemetry Overlay |
| `Esc` | Exit Game / Abort Challenge / Close Overlays |

---

## 8. Author & Credits

### Made by Lunarmist-byte
* **GitHub Profile:** [https://github.com/Lunarmist-byte](https://github.com/Lunarmist-byte)
* **LinkedIn Profile:** [https://www.linkedin.com/in/amal-s-kumar-ba69a1290/](https://www.linkedin.com/in/amal-s-kumar-ba69a1290/)
