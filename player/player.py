"""MARS SURVIVAL — Player Entity.

Integrates movement controller, low-gravity hop physics, animation controller,
and world state tracking into a unified Pygame player component.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import pygame
from config import DEFAULT_SPAWN_X, DEFAULT_SPAWN_Y, PLAYER_RADIUS
from world.player_state import PlayerState
from .movement import MovementController
from .animation import AnimationController


class Player:
    """Player-controlled 2D astronaut character."""

    def __init__(self, x: float = DEFAULT_SPAWN_X, y: float = DEFAULT_SPAWN_Y) -> None:
        self.position = pygame.Vector2(x, y)
        self.movement = MovementController()
        # Commander Suso (Sprite 1) is the primary playable mission commander
        self.animation = AnimationController(character_id=1)
        self.state = PlayerState(x=x, y=y)

        # Bounding box dimensions matching astronaut sprite (33 x 56 px)
        self.width = 32
        self.height = 56
        self.radius = PLAYER_RADIUS

    def switch_character(self, character_id: int = 1) -> None:
        """Switch active astronaut crew member."""
        if character_id not in (1, 2, 3, 4):
            character_id = 1

        self.animation.load_crew_character(character_id)
        self.state.active_crew_id = character_id

        from config import CREW_MEMBERS
        crew_info = CREW_MEMBERS.get(character_id, {"name": f"Astronaut {character_id}", "role": "Crew Member"})
        name = crew_info["name"]
        role = crew_info["role"]
        self.state.set_action_feedback(f"Active Operator: {name} // {role}", True, duration=3.0)

    @property
    def velocity(self) -> pygame.Vector2:
        return self.movement.velocity

    def handle_input(self, dx: float, dy: float, sprint: bool = False) -> None:
        """Forward raw keyboard inputs (WASD / Arrows) and sprint state to movement controller."""
        self.movement.update_input(dx, dy, sprint=sprint)

    def hop(self) -> bool:
        """Trigger low-gravity Martian hop."""
        return self.movement.start_jump()

    def update(self, dt: float, environment_or_rect: Any) -> Optional[Dict[str, Any]]:
        """Update player position, animations, state, and telemetry.
        
        Performs axis-separated movement to prevent walking over walls
        and enable smooth wall sliding along diagonal obstacles.
        """
        # Resolve environment collision interface and world bounding rect
        mars_base = environment_or_rect if hasattr(environment_or_rect, "check_foot_collision") else None
        world_rect = environment_or_rect.world_rect if mars_base else environment_or_rect

        # 1. Calculate displacement from delta time
        displacement = self.movement.calculate_displacement(dt)

        # 2. Axis-separated movement with wall collision & boundary clamping
        min_x = world_rect.left + self.width // 2
        max_x = world_rect.right - self.width // 2
        min_y = world_rect.top + self.height // 2
        max_y = world_rect.bottom - self.height // 2

        # Try horizontal movement (X axis)
        if displacement.x != 0:
            target_x = max(min_x, min(self.position.x + displacement.x, max_x))
            if mars_base:
                if not mars_base.check_foot_collision(target_x, self.position.y):
                    self.position.x = target_x
            else:
                self.position.x = target_x

        # Try vertical movement (Y axis) - allows sliding along walls if diagonal
        if displacement.y != 0:
            target_y = max(min_y, min(self.position.y + displacement.y, max_y))
            if mars_base:
                if not mars_base.check_foot_collision(self.position.x, target_y):
                    self.position.y = target_y
            else:
                self.position.y = target_y

        # 3. Synchronize player state model
        self.state.x = self.position.x
        self.state.y = self.position.y
        self.state.facing_direction = self.animation.facing_direction
        self.state.current_action = "HOPPING" if self.movement.jump_z > 0.0 else ("MOVING" if self.movement.velocity.length_squared() > 0 else "IDLE")
        self.state.update_timers(dt)

        # 4. Update animation controller
        self.animation.update(self.movement.input_vector, dt)

        # 5. Check if periodic movement telemetry should be dispatched to MARS-EIS
        telemetry = self.movement.track_movement(self.position, dt)
        return telemetry

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        """Render character frame and dynamic shadow at camera-transformed screen coordinates."""
        screen_pos = camera.world_to_screen(self.position.x, self.position.y)
        jump_z = self.movement.jump_z

        # 1. Subtle ground shadow beneath astronaut (scales with hop elevation)
        shadow_w = max(12, int(24 - jump_z * 0.22))
        shadow_h = max(4, int(8 - jump_z * 0.08))
        shadow_alpha = max(20, int(85 - jump_z * 0.9))

        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (0, 0, shadow_w, shadow_h))
        surface.blit(shadow_surf, (int(screen_pos.x - shadow_w // 2), int(screen_pos.y + self.height // 2 - shadow_h // 2)))

        # 2. Main character frame (elevated vertically by jump_z)
        frame = self.animation.get_current_frame()
        render_y = screen_pos.y - jump_z
        frame_rect = frame.get_rect(center=(int(screen_pos.x), int(render_y)))
        surface.blit(frame, frame_rect.topleft)

    def get_world_rect(self) -> pygame.Rect:
        """Return player bounding rectangle in world space."""
        rect = pygame.Rect(0, 0, self.width, self.height)
        rect.center = (int(self.position.x), int(self.position.y))
        return rect
