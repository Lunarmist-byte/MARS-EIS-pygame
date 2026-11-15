"""MARS SURVIVAL — Interactive Facility Challenge Minigame System.

Provides engaging arcade-style calibration and button-mashing minigames:
- "SWEET_SPOT": Dynamic oscillating needle resonance alignment
- "RAPID_TAP": Rapid button-mashing charge gauge frenzy (unboxing crates, turbo revving)

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
import random
from typing import Optional, Tuple, Dict, Any, Callable
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_ACCENT_MARS,
    COLOR_NOMINAL,
    COLOR_WARNING,
    COLOR_CRITICAL,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_HIGHLIGHT,
)


class ChallengeMinigame:
    """Manages an active facility calibration challenge session."""

    def __init__(self) -> None:
        self.is_active: bool = False
        self.facility_id: str = ""
        self.facility_name: str = ""
        self.objective_text: str = ""
        self.reward_text: str = ""
        self.mode: str = "SWEET_SPOT"  # "SWEET_SPOT" or "RAPID_TAP"

        # Sweet-Spot Mode
        self.needle_pos: float = 0.0
        self.needle_speed: float = 1.35
        self.needle_dir: float = 1.0
        self.target_zone: Tuple[float, float] = (0.42, 0.58)
        self.locks_required: int = 3
        self.locks_achieved: int = 0

        # Rapid-Tap Mode
        self.tap_progress: float = 0.0
        self.tap_decay: float = 0.32

        # Timers & Visuals
        self.time_remaining: float = 18.0
        self.feedback_text: str = ""
        self.feedback_color: Tuple[int, int, int] = COLOR_NOMINAL
        self.feedback_timer: float = 0.0
        self.shake_trauma: float = 0.0

        # Callback
        self.on_success: Optional[Callable[[], None]] = None

    def start_challenge(
        self,
        facility_id: str,
        facility_name: str,
        objective: str,
        reward_desc: str,
        on_success_callback: Callable[[], None],
        mode: str = "SWEET_SPOT",
    ) -> None:
        """Launch interactive minigame for this facility or grid station."""
        self.is_active = True
        self.facility_id = facility_id
        self.facility_name = facility_name
        self.objective_text = objective
        self.reward_text = reward_desc
        self.on_success = on_success_callback
        self.mode = mode

        self.needle_pos = 0.0
        self.needle_dir = 1.0
        self.needle_speed = random.uniform(1.2, 1.7)
        spread = random.uniform(0.12, 0.18)
        center = random.uniform(0.35, 0.65)
        self.target_zone = (center - spread / 2.0, center + spread / 2.0)

        self.locks_required = 3
        self.locks_achieved = 0

        self.tap_progress = 0.0
        self.tap_decay = 0.34

        self.time_remaining = 18.0 if mode == "SWEET_SPOT" else 10.0
        if mode == "RAPID_TAP":
            self.feedback_text = "MASH [SPACE] OR [E] RAPIDLY TO CHARGE GAUGE!"
        else:
            self.feedback_text = "PRESS [SPACE] OR [E] WHEN NEEDLE IS IN GREEN ZONE!"

        self.feedback_color = COLOR_TEXT_HIGHLIGHT
        self.feedback_timer = 2.5
        self.shake_trauma = 0.0

    def handle_key(self, key: int, audio: Any = None) -> bool:
        """Process player tap on Space, E, or Enter."""
        if not self.is_active:
            return False

        if key == pygame.K_ESCAPE:
            self.is_active = False
            if audio:
                audio.play("beep")
            return True

        if key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
            # ---------------------------------------------------------
            # RAPID-TAP MODE (Button-mashing frenzy)
            # ---------------------------------------------------------
            if self.mode == "RAPID_TAP":
                self.tap_progress += 0.15
                if audio:
                    audio.play("beep")
                if self.tap_progress >= 1.0:
                    self.tap_progress = 1.0
                    self.feedback_text = f"MAX CHARGE ACHIEVED! {self.reward_text}"
                    self.feedback_color = COLOR_NOMINAL
                    if audio:
                        audio.play("success")
                    if self.on_success:
                        self.on_success()
                    self.is_active = False
                return True

            # ---------------------------------------------------------
            # SWEET-SPOT MODE (Timing alignment)
            # ---------------------------------------------------------
            low, high = self.target_zone
            if low <= self.needle_pos <= high:
                self.locks_achieved += 1
                if audio:
                    audio.play("beep")

                if self.locks_achieved >= self.locks_required:
                    self.feedback_text = f"CALIBRATION COMPLETE! {self.reward_text}"
                    self.feedback_color = COLOR_NOMINAL
                    self.feedback_timer = 2.0
                    if audio:
                        audio.play("success")
                    if self.on_success:
                        self.on_success()
                    self.is_active = False
                    return True
                else:
                    self.feedback_text = f"LOCK #{self.locks_achieved} SECURED! RE-ALIGNING..."
                    self.feedback_color = COLOR_NOMINAL
                    self.feedback_timer = 1.2
                    self.needle_speed += 0.25
                    spread = random.uniform(0.10, 0.16)
                    center = random.uniform(0.25, 0.75)
                    self.target_zone = (center - spread / 2.0, center + spread / 2.0)
            else:
                self.shake_trauma = 0.5
                self.feedback_text = "CALIBRATION MISALIGNED! TRY AGAIN!"
                self.feedback_color = COLOR_CRITICAL
                self.feedback_timer = 1.0
                if audio:
                    audio.play("fail")

            return True

        return False

    def update(self, dt: float) -> None:
        """Advance timers and needle/charge animation."""
        if not self.is_active:
            return

        self.time_remaining = max(0.0, self.time_remaining - dt)
        if self.time_remaining <= 0.0:
            self.is_active = False
            return

        if self.shake_trauma > 0:
            self.shake_trauma = max(0.0, self.shake_trauma - dt * 2.0)

        if self.mode == "RAPID_TAP":
            self.tap_progress = max(0.0, self.tap_progress - self.tap_decay * dt)
        else:
            self.needle_pos += self.needle_dir * self.needle_speed * dt
            if self.needle_pos >= 1.0:
                self.needle_pos = 1.0
                self.needle_dir = -1.0
            elif self.needle_pos <= 0.0:
                self.needle_pos = 0.0
                self.needle_dir = 1.0

        if self.feedback_timer > 0:
            self.feedback_timer -= dt

    def render(self, surface: pygame.Surface) -> None:
        """Render 8-bit retro arcade challenge dialog."""
        if not self.is_active:
            return

        modal_w = 640
        modal_h = 280
        shake_x = math.sin(pygame.time.get_ticks() * 0.05) * (self.shake_trauma * 10.0)
        shake_y = math.cos(pygame.time.get_ticks() * 0.07) * (self.shake_trauma * 10.0)

        rect = pygame.Rect(
            int((WINDOW_WIDTH - modal_w) // 2 + shake_x),
            int((WINDOW_HEIGHT - modal_h) // 2 + shake_y),
            modal_w,
            modal_h,
        )

        # 8-bit solid panel with sharp border
        pygame.draw.rect(surface, (8, 12, 18), rect)
        pygame.draw.rect(surface, (0, 229, 255), rect, width=2)
        pygame.draw.rect(surface, (0, 160, 200), (rect.x + 3, rect.y + 3, modal_w - 6, modal_h - 6), width=1)

        font_large = pygame.font.SysFont("Consolas", 15, bold=True)
        font_med = pygame.font.SysFont("Consolas", 12, bold=True)
        font_small = pygame.font.SysFont("Consolas", 11)

        # Header
        hdr = font_large.render(f"CHALLENGE // {self.facility_name.upper()}", True, (255, 215, 0))
        surface.blit(hdr, (rect.x + 20, rect.y + 14))

        obj = font_small.render(f"Objective: {self.objective_text}", True, COLOR_TEXT_SECONDARY)
        surface.blit(obj, (rect.x + 20, rect.y + 38))

        timer_txt = font_med.render(f"TIME: {self.time_remaining:.1f}s", True, COLOR_WARNING if self.time_remaining < 5.0 else COLOR_NOMINAL)
        surface.blit(timer_txt, (rect.right - timer_txt.get_width() - 20, rect.y + 14))

        bar_w = 580
        bar_h = 36
        bar_x = rect.x + (modal_w - bar_w) // 2
        bar_y = rect.y + 75

        # -------------------------------------------------------------
        # RAPID-TAP MODE: TURBO POWER CHARGE BAR
        # -------------------------------------------------------------
        if self.mode == "RAPID_TAP":
            pygame.draw.rect(surface, (20, 24, 34), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (255, 179, 0), (bar_x, bar_y, bar_w, bar_h), width=2)

            fill_w = int(self.tap_progress * bar_w)
            if fill_w > 0:
                fill_col = (0, 255, 120) if self.tap_progress > 0.8 else ((255, 200, 40) if self.tap_progress > 0.4 else (255, 80, 50))
                pygame.draw.rect(surface, fill_col, (bar_x + 2, bar_y + 2, fill_w - 4, bar_h - 4))

            pct_lbl = font_large.render(f"CHARGE: {int(self.tap_progress * 100)}%", True, (255, 255, 255))
            surface.blit(pct_lbl, (bar_x + (bar_w - pct_lbl.get_width()) // 2, bar_y + 9))

            info_y = bar_y + bar_h + 20
            info_txt = font_large.render(">>> MASH [SPACE] OR [E] TO CHARGE! <<<", True, (255, 220, 0))
            surface.blit(info_txt, (bar_x + (bar_w - info_txt.get_width()) // 2, info_y))

        # -------------------------------------------------------------
        # SWEET-SPOT MODE: OSCILLATING RESONANCE TRACK
        # -------------------------------------------------------------
        else:
            pygame.draw.rect(surface, (20, 24, 34), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (60, 75, 95), (bar_x, bar_y, bar_w, bar_h), width=2)

            # Sweet Spot
            low, high = self.target_zone
            zx = int(bar_x + low * bar_w)
            zw = int((high - low) * bar_w)
            pygame.draw.rect(surface, (40, 180, 90), (zx, bar_y + 2, zw, bar_h - 4))
            pygame.draw.rect(surface, (0, 255, 140), (zx, bar_y, zw, bar_h), width=2)

            sweet_lbl = font_small.render("SWEET SPOT", True, (0, 255, 140))
            surface.blit(sweet_lbl, (zx + max(4, (zw - sweet_lbl.get_width()) // 2), bar_y + 10))

            # Needle
            nx = int(bar_x + self.needle_pos * bar_w)
            pygame.draw.rect(surface, (255, 255, 255), (nx - 3, bar_y - 4, 6, bar_h + 8))

            info_y = bar_y + bar_h + 18
            lock_str = f"LOCKS: [{self.locks_achieved}/{self.locks_required}]"
            surface.blit(font_med.render(lock_str, True, COLOR_TEXT_PRIMARY), (bar_x, info_y))
            for idx in range(self.locks_required):
                dx = bar_x + 140 + idx * 26
                col = (0, 255, 120) if idx < self.locks_achieved else (50, 60, 75)
                pygame.draw.circle(surface, col, (dx, info_y + 6), 6)

        # Status text
        fb_surf = font_med.render(self.feedback_text, True, self.feedback_color)
        surface.blit(fb_surf, (bar_x, rect.bottom - 45))

        # Helper
        helper = font_small.render("[SPACE] or [E] — Action  |  [ESC] Abort", True, (130, 150, 175))
        surface.blit(helper, (rect.right - helper.get_width() - 20, rect.bottom - 24))
