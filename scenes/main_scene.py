"""MARS SURVIVAL — Main Scene Coordinator.

Orchestrates environmental rendering, player movement, camera tracking,
HUD telemetry, and non-blocking MARS-EIS synchronization.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG
from world.world_state import WorldState
from player.player import Player
from systems.camera import Camera
from systems.input_handler import InputHandler
from systems.environment_animator import EnvironmentAnimator
from systems.mission_system import MissionSystem
from scenes.mars_base import MarsBase
from ui.hud import HUD
from ui.situation_modal import SituationModal
from backend.simulation_sync import SimulationSync


class MainScene:
    """Primary playable game scene coordinating world, player, and simulation sync."""

    def __init__(self, sync: SimulationSync) -> None:
        self.sync = sync
        self.world_state = WorldState()

        # Initialize environment and playable world
        self.mars_base = MarsBase()

        # Initialize player at base center
        self.player = Player()

        # Initialize camera tracking
        self.camera = Camera(
            viewport_width=WINDOW_WIDTH,
            viewport_height=WINDOW_HEIGHT,
            world_width=self.mars_base.world_rect.width,
            world_height=self.mars_base.world_rect.height,
            smoothing=0.10
        )
        # Snap camera immediately to player spawn
        self.camera.offset_x = self.player.position.x - (WINDOW_WIDTH / 2.0)
        self.camera.offset_y = self.player.position.y - (WINDOW_HEIGHT / 2.0)

        # UI & Input Systems
        self.hud = HUD()
        self.input_handler = InputHandler()
        self.situation_modal = SituationModal(self.hud.ui)
        self.env_animator = EnvironmentAnimator()
        self.mission_system = MissionSystem()

        self.nearby_facility: Optional[Dict[str, Any]] = None
        self.nearby_door: Optional[Any] = None

    def handle_actions(self, action_triggers: List[str]) -> None:
        """Dispatch player-initiated action requests to MARS-EIS and update missions."""
        for act in action_triggers:
            if act == "MANUAL_ADVANCE":
                queued = self.sync.request_advance()
                if queued:
                    self.player.state.set_action_feedback("Simulation Advance Step Dispatched (+10s)", True)
                else:
                    self.player.state.set_action_feedback("Advance in progress, please wait...", False)

            elif act == "CLEAN_SOLAR_PANELS":
                act_id = self.player.state.next_action_id("clean")
                self.sync.dispatch_action("CLEAN_PANELS", {"method": "ROBOTIC_WIPER"}, action_id=act_id)
                res = self.mission_system.complete_mission_for_facility("solar_farm", self.world_state, self.player.state)
                if res:
                    self.player.state.set_action_feedback(f"{res[0]} // {res[1]}", True, duration=4.0)
                else:
                    self.player.state.set_action_feedback("Solar panels de-soiled (+25% Efficiency)!", True)

            elif act == "EXCAVATE":
                act_id = self.player.state.next_action_id("drill")
                self.sync.dispatch_action("EXCAVATE", {"depth_m": 0.5}, action_id=act_id)
                res = self.mission_system.complete_mission_for_facility("greenhouse", self.world_state, self.player.state)
                if res:
                    self.player.state.set_action_feedback(f"{res[0]} // {res[1]}", True, duration=4.0)
                else:
                    self.player.state.set_action_feedback("Regolith excavated & crops fertilized (+15 Days Rations)!", True)

            elif act == "HABITAT_INTERACTION":
                # Context-aware interaction based on nearest facility
                if self.nearby_facility:
                    fac_id = self.nearby_facility.get("facility_id", "")
                    fac_name = self.nearby_facility.get("name", "Facility")
                    fac_act = self.nearby_facility.get("interaction_action", "SEAL_HULL_BREACH")

                    # Complete facility survival mission and apply authoritative stat boosts
                    res = self.mission_system.complete_mission_for_facility(fac_id, self.world_state, self.player.state)
                    if res:
                        fb, reward = res
                        self.player.state.set_action_feedback(f"{fb} // {reward}", True, duration=4.0)
                    else:
                        self.player.state.set_action_feedback(f"Interacting with {fac_name} ({fac_act})...", True)

                    act_id = self.player.state.next_action_id("hab")
                    self.sync.dispatch_action(fac_act, {"facility_id": fac_id}, action_id=act_id)
                else:
                    # Default habitat inspection
                    act_id = self.player.state.next_action_id("hab")
                    self.sync.dispatch_action("SEAL_HULL_BREACH", {}, action_id=act_id)
                    self.player.state.set_action_feedback("EVA Habitat Inspection & Structural Weld Complete", True)

            elif act == "FORCE_RECONNECT":
                self.sync.request_state_sync()
                self.player.state.set_action_feedback("Reconnecting to MARS-EIS...", True)

            elif act == "SELECT_CHAR_1":
                self.player.switch_character(1)
            elif act == "SELECT_CHAR_2":
                self.player.switch_character(2)
            elif act == "SELECT_CHAR_3":
                self.player.switch_character(3)
            elif act == "SELECT_CHAR_4":
                self.player.switch_character(4)
            elif act == "CYCLE_CHAR":
                next_id = (self.player.animation.character_id % 4) + 1
                self.player.switch_character(next_id)
            elif act == "TOGGLE_SITUATIONS":
                self.situation_modal.toggle()

    def update(self, dt: float) -> bool:
        """Frame update cycle. Returns False if game should exit."""
        # 1. Process Pygame events and user input (intercepted by situation modal if open)
        def modal_key_handler(key: int) -> bool:
            if self.situation_modal.is_open:
                return self.situation_modal.handle_key(key, self.sync)
            return False

        should_quit, action_triggers = self.input_handler.process_events(modal_key_handler)
        if should_quit:
            return False

        # 2. Dispatch queued actions
        self.handle_actions(action_triggers)

        # 3. Synchronize with background simulation worker (non-blocking)
        self.sync.poll_results(self.world_state, self.player.state)

        # Update modal timers and environmental simulation animations
        self.situation_modal.update(dt)
        self.env_animator.update(dt, self.world_state)

        # 4. Movement input & Player state update
        dx, dy = self.input_handler.get_movement_vector()
        self.player.handle_input(dx, dy)

        # Update automated base doors against player proximity
        self.mars_base.update(dt, (self.player.position.x, self.player.position.y))

        movement_telemetry = self.player.update(dt, self.mars_base)
        if movement_telemetry:
            self.sync.report_movement(
                distance_meters=movement_telemetry["distance_meters"],
                speed_ms=movement_telemetry["speed_ms"],
                heading_deg=movement_telemetry["heading_deg"],
                world_position=movement_telemetry["world_position"]
            )

        # 5. Camera follow tracking with procedural screen shake trauma
        self.camera.update(self.player.position, dt)
        self.camera.offset_x += self.env_animator.shake_offset_x
        self.camera.offset_y += self.env_animator.shake_offset_y

        # 6. Check facility and door proximity
        self.nearby_facility = self.mars_base.get_nearby_facility((self.player.position.x, self.player.position.y))
        self.nearby_door = self.mars_base.door_manager.get_nearby_door((self.player.position.x, self.player.position.y))

        return True

    def render(self, surface: pygame.Surface) -> None:
        """Draw complete scene layers."""
        # 1. Clear display
        surface.fill(COLOR_BG)

        # 2. Render background in camera coordinate space
        self.mars_base.render(surface, self.camera)

        # 3. Render player character in camera space
        self.player.render(surface, self.camera)

        # 4. Render atmospheric lighting, wind particles, and catastrophe overlays
        self.env_animator.render(surface, self.world_state)

        # 5. Render HUD in fixed screen coordinates
        self.hud.render(
            surface=surface,
            world_state=self.world_state,
            player_state=self.player.state,
            backend_url=self.sync.config.base_url,
            show_help=self.input_handler.show_help,
            show_debug=self.input_handler.show_debug,
            show_live_feed=self.input_handler.show_live_feed,
            nearby_facility=self.nearby_facility,
            nearby_door=self.nearby_door,
            active_crew_id=self.player.animation.character_id,
            mission_system=self.mission_system,
            base_facilities=self.mars_base.facilities,
        )

        # 6. Render Situation Injector modal if active
        self.situation_modal.render(surface, self.world_state)
