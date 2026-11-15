"""MARS SURVIVAL — Input Handling System.

Processes keyboard and window events, maps movement directions (WASD + Arrows),
and triggers interactive player actions with MARS-EIS.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
from typing import Tuple, List, Dict, Any, Optional
import pygame


class InputHandler:
    """Centralizes event capture and action key mapping."""

    def __init__(self) -> None:
        self.show_help: bool = False
        self.show_debug: bool = False
        self.show_live_feed: bool = False

    def process_events(self, modal_key_handler: Optional[Any] = None) -> Tuple[bool, List[str]]:
        """Process Pygame event queue.
        
        Args:
            modal_key_handler: Optional callable(key: int) -> bool. If returns True,
                the key event is absorbed by the active modal dialog.
        
        Returns:
            Tuple of (should_quit: bool, action_triggers: List[str])
        """
        should_quit = False
        action_triggers: List[str] = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                should_quit = True

            elif event.type == pygame.KEYDOWN:
                # If a modal dialog absorbs this key, do not trigger normal actions
                if modal_key_handler and modal_key_handler(event.key):
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.show_help:
                        self.show_help = False
                    elif self.show_live_feed:
                        self.show_live_feed = False
                    else:
                        should_quit = True

                # Real-Time Live Feed Inspector Toggle
                elif event.key == pygame.K_F5:
                    self.show_live_feed = not self.show_live_feed

                # MARS-EIS Situation Injector / Catastrophe Scenarios Modal
                elif event.key in (pygame.K_t, pygame.K_F4):
                    action_triggers.append("TOGGLE_SITUATIONS")

                # Interactive Action Triggers
                elif event.key == pygame.K_e:
                    action_triggers.append("HABITAT_INTERACTION")
                elif event.key == pygame.K_c:
                    action_triggers.append("CLEAN_SOLAR_PANELS")
                elif event.key == pygame.K_x:
                    action_triggers.append("EXCAVATE")
                elif event.key == pygame.K_SPACE:
                    action_triggers.append("PLAYER_HOP")

                # Character Crew Member Selection (1-4 or Tab)
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    action_triggers.append("SELECT_CHAR_1")
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    action_triggers.append("SELECT_CHAR_2")
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    action_triggers.append("SELECT_CHAR_3")
                elif event.key in (pygame.K_4, pygame.K_KP4):
                    action_triggers.append("SELECT_CHAR_4")
                elif event.key == pygame.K_TAB:
                    action_triggers.append("CYCLE_CHAR")

                # UI Toggles
                elif event.key == pygame.K_h:
                    action_triggers.append("TOGGLE_HUD")
                elif event.key == pygame.K_F1:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_F2:
                    action_triggers.append("FORCE_RECONNECT")
                elif event.key == pygame.K_F3:
                    self.show_debug = not self.show_debug

        return should_quit, action_triggers

    def get_movement_vector(self) -> Tuple[float, float]:
        """Poll continuous keyboard state for WASD and Arrow keys."""
        keys = pygame.key.get_pressed()

        dx = 0.0
        dy = 0.0

        # Horizontal movement (A/Left vs D/Right)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        # Vertical movement (W/Up vs S/Down)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0

        return dx, dy

    def is_sprinting(self) -> bool:
        """Check if Shift key is held for EVA sprint."""
        keys = pygame.key.get_pressed()
        return bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
