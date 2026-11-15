"""MARS SURVIVAL — Autonomous Base Door & Airlock System.

Simulates motorized sci-fi blast doors, airlocks, and facility bulkheads that
automatically detect nearby astronauts, slide open smoothly with pneumatic
sound effects and visual status indicators, and re-seal when the astronaut departs.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
import math
from typing import Dict, List, Optional, Tuple, Any
import pygame

from config import WORLD_SCALE, CREDIT_INFO
from systems.camera import Camera


class DoorAudio:
    """Manages pneumatic airlock and blast door sound effects."""

    def __init__(self) -> None:
        self.open_sound: Optional[pygame.mixer.Sound] = None
        self.close_sound: Optional[pygame.mixer.Sound] = None
        self.last_sound_time: float = 0.0
        self.min_interval: float = 0.12  # Throttle overlapping sounds
        self._load_sounds()

    def _load_sounds(self) -> None:
        """Attempt to load procedural sound effects if mixer is active."""
        if not pygame.mixer.get_init():
            return

        open_path = "assets/audio/door_open.wav"
        close_path = "assets/audio/door_close.wav"

        try:
            if os.path.exists(open_path):
                self.open_sound = pygame.mixer.Sound(open_path)
                self.open_sound.set_volume(0.35)
            if os.path.exists(close_path):
                self.close_sound = pygame.mixer.Sound(close_path)
                self.close_sound.set_volume(0.35)
        except Exception:
            self.open_sound = None
            self.close_sound = None

    def play_open(self, current_time: float = 0.0) -> None:
        """Play pneumatic door opening sound."""
        if self.open_sound and (current_time - self.last_sound_time >= self.min_interval):
            try:
                self.open_sound.play()
                self.last_sound_time = current_time
            except Exception:
                pass

    def play_close(self, current_time: float = 0.0) -> None:
        """Play pneumatic door closing sound."""
        if self.close_sound and (current_time - self.last_sound_time >= self.min_interval):
            try:
                self.close_sound.play()
                self.last_sound_time = current_time
            except Exception:
                pass


class Door:
    """Represents a single automated sliding bulkhead or airlock door."""

    def __init__(
        self,
        door_id: str,
        name: str,
        base_cx: float,
        base_cy: float,
        base_w: float,
        base_h: float,
        orientation: str,  # "horizontal" or "vertical"
        scale: float = WORLD_SCALE,
        proximity_radius: float = 95.0,  # pixels in world coordinates (~24m)
        open_speed: float = 2.8,  # opens fully in ~0.35 seconds
        close_delay: float = 0.85,  # hold open time after player exits radius
    ) -> None:
        self.door_id = door_id
        self.name = name
        self.orientation = orientation  # "horizontal" = splits L/R; "vertical" = splits U/D

        # World coordinates (scaled)
        self.cx = base_cx * scale
        self.cy = base_cy * scale
        self.width = base_w * scale
        self.height = base_h * scale

        # Bounding rect in world coordinates when fully closed
        self.rect = pygame.Rect(
            int(self.cx - self.width / 2.0),
            int(self.cy - self.height / 2.0),
            int(self.width),
            int(self.height),
        )

        self.proximity_radius = proximity_radius or 140.0
        self.open_speed = open_speed or 4.0
        self.close_delay = close_delay or 1.2

        # Dynamic state
        self.state: str = "CLOSED"  # "CLOSED", "OPENING", "OPEN", "CLOSING"
        self.open_ratio: float = 0.0  # 0.0 = fully closed, 1.0 = fully open
        self.close_timer: float = 0.0
        self.is_player_nearby: bool = False
        self.sensor_pulse: float = 0.0
        self.total_time: float = 0.0

    def is_blocking(self) -> bool:
        """Returns True only if door is completely closed and player is not approaching."""
        if self.is_player_nearby or self.open_ratio > 0.05:
            return False
        return self.open_ratio < 0.2

    def check_collision(self, world_x: float, world_y: float) -> bool:
        """Check if footprint at (world_x, world_y) collides with closed door."""
        if not self.is_blocking():
            return False

        # In horizontal doors, depth is height; in vertical doors, depth is width.
        # Check if point falls within the door boundary rectangle
        return self.rect.collidepoint(int(world_x), int(world_y))

    def update(
        self,
        dt: float,
        player_pos: Tuple[float, float],
        audio: Optional[DoorAudio] = None,
    ) -> None:
        """Update proximity detection, state transitions, and slide animation."""
        self.total_time += dt
        self.sensor_pulse = (self.sensor_pulse + dt * 5.0) % (math.pi * 2)

        px, py = player_pos
        dist = math.hypot(px - self.cx, py - self.cy)

        # Proximity detection
        nearby = dist <= self.proximity_radius
        self.is_player_nearby = nearby

        if nearby:
            # Player is nearby: trigger open and refresh hold timer
            self.close_timer = self.close_delay
            if self.state in ("CLOSED", "CLOSING"):
                self.state = "OPENING"
                if audio:
                    audio.play_open(self.total_time)
        else:
            # Player is outside radius: count down hold timer before closing
            if self.state == "OPEN":
                self.close_timer -= dt
                if self.close_timer <= 0.0:
                    self.state = "CLOSING"
                    if audio:
                        audio.play_close(self.total_time)

        # Slide animation interpolation
        if self.state == "OPENING":
            self.open_ratio += self.open_speed * dt
            if self.open_ratio >= 1.0:
                self.open_ratio = 1.0
                self.state = "OPEN"
        elif self.state == "CLOSING":
            self.open_ratio -= self.open_speed * dt
            if self.open_ratio <= 0.0:
                self.open_ratio = 0.0
                self.state = "CLOSED"

    def render(self, surface: pygame.Surface, camera: Camera) -> None:
        """Render animated door panels, track frames, and status LEDs in camera space."""
        # Convert world coordinates to camera viewport screen coordinates
        screen_x = self.rect.x - camera.offset_x
        screen_y = self.rect.y - camera.offset_y

        view_w, view_h = camera.viewport_width, camera.viewport_height
        # Early-out if outside visible viewport
        if (
            screen_x + self.width + 50 < 0
            or screen_x - 50 > view_w
            or screen_y + self.height + 50 < 0
            or screen_y - 50 > view_h
        ):
            return

        door_screen_rect = pygame.Rect(int(screen_x), int(screen_y), int(self.width), int(self.height))

        # Status LED color based on state
        pulse_alpha = 0.7 + 0.3 * math.sin(self.sensor_pulse)
        if self.open_ratio > 0.8:
            led_color = (0, 235, 140)  # Bright Green (OPEN)
        elif self.state == "OPENING" or self.open_ratio > 0.2:
            led_color = (0, 220, 255)  # Cyan (AUTHORIZING / MOVING)
        else:
            led_color = (int(255 * pulse_alpha), 45, 45)  # Pulsing Red (SEALED)

        if self.orientation == "horizontal":
            self._render_horizontal(surface, door_screen_rect, led_color)
        else:
            self._render_vertical(surface, door_screen_rect, led_color)

    def _render_horizontal(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        led_color: Tuple[int, int, int],
    ) -> None:
        """Render horizontal door (corridor runs North-South, panels split Left/Right)."""
        w = rect.width
        h = rect.height
        half_w = w / 2.0
        slide_offset = half_w * self.open_ratio

        # 1. Floor track rails (top and bottom runner tracks)
        rail_color = (25, 30, 42)
        pygame.draw.line(surface, rail_color, (rect.left - 2, rect.top), (rect.right + 2, rect.top), width=2)
        pygame.draw.line(surface, rail_color, (rect.left - 2, rect.bottom), (rect.right + 2, rect.bottom), width=2)

        # 2. Glowing cyan threshold line when opening or open
        if self.open_ratio > 0.05:
            thresh_glow = (0, 220, 255)
            pygame.draw.line(surface, thresh_glow, (rect.left, rect.centery), (rect.right, rect.centery), width=2)

        # 3. Sliding Blast Door Panels (fade and retract cleanly into frame)
        if self.open_ratio < 0.92:
            panel_alpha = int((1.0 - self.open_ratio) * 230)
            panel_surf = pygame.Surface((w + 20, h), pygame.SRCALPHA)

            lp_x = int(half_w - slide_offset)
            rp_x = int(half_w + slide_offset)

            # Left panel
            pygame.draw.rect(panel_surf, (40, 48, 62, panel_alpha), (0, 0, lp_x, h))
            pygame.draw.line(panel_surf, (70, 84, 108, panel_alpha), (0, 0), (lp_x, 0), width=1)
            pygame.draw.line(panel_surf, led_color + (panel_alpha,), (lp_x - 1, 0), (lp_x - 1, h), width=2)

            # Right panel
            pygame.draw.rect(panel_surf, (40, 48, 62, panel_alpha), (rp_x, 0, w - rp_x, h))
            pygame.draw.line(panel_surf, (70, 84, 108, panel_alpha), (rp_x, 0), (w, 0), width=1)
            pygame.draw.line(panel_surf, led_color + (panel_alpha,), (rp_x, 0), (rp_x, h), width=2)

            surface.blit(panel_surf, (rect.left, rect.top))

        # 4. Slim door frame jambs
        jamb_w = 4
        pygame.draw.rect(surface, (25, 30, 42), (rect.left - jamb_w, rect.top - 1, jamb_w, h + 2))
        pygame.draw.rect(surface, (25, 30, 42), (rect.right, rect.top - 1, jamb_w, h + 2))

        # Sensor beacon dot
        sensor_col = (0, 240, 255) if self.is_player_nearby else (80, 100, 120)
        pygame.draw.circle(surface, sensor_col, (rect.centerx, rect.top - 3), 3)

    def _render_vertical(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        led_color: Tuple[int, int, int],
    ) -> None:
        """Render vertical door (corridor runs East-West, panels split Up/Down)."""
        w = rect.width
        h = rect.height
        half_h = h / 2.0
        slide_offset = half_h * self.open_ratio

        # 1. Floor track rails (left and right runner tracks)
        rail_color = (25, 30, 42)
        pygame.draw.line(surface, rail_color, (rect.left, rect.top - 2), (rect.left, rect.bottom + 2), width=2)
        pygame.draw.line(surface, rail_color, (rect.right, rect.top - 2), (rect.right, rect.bottom + 2), width=2)

        # 2. Glowing cyan threshold line when open
        if self.open_ratio > 0.05:
            thresh_glow = (0, 220, 255)
            pygame.draw.line(surface, thresh_glow, (rect.centerx, rect.top), (rect.centerx, rect.bottom), width=2)

        # 3. Sliding Blast Door Panels (fade and retract cleanly into frame)
        if self.open_ratio < 0.92:
            panel_alpha = int((1.0 - self.open_ratio) * 230)
            panel_surf = pygame.Surface((w, h + 20), pygame.SRCALPHA)

            tp_h = int(half_h - slide_offset)
            bp_y = int(half_h + slide_offset)

            # Top panel
            pygame.draw.rect(panel_surf, (40, 48, 62, panel_alpha), (0, 0, w, tp_h))
            pygame.draw.line(panel_surf, (70, 84, 108, panel_alpha), (0, 0), (0, tp_h), width=1)
            pygame.draw.line(panel_surf, led_color + (panel_alpha,), (0, tp_h - 1), (w, tp_h - 1), width=2)

            # Bottom panel
            pygame.draw.rect(panel_surf, (40, 48, 62, panel_alpha), (0, bp_y, w, h - bp_y))
            pygame.draw.line(panel_surf, (70, 84, 108, panel_alpha), (0, bp_y), (0, h), width=1)
            pygame.draw.line(panel_surf, led_color + (panel_alpha,), (0, bp_y), (w, bp_y), width=2)

            surface.blit(panel_surf, (rect.left, rect.top))

        # 4. Slim door frame jambs
        jamb_h = 4
        pygame.draw.rect(surface, (25, 30, 42), (rect.left - 1, rect.top - jamb_h, w + 2, jamb_h))
        pygame.draw.rect(surface, (25, 30, 42), (rect.left - 1, rect.bottom, w + 2, jamb_h))

        # Sensor beacon dot
        sensor_col = (0, 240, 255) if self.is_player_nearby else (80, 100, 120)
        pygame.draw.circle(surface, sensor_col, (rect.right + 3, rect.centery), 3)


# Standard registry of all 11 Mars base airlocks and bulkheads aligned with map artwork
BASE_DOORS_CONFIG = [
    {
        "id": "reactor_door",
        "name": "Nuclear Reactor Bulkhead",
        "cx": 512, "cy": 175, "w": 56, "h": 16,
        "orientation": "horizontal",
    },
    {
        "id": "generator_door",
        "name": "Power Generator Bulkhead",
        "cx": 512, "cy": 455, "w": 56, "h": 16,
        "orientation": "horizontal",
    },
    {
        "id": "south_exterior_door",
        "name": "South Surface Airlock",
        "cx": 512, "cy": 638, "w": 56, "h": 16,
        "orientation": "horizontal",
    },
    {
        "id": "medbay_door",
        "name": "Medbay Airlock",
        "cx": 366, "cy": 375, "w": 16, "h": 50,
        "orientation": "vertical",
    },
    {
        "id": "water_door",
        "name": "Water Recycling Hatch",
        "cx": 645, "cy": 375, "w": 16, "h": 50,
        "orientation": "vertical",
    },
    {
        "id": "comms_door",
        "name": "Communications Bulkhead",
        "cx": 445, "cy": 280, "w": 42, "h": 16,
        "orientation": "horizontal",
    },
    {
        "id": "command_door",
        "name": "Command Lab Hatch",
        "cx": 575, "cy": 280, "w": 42, "h": 16,
        "orientation": "horizontal",
    },
    {
        "id": "greenhouse_door",
        "name": "Hydroponics Bulkhead",
        "cx": 445, "cy": 470, "w": 42, "h": 16,
        "orientation": "horizontal",
    },
    {
        "id": "workshop_door",
        "name": "Workshop Bulkhead",
        "cx": 575, "cy": 470, "w": 42, "h": 16,
        "orientation": "horizontal",
    },
    {
        "id": "oxygen_door",
        "name": "Oxygen Generation Bulkhead",
        "cx": 838, "cy": 560, "w": 16, "h": 48,
        "orientation": "vertical",
    },
    {
        "id": "west_airlock_door",
        "name": "West EVA Airlock",
        "cx": 36, "cy": 360, "w": 16, "h": 48,
        "orientation": "vertical",
    },
    {
        "id": "east_airlock_door",
        "name": "East Pad Airlock",
        "cx": 944, "cy": 270, "w": 16, "h": 48,
        "orientation": "vertical",
    },
]


class DoorManager:
    """Manages all animated base doors, state transitions, audio, and collision."""

    def __init__(self, door_configs: Optional[List[Dict[str, Any]]] = None) -> None:
        configs = door_configs or BASE_DOORS_CONFIG
        self.doors: List[Door] = []
        self.doors_by_id: Dict[str, Door] = {}
        self.audio = DoorAudio()

        for cfg in configs:
            door = Door(
                door_id=cfg["id"],
                name=cfg["name"],
                base_cx=float(cfg["cx"]),
                base_cy=float(cfg["cy"]),
                base_w=float(cfg["w"]),
                base_h=float(cfg["h"]),
                orientation=cfg["orientation"],
                scale=WORLD_SCALE,
                proximity_radius=140.0,
                open_speed=4.0,
                close_delay=1.2,
            )
            self.doors.append(door)
            self.doors_by_id[door.door_id] = door

    def update(self, dt: float, player_pos: Tuple[float, float]) -> None:
        """Update all doors with player proximity and animate slide states."""
        for door in self.doors:
            door.update(dt, player_pos, self.audio)

    def render(self, surface: pygame.Surface, camera: Camera) -> None:
        """Render all visible doors within camera viewport."""
        for door in self.doors:
            door.render(surface, camera)

    def check_collision(self, world_x: float, world_y: float) -> bool:
        """Check if position intersects any closed door blocking movement."""
        for door in self.doors:
            if door.check_collision(world_x, world_y):
                return True
        return False

    def get_nearby_door(self, player_pos: Tuple[float, float], radius: float = 110.0) -> Optional[Door]:
        """Return the closest door within detection radius, if any."""
        px, py = player_pos
        closest: Optional[Door] = None
        closest_dist = radius
        for door in self.doors:
            d = math.hypot(px - door.cx, py - door.cy)
            if d < closest_dist:
                closest_dist = d
                closest = door
        return closest
