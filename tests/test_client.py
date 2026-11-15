"""MARS SURVIVAL — Automated Test Suite.

Unit and integration tests covering movement normalization, animation state
transitions, environmental telemetry parsing, missing metric formatting,
camera transformations, and background aspect-ratio scaling.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

import os
import sys
import unittest
import math

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((1280, 720))

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    WORLD_SCALE,
    BASE_WIDTH,
    BASE_HEIGHT,
    PLAYER_SPEED,
    ANIMATION_NAMES,
    CREDIT_INFO,
)
from world.environmental_state import EnvironmentalState
from world.world_state import WorldState
from world.player_state import PlayerState
from player.movement import MovementController
from player.animation import AnimationController
from player.player import Player
from systems.camera import Camera
from scenes.mars_base import MarsBase


class TestMarsSurvivalClient(unittest.TestCase):
    """Test suite validating core game and simulation client requirements."""

    def test_credits_present(self):
        """Verify author credits are correctly configured."""
        self.assertEqual(CREDIT_INFO["author"], "Lunarmist-byte")
        self.assertIn("Lunarmist-byte", CREDIT_INFO["github"])
        self.assertIn("amal-s-kumar", CREDIT_INFO["linkedin"])

    def test_environmental_missing_value_handling(self):
        """Verify missing environmental measurements strictly display 'N/A'."""
        empty_env = EnvironmentalState()
        self.assertEqual(empty_env.format_air_temp(), "N/A")
        self.assertEqual(empty_env.format_surface_temp(), "N/A")
        self.assertEqual(empty_env.format_pressure(), "N/A")
        self.assertEqual(empty_env.format_wind(), "N/A")
        self.assertEqual(empty_env.format_dust_opacity(), "N/A")
        self.assertEqual(empty_env.format_radiation(), "N/A")
        self.assertEqual(empty_env.format_solar(), "N/A")

    def test_environmental_state_kelvin_conversion(self):
        """Verify Kelvin to Celsius temperature conversion."""
        raw_data = {
            "thermal": {
                "air_temp_k": 215.15,
                "surface_temp_k": 223.15,
            },
            "atmosphere": {
                "pressure_pa": 750.5,
                "wind_speed_ms": 6.5,
                "wind_direction_deg": 180.0,
            },
            "dust": {
                "optical_depth_tau": 0.45,
            },
            "radiation": {
                "surface_dose_rate_ush_hr": 25.4,
            },
            "solar": {
                "net_flux_wm2": 380.0,
            }
        }
        env = EnvironmentalState.from_backend_dict(raw_data)
        self.assertAlmostEqual(env.air_temperature_c, -58.0, places=1)
        self.assertAlmostEqual(env.surface_temperature_c, -50.0, places=1)
        self.assertEqual(env.format_pressure(), "750.5 Pa")
        self.assertIn("6.5 m/s", env.format_wind())
        self.assertEqual(env.format_dust_opacity(), "τ 0.45")

    def test_movement_diagonal_normalization(self):
        """Verify diagonal movement does not exceed cardinal movement speed."""
        ctrl = MovementController(speed=PLAYER_SPEED)
        
        # Pure cardinal movement
        ctrl.update_input(1.0, 0.0)
        self.assertAlmostEqual(ctrl.velocity.length(), PLAYER_SPEED, places=2)

        # Diagonal movement
        ctrl.update_input(1.0, 1.0)
        # Normalized length must be exactly equal to speed, NOT sqrt(2) * speed
        self.assertAlmostEqual(ctrl.velocity.length(), PLAYER_SPEED, places=2)
        expected_component = PLAYER_SPEED / math.sqrt(2.0)
        self.assertAlmostEqual(ctrl.velocity.x, expected_component, places=2)
        self.assertAlmostEqual(ctrl.velocity.y, expected_component, places=2)

    def test_animation_directional_selection_and_flipping(self):
        """Verify animation naming, directional transitions, and right-flip requirement."""
        anim = AnimationController()
        
        # Verify required animation names are prepared
        for name in ["idle", "walk_down", "walk_up", "walk_left", "walk_right"]:
            self.assertIn(name, anim.animations)

        # 1. Idle when no input
        anim.update(pygame.Vector2(0, 0), 0.016)
        self.assertEqual(anim.current_animation, "idle")

        # 2. Moving up
        anim.update(pygame.Vector2(0, -1), 0.016)
        self.assertEqual(anim.current_animation, "walk_up")
        self.assertEqual(anim.facing_direction, "up")
        self.assertFalse(anim.flip_horizontal)

        # 3. Moving down
        anim.update(pygame.Vector2(0, 1), 0.016)
        self.assertEqual(anim.current_animation, "walk_down")
        self.assertEqual(anim.facing_direction, "down")
        self.assertFalse(anim.flip_horizontal)

        # 4. Moving left
        anim.update(pygame.Vector2(-1, 0), 0.016)
        self.assertEqual(anim.current_animation, "walk_left")
        self.assertEqual(anim.facing_direction, "left")
        self.assertFalse(anim.flip_horizontal)

        # 5. Moving right -> Must use walk_left with horizontal flipping enabled
        anim.update(pygame.Vector2(1, 0), 0.016)
        self.assertEqual(anim.current_animation, "walk_left")
        self.assertEqual(anim.facing_direction, "right")
        self.assertTrue(anim.flip_horizontal)

        # 6. Stop moving -> Must retain last valid facing direction
        anim.update(pygame.Vector2(0, 0), 0.016)
        self.assertEqual(anim.current_animation, "idle")
        self.assertEqual(anim.facing_direction, "right")
        self.assertTrue(anim.flip_horizontal)

    def test_character_selection(self):
        """Verify all 4 astronaut crew member sprites load and switch cleanly."""
        anim = AnimationController(character_id=1)
        for char_id in range(1, 5):
            anim.load_crew_character(char_id)
            self.assertEqual(anim.character_id, char_id)
            self.assertTrue(len(anim.animations["walk_left"]) > 0)
            self.assertTrue(len(anim.animations["idle"]) > 0)
            frame = anim.get_current_frame()
            self.assertIsInstance(frame, pygame.Surface)
            self.assertTrue(frame.get_width() > 0 and frame.get_height() > 0)

    def test_wall_collision_bounds_player(self):
        """Verify the player character cannot walk over solid base walls."""
        base = MarsBase()
        player = Player(x=1000, y=840)

        # Move down towards generator wall
        for _ in range(60):
            player.handle_input(0.0, 1.0)
            player.update(0.016, base)

        # Move left towards solid west wall
        for _ in range(120):
            player.handle_input(-1.0, 0.0)
            player.update(0.016, base)

        blocked_x = player.position.x
        # Attempt to walk directly into the wall repeatedly
        for _ in range(30):
            player.handle_input(-1.0, 0.0)
            player.update(0.016, base)

        self.assertEqual(player.position.x, blocked_x, "Player walked through a solid wall!")

    def test_camera_clamping(self):
        """Verify camera keeps viewport clamped within world bounds."""
        cam = Camera(viewport_width=1280, viewport_height=720, world_width=2048, world_height=1364, smoothing=1.0)
        
        # Target at origin
        cam.update((0, 0), dt=1.0)
        self.assertEqual(cam.offset_x, 0.0)
        self.assertEqual(cam.offset_y, 0.0)

        # Target far beyond bottom-right
        cam.update((5000, 5000), dt=1.0)
        max_x = 2048 - 1280
        max_y = 1364 - 720
        self.assertEqual(cam.offset_x, max_x)
        self.assertEqual(cam.offset_y, max_y)

    def test_mars_base_aspect_ratio_preservation(self):
        """Verify Mars base background preserves exact proportions."""
        base = MarsBase()
        raw_w, raw_h = base.raw_surface.get_size()
        scaled_w, scaled_h = base.scaled_surface.get_size()

        orig_aspect = raw_w / float(raw_h)
        scaled_aspect = scaled_w / float(scaled_h)
        self.assertAlmostEqual(orig_aspect, scaled_aspect, places=3)
        self.assertEqual(scaled_w, WORLD_WIDTH)
        self.assertEqual(scaled_h, WORLD_HEIGHT)

    def test_hud_rendering(self):
        """Verify HUD renders cleanly with all widgets and no unhandled name errors."""
        from ui.hud import HUD
        hud = HUD()
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        world_state = WorldState()
        player_state = PlayerState()
        # Render offline
        hud.render(surface, world_state, player_state, "http://127.0.0.1:8000")
        # Render online
        world_state.simulation_status = "CONNECTED"
        hud.render(surface, world_state, player_state, "http://127.0.0.1:8000", show_help=True, show_debug=True)

    def test_door_auto_open_and_close_on_proximity(self):
        """Verify automated blast doors detect astronaut proximity, slide open, and re-seal."""
        from scenes.doors import Door
        door = Door(
            door_id="test_door",
            name="Test Bulkhead",
            base_cx=500.0,
            base_cy=500.0,
            base_w=60.0,
            base_h=22.0,
            orientation="horizontal",
            scale=1.0,
            proximity_radius=80.0,
            open_speed=4.0,  # fast open in 0.25s
            close_delay=0.2,
        )

        # 1. Initially closed and blocking
        self.assertEqual(door.state, "CLOSED")
        self.assertEqual(door.open_ratio, 0.0)
        self.assertTrue(door.is_blocking())
        self.assertTrue(door.check_collision(500.0, 500.0))

        # 2. Player approaches within proximity radius (distance = 40px < 80px)
        door.update(0.016, (500.0, 460.0))
        self.assertEqual(door.state, "OPENING")

        # Step forward in time until fully open
        for _ in range(30):
            door.update(0.016, (500.0, 460.0))

        self.assertEqual(door.state, "OPEN")
        self.assertEqual(door.open_ratio, 1.0)
        self.assertFalse(door.is_blocking())
        self.assertFalse(door.check_collision(500.0, 500.0), "Open door should not block collision")

        # 3. Player departs (distance = 200px > 80px)
        door.update(0.016, (500.0, 300.0))
        self.assertEqual(door.state, "OPEN")  # Holds during close_delay

        # Advance past close delay
        for _ in range(20):
            door.update(0.016, (500.0, 300.0))
        self.assertIn(door.state, ("CLOSING", "CLOSED"))

        # Step until fully sealed
        for _ in range(40):
            door.update(0.016, (500.0, 300.0))

        self.assertEqual(door.state, "CLOSED")
        self.assertEqual(door.open_ratio, 0.0)
        self.assertTrue(door.is_blocking())
        self.assertTrue(door.check_collision(500.0, 500.0))

    def test_door_manager_integrated_with_mars_base(self):
        """Verify MarsBase seamlessly manages all doors and renders without errors."""
        base = MarsBase()
        self.assertEqual(len(base.door_manager.doors), 12)

        # Update doors with player at central spawn (1000, 840)
        base.update(0.016, (1000.0, 840.0))

        # Verify rendering in camera space
        cam = Camera(1280, 720, WORLD_WIDTH, WORLD_HEIGHT)
        surf = pygame.Surface((1280, 720))
        base.render(surf, cam)

    def test_environment_animator_and_catastrophes(self):
        """Verify environmental simulation animator, diurnal lighting, and trauma shake."""
        from systems.environment_animator import EnvironmentAnimator
        anim = EnvironmentAnimator()
        surf = pygame.Surface((1280, 720))
        world_state = WorldState()

        # 1. Screen shake trauma
        self.assertEqual(anim.trauma, 0.0)
        anim.add_trauma(0.6)
        self.assertEqual(anim.trauma, 0.6)
        anim.update(0.1, world_state)
        self.assertTrue(anim.trauma < 0.6)
        self.assertTrue(anim.shake_offset_x != 0.0 or anim.shake_offset_y != 0.0)

        # 2. Day / Twilight / Night cycle rendering
        world_state.fractional_sol = 0.5  # Noon
        anim.render(surf, world_state)
        world_state.fractional_sol = 0.25  # Twilight
        anim.render(surf, world_state)
        world_state.fractional_sol = 0.05  # Night
        anim.render(surf, world_state)

        # 3. Active catastrophe visual effects
        world_state.catastrophes = [
            {"type": "GLOBAL_DUST_STORM", "name": "Global Dust Storm", "severity": 0.9, "active": True},
            {"type": "SEVERE_MARSQUAKE", "name": "Severe Marsquake", "severity": 0.85, "screen_shake_intensity": 1.2, "active": True},
            {"type": "SOLAR_PARTICLE_EVENT", "name": "Solar Flare", "severity": 0.7, "active": True},
            {"type": "CRYOGENIC_FLASH_FREEZE", "name": "Flash Freeze", "severity": 0.9, "active": True},
            {"type": "HABITAT_HULL_BREACH", "name": "Hull Depressurization", "severity": 1.0, "active": True},
        ]
        anim.update(0.016, world_state)
        anim.render(surf, world_state)

    def test_situation_modal_and_backend_dispatch(self):
        """Verify situation injector modal triggers scenario presets and catastrophe events."""
        from ui.components import UIComponents
        from ui.situation_modal import SituationModal
        from backend.simulation_sync import SimulationSync

        ui = UIComponents()
        modal = SituationModal(ui)
        sync = SimulationSync()
        world_state = WorldState()
        surf = pygame.Surface((1280, 720))

        # 1. Toggle modal
        self.assertFalse(modal.is_open)
        modal.toggle()
        self.assertTrue(modal.is_open)

        # 2. Render modal
        modal.render(surf, world_state)

        # 3. Trigger Scenario 1 (Dust Storm 2018) via numeric key
        handled = modal.handle_key(pygame.K_1, sync)
        self.assertTrue(handled)
        self.assertIn("2018 Global Dust Storm", modal.feedback_message)

        # 4. Trigger Catastrophe 7 (Severe Marsquake) via numeric key
        handled = modal.handle_key(pygame.K_7, sync)
        self.assertTrue(handled)
        self.assertIn("Marsquake", modal.feedback_message)

        # 5. Close modal
        modal.handle_key(pygame.K_ESCAPE, sync)
        self.assertFalse(modal.is_open)

    def test_live_feed_client_and_telemetry_streaming(self):
        """Verify real-time WebSocket live feed client, packet decoding, and HUD live stream integration."""
        from backend.backend_config import BackendConfig
        from backend.live_feed import LiveFeedClient
        from backend.simulation_sync import SimulationSync
        from ui.hud import HUD

        # 1. Verify WebSocket URL derivation
        cfg = BackendConfig(base_url="http://127.0.0.1:8000")
        self.assertEqual(cfg.get_ws_url(), "ws://127.0.0.1:8000/ws/telemetry")

        # 2. Test LiveFeedClient packet simulation
        client = LiveFeedClient(cfg)
        self.assertFalse(client.is_connected)

        sample_telemetry = {
            "type": "TELEMETRY_UPDATE",
            "sol": 42,
            "fractional_sol": 0.35,
            "ltst_hours": 8.4,
            "optical_depth_tau": 0.85,
            "surface_temp_k": 225.15,
            "air_temp_k": 218.15,
            "pressure_pa": 715.0,
            "wind_speed_ms": 14.5,
            "wind_direction_deg": 270.0,
            "battery_soc": 0.88,
            "battery_level_wh": 4400.0,
            "power_gen_w": 620.0,
            "power_load_w": 310.0,
            "emergency_level": "WARNING",
            "active_events": [],
            "issues": [{"title": "Dust Accumulation"}],
            "catastrophes": [],
            "godot_visuals": {
                "fog_density": 0.0038,
                "sun_energy": 0.75,
                "sun_pitch_deg": 35.0,
                "sun_yaw_deg": 270.0,
                "is_blue_twilight": True,
                "wind_particle_scale": 2.9,
            }
        }

        # Put packet on incoming queue
        client.incoming_packets.put(("TELEMETRY_UPDATE", sample_telemetry))
        client.packets_received = 1
        client.packet_rate_hz = 1.0

        # 3. Process packet through SimulationSync
        sync = SimulationSync(cfg)
        sync.live_feed = client
        world_state = WorldState()
        player_state = PlayerState()

        sync.poll_results(world_state, player_state)

        # Assert world_state is updated live
        self.assertTrue(world_state.is_live_feed)
        self.assertEqual(world_state.sol, 42)
        self.assertAlmostEqual(world_state.environment.air_temperature_c, -55.0, places=1)
        self.assertAlmostEqual(world_state.environment.surface_temperature_c, -48.0, places=1)
        self.assertEqual(world_state.environment.pressure_pa, 715.0)
        self.assertEqual(world_state.environment.wind_speed_m_s, 14.5)
        self.assertEqual(world_state.environment.dust_opacity_tau, 0.85)
        self.assertEqual(world_state.battery_soc, 88.0)
        self.assertEqual(world_state.emergency_level, "WARNING")
        self.assertIn("LIVE FEED", world_state.simulation_status)
        self.assertTrue(world_state.godot_visuals.get("is_blue_twilight"))

        # 4. Render HUD with live feed overlay
        hud = HUD()
        surf = pygame.Surface((1280, 720))
        hud.render(
            surface=surf,
            world_state=world_state,
            player_state=player_state,
            backend_url="ws://127.0.0.1:8000/ws/telemetry",
            show_live_feed=True,
        )

    def test_corridors_open_and_missions_progression(self):
        """Verify that all room corridors are 100% open and missions increase stats."""
        from systems.mission_system import MissionSystem
        from scenes.doors import Door
        from scenes.mars_base import MarsBase

        # 1. Verify MarsBase has open corridors to all rooms
        mars_base = MarsBase()
        self.assertIsNotNone(mars_base.collision_mask)

        # Check key corridor waypoints are completely unblocked
        corridor_checkpoints = [
            (512 * WORLD_SCALE, 395 * WORLD_SCALE),  # Central Rotunda
            (460 * WORLD_SCALE, 375 * WORLD_SCALE),  # Medbay corridor
            (512 * WORLD_SCALE, 280 * WORLD_SCALE),  # North Reactor corridor
            (512 * WORLD_SCALE, 455 * WORLD_SCALE),  # South Generator corridor
            (450 * WORLD_SCALE, 280 * WORLD_SCALE),  # Comms corridor
            (570 * WORLD_SCALE, 280 * WORLD_SCALE),  # Command Lab corridor
            (560 * WORLD_SCALE, 375 * WORLD_SCALE),  # Water Recycling corridor
            (450 * WORLD_SCALE, 470 * WORLD_SCALE),  # Greenhouse corridor
            (570 * WORLD_SCALE, 470 * WORLD_SCALE),  # Workshop corridor
            (838 * WORLD_SCALE, 560 * WORLD_SCALE),  # Oxygen Plant doorway
        ]
        for wx, wy in corridor_checkpoints:
            mars_base.update(0.1, (wx, wy))
            collides = mars_base.check_foot_collision(wx, wy)
            self.assertFalse(collides, f"Corridor at world ({wx}, {wy}) should be open and walkable!")

        # 2. Verify Door does not block when player is nearby
        door = Door("test_door", "Test Bulkhead", 100, 100, 40, 20, "horizontal")
        door.is_player_nearby = True
        door.open_ratio = 0.0
        self.assertFalse(door.is_blocking(), "Approaching player must not be blocked by door sensor!")

        # 3. Test MissionSystem stat increments
        missions = MissionSystem()
        world_state = WorldState()
        player_state = PlayerState()
        player_state.health = 50.0

        # Oxygen mission
        res = missions.complete_mission_for_facility("oxygen_plant", world_state, player_state)
        self.assertIsNotNone(res)
        self.assertIsNotNone(world_state.oxygen_reserve)
        self.assertTrue(world_state.oxygen_reserve >= 25.0)

        # Water mission
        res = missions.complete_mission_for_facility("water_recycling", world_state, player_state)
        self.assertIsNotNone(res)
        self.assertIsNotNone(world_state.water_reserve)
        self.assertTrue(world_state.water_reserve >= 35.0)

        # Food mission
        res = missions.complete_mission_for_facility("greenhouse", world_state, player_state)
        self.assertIsNotNone(res)
        self.assertIsNotNone(world_state.food_reserve)
        self.assertTrue(world_state.food_reserve >= 15.0)

        # Solar mission
        res = missions.complete_mission_for_facility("solar_farm", world_state, player_state)
        self.assertIsNotNone(res)
        self.assertIsNotNone(world_state.solar_panel_efficiency)
        self.assertTrue(world_state.solar_panel_efficiency >= 25.0)

        # Medical mission
        res = missions.complete_mission_for_facility("medbay", world_state, player_state)
        self.assertIsNotNone(res)
        self.assertEqual(player_state.health, 100.0)

        # Battery mission
        res = missions.complete_mission_for_facility("power_generator", world_state, player_state)
        self.assertIsNotNone(res)
        self.assertIsNotNone(world_state.battery_soc)
        self.assertTrue(world_state.battery_soc >= 30.0)


if __name__ == "__main__":
    unittest.main()
