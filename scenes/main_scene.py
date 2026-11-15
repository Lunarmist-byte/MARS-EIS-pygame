"""DUSTFALL — Main Scene Coordinator.

Orchestrates 2D platformer-level gameplay polish:
- Player (Commander Suso) with low-gravity hops and EVA sprint
- Other 3 crew members (Dr. Maya, Alex, Vikram) placed as interactive living NPCs
- 15 Grid Challenge stations across the base with 8-bit markers [ ★ ]
- Interactive sweet-spot calibration minigames
- Collapsible 8-bit minimalist HUD interface ([H] toggle)
- Auto-expiring catastrophe simulation (no lingering alerts)
- Procedural audio, particle FX, collectibles, and MARS-EIS synchronization.

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
from systems.audio_synthesizer import SoundSynthesizer
from systems.particle_fx import ParticleFXSystem
from systems.floating_text import FloatingTextSystem
from systems.collectibles_system import CollectiblesSystem
from systems.facility_challenge_minigame import ChallengeMinigame
from systems.npc_system import NPCSystem
from systems.grid_challenges import GridChallengeSystem
from systems.catastrophe_manager import CatastropheDirector
from scenes.mars_base import MarsBase
from ui.hud import HUD
from ui.components import UIComponents
from ui.situation_modal import SituationModal
from backend.simulation_sync import SimulationSync


class MainScene:
    """Primary playable game scene coordinating world, player, and simulation sync."""

    def __init__(self, sync: SimulationSync) -> None:
        self.sync = sync
        self.world_state = WorldState()

        # Initialize environment and playable world
        self.mars_base = MarsBase()

        # Initialize player (Commander Suso) at base center
        self.player = Player()

        # Initialize camera tracking
        self.camera = Camera(
            viewport_width=WINDOW_WIDTH,
            viewport_height=WINDOW_HEIGHT,
            world_width=self.mars_base.world_rect.width,
            world_height=self.mars_base.world_rect.height,
            smoothing=0.10
        )
        self.camera.offset_x = self.player.position.x - (WINDOW_WIDTH / 2.0)
        self.camera.offset_y = self.player.position.y - (WINDOW_HEIGHT / 2.0)

        # UI & Input Systems
        self.hud = HUD()
        self.input_handler = InputHandler()
        self.ui_components = UIComponents()
        self.situation_modal = SituationModal(self.ui_components)
        self.env_animator = EnvironmentAnimator()
        self.mission_system = MissionSystem()

        # Arcade Polish Systems
        self.audio = SoundSynthesizer()
        self.particle_fx = ParticleFXSystem()
        self.floating_text = FloatingTextSystem()
        self.collectibles = CollectiblesSystem()
        self.challenge_minigame = ChallengeMinigame()

        # Crew NPCs (Amal, Gowri, Christy) & 20 Grid Challenge Stations
        self.npc_system = NPCSystem()
        self.grid_challenges = GridChallengeSystem()

        # Procedural Catastrophe Director & Emergency Evacuation Manager
        self.catastrophe_director = CatastropheDirector(
            world_state=self.world_state,
            audio=self.audio,
            npc_system=self.npc_system,
            grid_challenges=self.grid_challenges,
            mission_system=self.mission_system,
            particle_fx=self.particle_fx,
            floating_text=self.floating_text,
            sync=self.sync,
            initial_delay=300.0,  # Catastrophe happens once every 5 minutes (300s)
        )

        # Start game during initial Ferric Dust Storm with NPCs inside wandering randomly
        self.catastrophe_director.trigger_catastrophe("GLOBAL_DUST_STORM", self.player.position)

        self.nearby_facility: Optional[Dict[str, Any]] = None

    def handle_actions(self, action_triggers: List[str]) -> None:
        """Dispatch player-initiated action requests to MARS-EIS and update missions."""
        for act in action_triggers:
            if act == "PLAYER_HOP":
                if self.player.hop():
                    self.audio.play("hop")
                    self.particle_fx.spawn_landing_ring(self.player.position.x, self.player.position.y + self.player.height // 2 - 2)
                    self.sync.request_advance()

            elif act == "TOGGLE_HUD":
                self.hud.toggle_collapse()
                self.audio.play("beep")

            elif act == "MANUAL_ADVANCE":
                queued = self.sync.request_advance()
                if queued:
                    self.player.state.set_action_feedback("Simulation Advance Step Dispatched (+10s)", True)
                else:
                    self.player.state.set_action_feedback("Advance in progress, please wait...", False)

            elif act == "CLEAN_SOLAR_PANELS":
                act_id = self.player.state.next_action_id("clean")
                self.sync.dispatch_action("CLEAN_PANELS", {"method": "ROBOTIC_WIPER"}, action_id=act_id)
                self.audio.play("success")
                self.particle_fx.spawn_celebration_burst(self.player.position.x, self.player.position.y, particle_type="spark")
                res = self.mission_system.complete_mission_for_facility("solar_farm", self.world_state, self.player.state)
                if res:
                    self.floating_text.spawn(res[1], self.player.position.x, self.player.position.y - 35, color=(255, 220, 80), big=True)
                    self.player.state.set_action_feedback(f"{res[0]} // {res[1]}", True, duration=4.0)
                else:
                    self.floating_text.spawn("+15% Photovoltaic Efficiency", self.player.position.x, self.player.position.y - 35, color=(255, 220, 80), big=True)
                    self.player.state.set_action_feedback("Solar Array Wiped // Basalt Regolith Cleared", True, duration=4.0)

            elif act == "EXCAVATE":
                act_id = self.player.state.next_action_id("drill")
                self.sync.dispatch_action("EXCAVATE", {"depth_m": 0.5}, action_id=act_id)
                self.audio.play("beep")
                if self.player.state.is_outside:
                    self.particle_fx.spawn_celebration_burst(self.player.position.x, self.player.position.y, particle_type="spark")
                    self.floating_text.spawn("+15 kg Regolith Core! (+50 Science)", self.player.position.x, self.player.position.y - 35, color=(240, 180, 80), big=True)
                    self.player.state.set_action_feedback("EVA Surface Drill // Subsurface Regolith Sample Extracted (+50 Sci)", True, duration=4.0)
                else:
                    res = self.mission_system.complete_mission_for_facility("greenhouse", self.world_state, self.player.state)
                    if res:
                        self.audio.play("success")
                        self.particle_fx.spawn_celebration_burst(self.player.position.x, self.player.position.y, particle_type="bio")
                        self.floating_text.spawn(res[1], self.player.position.x, self.player.position.y - 35, color=(120, 255, 140), big=True)
                        self.player.state.set_action_feedback(f"{res[0]} // {res[1]}", True, duration=4.0)

            elif act == "HABITAT_INTERACTION":
                # Priority 1: Check nearby Crew NPC (Amal, Gowri, Christy)
                nearby_npc = self.npc_system.get_nearby_npc(self.player.position)
                if nearby_npc:
                    line = self.npc_system.trigger_talk(self.player.position)
                    self.audio.play("beep")
                    if line:
                        self.player.state.set_action_feedback(line, True, duration=5.0)
                    return

                # Priority 2: Check nearby Grid Challenge Station
                nearby_station = self.grid_challenges.get_nearby_station(self.player.position)
                if nearby_station and not self.challenge_minigame.is_active:
                    st_id = nearby_station.station_id
                    st_name = nearby_station.name

                    def on_station_win() -> None:
                        res = self.grid_challenges.complete_station(st_id, self.world_state, self.player.state)
                        self.catastrophe_director.notify_repair_progress()
                        self.particle_fx.spawn_celebration_burst(self.player.position.x, self.player.position.y, particle_type="spark")
                        if res:
                            name, reward = res
                            self.floating_text.spawn(reward, self.player.position.x, self.player.position.y - 45, color=(100, 255, 160), big=True)
                            self.floating_text.spawn(f"+20% SPACE HEALTH! (Integrity: {self.world_state.station_health:.0f}%)", self.player.position.x, self.player.position.y - 70, color=(0, 255, 200), big=True)
                            self.player.state.set_action_feedback(f"CHALLENGE WON: {reward} // Space Health: {self.world_state.station_health:.0f}%", True, duration=4.0)
                            if self.world_state.station_health >= 100.0:
                                self.catastrophe_director.update(0.0, self.player.position)

                    self.challenge_minigame.start_challenge(
                        facility_id=st_id,
                        facility_name=st_name,
                        objective=nearby_station.objective,
                        reward_desc=nearby_station.reward_desc,
                        on_success_callback=on_station_win,
                        mode=nearby_station.mode,
                    )
                    self.audio.play("beep")
                    return

                # Priority 3: Check nearby base facility
                if self.nearby_facility and not self.challenge_minigame.is_active:
                    fac_id = self.nearby_facility.get("facility_id", "")
                    fac_name = self.nearby_facility.get("name", "Facility")
                    fac_act = self.nearby_facility.get("interaction_action", "SEAL_HULL_BREACH")

                    cur_m = None
                    for m in self.mission_system.missions:
                        if m.facility_id == fac_id:
                            cur_m = m
                            break
                    obj_text = cur_m.objective if cur_m else f"Align {fac_name} resonance parameters."
                    rew_text = cur_m.reward_desc if cur_m else "Base Infrastructure Online"

                    def on_facility_win() -> None:
                        res = self.mission_system.complete_mission_for_facility(fac_id, self.world_state, self.player.state)
                        self.catastrophe_director.notify_repair_progress()
                        p_type = "oxygen" if "oxygen" in fac_id else ("water" if "water" in fac_id else ("bio" if "greenhouse" in fac_id else "spark"))
                        self.particle_fx.spawn_celebration_burst(self.player.position.x, self.player.position.y, particle_type=p_type)
                        if res:
                            fb, reward = res
                            self.floating_text.spawn(reward, self.player.position.x, self.player.position.y - 45, color=(100, 255, 160), big=True)
                            self.floating_text.spawn(f"+25% SPACE HEALTH! (Integrity: {self.world_state.station_health:.0f}%)", self.player.position.x, self.player.position.y - 70, color=(0, 255, 200), big=True)
                            self.player.state.set_action_feedback(f"MISSION SUCCESS: {reward} // Space Health: {self.world_state.station_health:.0f}%", True, duration=4.0)
                            if self.world_state.station_health >= 100.0:
                                self.catastrophe_director.update(0.0, self.player.position)
                        act_id = self.player.state.next_action_id("hab")
                        self.sync.dispatch_action(fac_act, {"facility_id": fac_id}, action_id=act_id)

                    fac_mode = self.nearby_facility.get("challenge_mode", "CIRCUIT_SEQUENCE")
                    self.challenge_minigame.start_challenge(
                        facility_id=fac_id,
                        facility_name=fac_name,
                        objective=obj_text,
                        reward_desc=rew_text,
                        on_success_callback=on_facility_win,
                        mode=fac_mode,
                    )
                    self.audio.play("beep")
                else:
                    act_id = self.player.state.next_action_id("hab")
                    self.sync.dispatch_action("SEAL_HULL_BREACH", {}, action_id=act_id)
                    self.player.state.set_action_feedback("EVA Habitat Inspection Complete", True)

            elif act == "FORCE_RECONNECT":
                self.sync.request_state_sync()
                self.player.state.set_action_feedback("Reconnecting to MARS-EIS...", True)

            elif act == "TOGGLE_SITUATIONS":
                self.situation_modal.toggle()
                self.audio.play("beep")

            elif act == "SELECT_CHAR_1":
                self.player.switch_character(1)
                self.npc_system.set_active_player(1)
                self.audio.play("beep")
            elif act == "SELECT_CHAR_2":
                self.player.switch_character(2)
                self.npc_system.set_active_player(2)
                self.audio.play("beep")
            elif act == "SELECT_CHAR_3":
                self.player.switch_character(3)
                self.npc_system.set_active_player(3)
                self.audio.play("beep")
            elif act == "SELECT_CHAR_4":
                self.player.switch_character(4)
                self.npc_system.set_active_player(4)
                self.audio.play("beep")
            elif act == "CYCLE_CHAR":
                next_id = (self.player.animation.character_id % 4) + 1
                self.player.switch_character(next_id)
                self.npc_system.set_active_player(next_id)
                self.audio.play("beep")

    def update(self, dt: float) -> bool:
        """Frame update cycle. Returns False if game should exit."""
        # 0. Check if Mission Failed / Game Over state is active
        if self.catastrophe_director.is_game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.catastrophe_director.restart(self.player.position)
                        self.player.state.health = 100.0
                    elif event.key == pygame.K_ESCAPE:
                        return False
            return True

        # 1. Process Pygame events and user input
        def modal_handler(k: int) -> bool:
            if self.challenge_minigame.is_active:
                return self.challenge_minigame.handle_key(k, self.audio)
            if self.situation_modal.is_open:
                handled = self.situation_modal.handle_key(k, self.sync, self.world_state)
                if handled and k in (pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
                    key_map = {
                        pygame.K_6: "GLOBAL_DUST_STORM",
                        pygame.K_7: "SEVERE_MARSQUAKE",
                        pygame.K_8: "SOLAR_PARTICLE_EVENT",
                        pygame.K_9: "CRYOGENIC_FLASH_FREEZE",
                        pygame.K_0: "HABITAT_HULL_BREACH",
                    }
                    if k in key_map:
                        self.catastrophe_director.trigger_catastrophe(key_map[k], self.player.position)
                return handled
            return False

        should_quit, action_triggers = self.input_handler.process_events(modal_key_handler=modal_handler)
        if should_quit:
            return False

        # 2. Dispatch queued actions
        self.handle_actions(action_triggers)

        # 3. Synchronize with background simulation worker (non-blocking)
        self.sync.poll_results(self.world_state, self.player.state)

        # 4. Update procedural Catastrophe Director (random catastrophes, NPC shelter evacuation, Space Health)
        self.catastrophe_director.update(dt, self.player.position)

        # Update modal and minigame timers
        self.situation_modal.update(dt)
        self.challenge_minigame.update(dt)

        # 4. Check Collectibles Proximity Pickup
        collected = self.collectibles.update(dt, self.player.position)
        if collected:
            self.audio.play("pickup")
            self.particle_fx.spawn_celebration_burst(collected.world_x, collected.world_y, particle_type="spark")
            self.floating_text.spawn(f"+{collected.science_points} SCIENCE! {collected.name}", collected.world_x, collected.world_y - 25, color=collected.color, big=True)
            self.player.state.set_action_feedback(f"Discovered: {collected.name} (+{collected.science_points} pts)", True, duration=3.5)

        # Update transient visual systems, NPCs, and Grid Stations
        self.particle_fx.update(dt)
        self.floating_text.update(dt)
        self.npc_system.update(dt, self.player.position)
        self.grid_challenges.update(dt)

        # Update environmental lighting and dust particles
        self.env_animator.update(dt, self.world_state)

        # 5. Movement input & Player state update
        dx, dy = self.input_handler.get_movement_vector()
        sprint = self.input_handler.is_sprinting()
        self.player.handle_input(dx, dy, sprint=sprint)

        # Footsteps and sprint particles
        if self.player.movement.has_footstep:
            self.audio.play("footstep")
            self.particle_fx.spawn_footstep_puff(self.player.position.x, self.player.position.y + self.player.height // 2 - 2, self.player.movement.velocity)

        if self.player.movement.just_landed:
            self.audio.play("land")
            self.particle_fx.spawn_landing_ring(self.player.position.x, self.player.position.y + self.player.height // 2 - 2)

        if sprint and self.player.movement.velocity.length_squared() > 0:
            self.particle_fx.spawn_thruster_plume(self.player.position.x, self.player.position.y, self.player.movement.velocity)

        movement_telemetry = self.player.update(dt, self.mars_base)
        if movement_telemetry:
            self.sync.report_movement(
                distance_meters=movement_telemetry["distance_meters"],
                speed_ms=movement_telemetry["speed_ms"],
                heading_deg=movement_telemetry["heading_deg"],
                world_position=movement_telemetry["world_position"]
            )

        # 6. Camera follow tracking
        self.camera.update(self.player.position, dt)

        # 7. Check facility proximity and outside/EVA environment status
        self.nearby_facility = self.mars_base.get_nearby_facility((self.player.position.x, self.player.position.y))
        is_outside, loc_name = self.mars_base.get_location_info(self.player.position.x, self.player.position.y)
        self.player.state.is_outside = is_outside
        self.player.state.location_name = loc_name

        return True

    def render(self, surface: pygame.Surface) -> None:
        """Draw complete scene layers."""
        # 1. Clear display
        surface.fill(COLOR_BG)

        # 2. Render background in camera coordinate space
        self.mars_base.render(surface, self.camera)

        # 3. Render 15 Grid Challenge Station markers [ ★ ]
        self.grid_challenges.render(surface, self.camera, self.player.position)

        # 4. Render collectible science artifacts
        self.collectibles.render(surface, self.camera)

        # 5. Render particle FX (dust foot puffs, thruster plumes, landing rings)
        self.particle_fx.render(surface, self.camera)

        # 6. Render Crew NPCs (Amal, Gowri, Christy)
        self.npc_system.render(surface, self.camera, self.player.position)

        # 7. Render player character (Commander Suso) in camera space
        self.player.render(surface, self.camera)

        # 8. Render floating reward text popups
        self.floating_text.render(surface, self.camera)

        # 9. Render atmospheric lighting and original dust particles
        self.env_animator.render(surface, self.world_state)

        # 10. Render 8-Bit Retro Collapsible HUD
        nearby_npc = self.npc_system.get_nearby_npc(self.player.position)
        nearby_station = self.grid_challenges.get_nearby_station(self.player.position)
        self.hud.render(
            surface=surface,
            world_state=self.world_state,
            player_state=self.player.state,
            backend_url=self.sync.config.base_url,
            show_help=self.input_handler.show_help,
            show_debug=self.input_handler.show_debug,
            show_live_feed=self.input_handler.show_live_feed,
            nearby_facility=self.nearby_facility,
            active_crew_id=self.player.animation.character_id,
            mission_system=self.mission_system,
            base_facilities=self.mars_base.facilities,
            collectibles=self.collectibles,
            grid_challenges=self.grid_challenges,
            nearby_npc=nearby_npc,
            nearby_station=nearby_station,
        )

        # 11. Render situation injector modal overlay when open
        self.situation_modal.render(surface, self.world_state)

        # 12. Render interactive facility challenge minigame when active
        self.challenge_minigame.render(surface)

        # 13. Render Game Over overlay if crew died / failed
        if self.catastrophe_director.is_game_over:
            self._render_game_over(surface)

    def _render_game_over(self, surface: pygame.Surface) -> None:
        """Render retro arcade Game Over / Mission Failed death screen."""
        from ui.font_manager import FontManager

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((14, 4, 6, 235))
        surface.blit(overlay, (0, 0))

        box_w = 760
        box_h = 320
        box_x = (WINDOW_WIDTH - box_w) // 2
        box_y = (WINDOW_HEIGHT - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(surface, (20, 8, 10), box_rect)
        pygame.draw.rect(surface, (255, 60, 60), box_rect, width=3)
        pygame.draw.rect(surface, (180, 40, 40), (box_x + 4, box_y + 4, box_w - 8, box_h - 8), width=1)

        font_big = FontManager.get(20, bold=True)
        font_med = FontManager.get(13, bold=True)
        font_body = FontManager.get(11)

        title = font_big.render("☠  MISSION FAILED // EXPEDITION LOST  ☠", True, (255, 60, 60))
        surface.blit(title, (box_x + (box_w - title.get_width()) // 2, box_y + 24))

        sub = font_med.render("ALL CREW MEMBERS PERISHED ON MARS", True, (255, 180, 80))
        surface.blit(sub, (box_x + (box_w - sub.get_width()) // 2, box_y + 64))

        pygame.draw.line(surface, (150, 40, 40), (box_x + 40, box_y + 96), (box_x + box_w - 40, box_y + 96), 1)

        desc1 = font_body.render("CAUSE OF DEATH: CRITICAL HABITAT DECOMPRESSION & LIFE SUPPORT COLLAPSE", True, (240, 240, 245))
        surface.blit(desc1, (box_x + (box_w - desc1.get_width()) // 2, box_y + 115))

        reason_text = self.catastrophe_director.game_over_reason or "Emergency catastrophe unaddressed for over 1.30 minutes (90 seconds)."
        desc2 = font_body.render(f"\"{reason_text}\"", True, (255, 140, 140))
        surface.blit(desc2, (box_x + (box_w - desc2.get_width()) // 2, box_y + 140))

        status_text = font_body.render("Space Health: 0%  |  Atmospheric Pressure: 0.0 kPa  |  O2 Reserves: 0.0 kg", True, (150, 160, 180))
        surface.blit(status_text, (box_x + (box_w - status_text.get_width()) // 2, box_y + 175))

        prompt_box = pygame.Rect(box_x + 80, box_y + 225, box_w - 160, 50)
        pygame.draw.rect(surface, (30, 12, 16), prompt_box)
        pygame.draw.rect(surface, (255, 200, 0), prompt_box, width=1)

        retry = font_med.render("[R] RETRY MISSION & REVIVE CREW", True, (0, 255, 200))
        surface.blit(retry, (prompt_box.x + 20, prompt_box.y + 16))

        quit_txt = font_med.render("[ESC] QUIT SIMULATION", True, (255, 80, 80))
        surface.blit(quit_txt, (prompt_box.right - quit_txt.get_width() - 20, prompt_box.y + 16))
