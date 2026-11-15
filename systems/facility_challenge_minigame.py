"""MARS SURVIVAL — Interactive Facility Challenge Minigame System.

Provides 5 distinct, engaging 2D retro arcade minigames across all base facilities
and grid challenge stations:
1. "CIRCUIT_SEQUENCE": Directional arrow QTE wiring sequence ([↑][→][↓][←])
2. "PRESSURE_VALVE": Chamber pressure balance & stability regulation
3. "FREQUENCY_TUNE": Dual-oscilloscope radio harmonic wave matching ([A]/[D] to tune)
4. "TARGET_STRIKE": Radar scanning reticle crosshair mineral/pathogen lock
5. "RAPID_TAP": High-speed button mashing turbo charge frenzy
6. "SWEET_SPOT": Fast precision resonance needle lock

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
import random
from typing import Optional, Tuple, Dict, Any, Callable, List
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
    """Manages diverse 2D arcade interactive challenge minigames."""

    def __init__(self) -> None:
        self.is_active: bool = False
        self.facility_id: str = ""
        self.facility_name: str = ""
        self.objective_text: str = ""
        self.reward_text: str = ""
        self.mode: str = "CIRCUIT_SEQUENCE"

        # General Timers & Juice
        self.time_remaining: float = 20.0
        self.feedback_text: str = ""
        self.feedback_color: Tuple[int, int, int] = COLOR_NOMINAL
        self.feedback_timer: float = 0.0
        self.shake_trauma: float = 0.0
        self.anim_clock: float = 0.0

        # Callback
        self.on_success: Optional[Callable[[], None]] = None

        # Mode 1: CIRCUIT_SEQUENCE
        self.sequence: List[str] = []
        self.sequence_index: int = 0

        # Mode 2: PRESSURE_VALVE
        self.pressure: float = 0.50
        self.pressure_target_min: float = 0.38
        self.pressure_target_max: float = 0.68
        self.stability_progress: float = 0.0

        # Mode 3: FREQUENCY_TUNE
        self.target_freq: float = 4.0
        self.player_freq: float = 1.5

        # Mode 4: TARGET_STRIKE
        self.strike_targets: List[Dict[str, Any]] = []
        self.reticle_x: float = 0.0
        self.reticle_dir: float = 1.0
        self.hits_achieved: int = 0
        self.hits_required: int = 3

        # Mode 5: RAPID_TAP
        self.tap_progress: float = 0.0
        self.tap_decay: float = 0.32

        # Mode 6: SWEET_SPOT
        self.needle_pos: float = 0.0
        self.needle_speed: float = 1.4
        self.needle_dir: float = 1.0
        self.target_zone: Tuple[float, float] = (0.42, 0.58)
        self.locks_required: int = 3
        self.locks_achieved: int = 0

    def start_challenge(
        self,
        facility_id: str,
        facility_name: str,
        objective: str,
        reward_desc: str,
        on_success_callback: Callable[[], None],
        mode: str = "CIRCUIT_SEQUENCE",
    ) -> None:
        """Launch interactive minigame with the designated challenge mode."""
        self.is_active = True
        self.facility_id = facility_id
        self.facility_name = facility_name
        self.objective_text = objective
        self.reward_text = reward_desc
        self.on_success = on_success_callback
        self.mode = mode
        self.shake_trauma = 0.0
        self.anim_clock = 0.0

        # Initialize specific mode state
        if self.mode == "CIRCUIT_SEQUENCE":
            self.time_remaining = 16.0
            dirs = ["UP", "DOWN", "LEFT", "RIGHT"]
            self.sequence = [random.choice(dirs) for _ in range(5)]
            self.sequence_index = 0
            self.feedback_text = "ENTER ARROW KEYS OR [WASD] IN SEQUENCE!"
            self.feedback_color = COLOR_TEXT_HIGHLIGHT

        elif self.mode == "PRESSURE_VALVE":
            self.time_remaining = 20.0
            self.pressure = 0.50
            self.pressure_target_min = random.uniform(0.35, 0.45)
            self.pressure_target_max = self.pressure_target_min + 0.28
            self.stability_progress = 0.0
            self.feedback_text = "PUMP VALVE WITH [SPACE] OR [E] TO KEEP GAUGE IN GREEN ZONE!"
            self.feedback_color = COLOR_TEXT_HIGHLIGHT

        elif self.mode == "FREQUENCY_TUNE":
            self.time_remaining = 20.0
            self.target_freq = random.uniform(2.5, 6.5)
            self.player_freq = random.choice([1.0, 7.5])
            self.feedback_text = "TUNE FREQUENCY WITH [A]/[D] OR ARROWS TO RESONATE, THEN PRESS [SPACE]!"
            self.feedback_color = COLOR_TEXT_HIGHLIGHT

        elif self.mode == "TARGET_STRIKE":
            self.time_remaining = 18.0
            self.hits_achieved = 0
            self.hits_required = 3
            self.reticle_x = 0.0
            self.reticle_dir = 1.0
            self.strike_targets = [
                {"x": random.uniform(0.15, 0.35), "speed": random.uniform(0.10, 0.20), "dir": 1.0, "hit": False},
                {"x": random.uniform(0.40, 0.60), "speed": random.uniform(-0.25, -0.12), "dir": -1.0, "hit": False},
                {"x": random.uniform(0.65, 0.85), "speed": random.uniform(0.15, 0.25), "dir": 1.0, "hit": False},
            ]
            self.feedback_text = "PRESS [SPACE] OR [E] WHEN CROSSHAIR OVERLAPS AN ORE TARGET!"
            self.feedback_color = COLOR_TEXT_HIGHLIGHT

        elif self.mode == "RAPID_TAP":
            self.time_remaining = 12.0
            self.tap_progress = 0.0
            self.tap_decay = 0.32
            self.feedback_text = "MASH [SPACE] OR [E] RAPIDLY TO CHARGE TO 100%!"
            self.feedback_color = COLOR_TEXT_HIGHLIGHT

        else:
            # Fallback SWEET_SPOT
            self.time_remaining = 18.0
            self.needle_pos = 0.0
            self.needle_dir = 1.0
            self.needle_speed = random.uniform(1.2, 1.6)
            spread = random.uniform(0.14, 0.20)
            center = random.uniform(0.35, 0.65)
            self.target_zone = (center - spread / 2.0, center + spread / 2.0)
            self.locks_required = 3
            self.locks_achieved = 0
            self.feedback_text = "PRESS [SPACE] OR [E] WHEN NEEDLE IS IN GREEN ZONE!"
            self.feedback_color = COLOR_TEXT_HIGHLIGHT

    def _trigger_win(self, audio: Any = None) -> None:
        """Handle challenge success."""
        self.feedback_text = f"CHALLENGE VICTORY! {self.reward_text}"
        self.feedback_color = COLOR_NOMINAL
        if audio:
            audio.play("success")
        if self.on_success:
            self.on_success()
        self.is_active = False

    def handle_key(self, key: int, audio: Any = None) -> bool:
        """Handle keyboard interactions for the active minigame."""
        if not self.is_active:
            return False

        if key == pygame.K_ESCAPE:
            self.is_active = False
            if audio:
                audio.play("beep")
            return True

        # ---------------------------------------------------------------------
        # 1. CIRCUIT_SEQUENCE (Arrow Keys / WASD Sequence)
        # ---------------------------------------------------------------------
        if self.mode == "CIRCUIT_SEQUENCE":
            expected = self.sequence[self.sequence_index]
            pressed = None

            if key in (pygame.K_UP, pygame.K_w):
                pressed = "UP"
            elif key in (pygame.K_DOWN, pygame.K_s):
                pressed = "DOWN"
            elif key in (pygame.K_LEFT, pygame.K_a):
                pressed = "LEFT"
            elif key in (pygame.K_RIGHT, pygame.K_d):
                pressed = "RIGHT"

            if pressed:
                if pressed == expected:
                    self.sequence_index += 1
                    if audio:
                        audio.play("beep")
                    if self.sequence_index >= len(self.sequence):
                        self._trigger_win(audio)
                    else:
                        self.feedback_text = f"STEP {self.sequence_index}/{len(self.sequence)} ALIGNED! NEXT: [{self.sequence[self.sequence_index]}]"
                        self.feedback_color = COLOR_NOMINAL
                else:
                    self.shake_trauma = 0.5
                    self.sequence_index = 0
                    self.feedback_text = "WRONG CIRCUIT WIRE! SEQUENCE RESET!"
                    self.feedback_color = COLOR_CRITICAL
                    if audio:
                        audio.play("fail")
                return True

        # ---------------------------------------------------------------------
        # 2. PRESSURE_VALVE (Space / E / W Valve Pump)
        # ---------------------------------------------------------------------
        elif self.mode == "PRESSURE_VALVE":
            if key in (pygame.K_SPACE, pygame.K_e, pygame.K_w, pygame.K_UP):
                self.pressure = min(1.0, self.pressure + 0.16)
                if audio:
                    audio.play("beep")
                return True

        # ---------------------------------------------------------------------
        # 3. FREQUENCY_TUNE (A/D to adjust frequency dial, Space/E to Lock)
        # ---------------------------------------------------------------------
        elif self.mode == "FREQUENCY_TUNE":
            if key in (pygame.K_LEFT, pygame.K_a):
                self.player_freq = max(1.0, self.player_freq - 0.35)
                if audio:
                    audio.play("beep")
                return True
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.player_freq = min(8.5, self.player_freq + 0.35)
                if audio:
                    audio.play("beep")
                return True
            elif key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
                diff = abs(self.player_freq - self.target_freq)
                if diff <= 0.45:
                    self._trigger_win(audio)
                else:
                    self.shake_trauma = 0.4
                    self.feedback_text = "SIGNAL MISALIGNED! TUNE WITH [A]/[D] OR ARROWS!"
                    self.feedback_color = COLOR_CRITICAL
                    if audio:
                        audio.play("fail")
                return True

        # ---------------------------------------------------------------------
        # 4. TARGET_STRIKE (Space / E when reticle overlaps target)
        # ---------------------------------------------------------------------
        elif self.mode == "TARGET_STRIKE":
            if key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
                hit_any = False
                for t in self.strike_targets:
                    if not t["hit"] and abs(self.reticle_x - t["x"]) <= 0.08:
                        t["hit"] = True
                        self.hits_achieved += 1
                        hit_any = True
                        if audio:
                            audio.play("pickup")
                        break

                if hit_any:
                    if self.hits_achieved >= self.hits_required:
                        self._trigger_win(audio)
                    else:
                        self.feedback_text = f"TARGET LOCKED! [{self.hits_achieved}/{self.hits_required}] SECURED!"
                        self.feedback_color = COLOR_NOMINAL
                else:
                    self.shake_trauma = 0.3
                    self.feedback_text = "RETICLE MISSED! TIME YOUR STRIKE!"
                    self.feedback_color = COLOR_WARNING
                    if audio:
                        audio.play("fail")
                return True

        # ---------------------------------------------------------------------
        # 5. RAPID_TAP (Button-mashing frenzy)
        # ---------------------------------------------------------------------
        elif self.mode == "RAPID_TAP":
            if key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
                self.tap_progress += 0.14
                if audio:
                    audio.play("beep")
                if self.tap_progress >= 1.0:
                    self.tap_progress = 1.0
                    self._trigger_win(audio)
                return True

        # ---------------------------------------------------------------------
        # 6. SWEET_SPOT (Needle Timing)
        # ---------------------------------------------------------------------
        elif self.mode == "SWEET_SPOT":
            if key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
                low, high = self.target_zone
                if low <= self.needle_pos <= high:
                    self.locks_achieved += 1
                    if audio:
                        audio.play("beep")
                    if self.locks_achieved >= self.locks_required:
                        self._trigger_win(audio)
                    else:
                        self.feedback_text = f"LOCK #{self.locks_achieved} SECURED! RE-ALIGNING..."
                        self.feedback_color = COLOR_NOMINAL
                        spread = random.uniform(0.12, 0.18)
                        center = random.uniform(0.25, 0.75)
                        self.target_zone = (center - spread / 2.0, center + spread / 2.0)
                else:
                    self.shake_trauma = 0.4
                    self.feedback_text = "CALIBRATION MISALIGNED! TRY AGAIN!"
                    self.feedback_color = COLOR_CRITICAL
                    if audio:
                        audio.play("fail")
                return True

        return False

    def update(self, dt: float) -> None:
        """Update physics, timers, and animations."""
        if not self.is_active:
            return

        self.anim_clock += dt
        self.time_remaining = max(0.0, self.time_remaining - dt)
        if self.time_remaining <= 0.0:
            self.is_active = False
            return

        if self.shake_trauma > 0:
            self.shake_trauma = max(0.0, self.shake_trauma - dt * 2.5)

        # Mode-specific updates
        if self.mode == "PRESSURE_VALVE":
            self.pressure = max(0.0, self.pressure - 0.24 * dt)
            if self.pressure_target_min <= self.pressure <= self.pressure_target_max:
                self.stability_progress += 0.42 * dt
                self.feedback_text = f"PRESSURE STABLE! STABILITY: {int(self.stability_progress * 100)}%"
                self.feedback_color = COLOR_NOMINAL
                if self.stability_progress >= 1.0:
                    self._trigger_win()
            else:
                self.stability_progress = max(0.0, self.stability_progress - 0.15 * dt)
                if self.pressure < self.pressure_target_min:
                    self.feedback_text = "UNDERPRESSURE! PUMP VALVE WITH [SPACE]!"
                    self.feedback_color = COLOR_WARNING
                else:
                    self.feedback_text = "OVERPRESSURE! ALLOW VALVE TO BLEED DOWN!"
                    self.feedback_color = COLOR_CRITICAL

        elif self.mode == "TARGET_STRIKE":
            self.reticle_x += self.reticle_dir * 0.95 * dt
            if self.reticle_x >= 1.0:
                self.reticle_x = 1.0
                self.reticle_dir = -1.0
            elif self.reticle_x <= 0.0:
                self.reticle_x = 0.0
                self.reticle_dir = 1.0

            for t in self.strike_targets:
                if not t["hit"]:
                    t["x"] += t["speed"] * dt
                    if t["x"] > 0.92:
                        t["x"] = 0.92
                        t["speed"] = -abs(t["speed"])
                    elif t["x"] < 0.08:
                        t["x"] = 0.08
                        t["speed"] = abs(t["speed"])

        elif self.mode == "RAPID_TAP":
            self.tap_progress = max(0.0, self.tap_progress - self.tap_decay * dt)

        elif self.mode == "SWEET_SPOT":
            self.needle_pos += self.needle_dir * self.needle_speed * dt
            if self.needle_pos >= 1.0:
                self.needle_pos = 1.0
                self.needle_dir = -1.0
            elif self.needle_pos <= 0.0:
                self.needle_pos = 0.0
                self.needle_dir = 1.0

    def render(self, surface: pygame.Surface) -> None:
        """Render distinct retro arcade minigame interface."""
        if not self.is_active:
            return

        modal_w = 680
        modal_h = 290
        shake_x = math.sin(pygame.time.get_ticks() * 0.05) * (self.shake_trauma * 12.0)
        shake_y = math.cos(pygame.time.get_ticks() * 0.07) * (self.shake_trauma * 12.0)

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
        font_giant = pygame.font.SysFont("Consolas", 24, bold=True)

        # Header
        hdr = font_large.render(f"CHALLENGE [{self.mode.replace('_', ' ')}] // {self.facility_name.upper()}", True, (255, 215, 0))
        surface.blit(hdr, (rect.x + 20, rect.y + 14))

        obj = font_small.render(f"Objective: {self.objective_text}", True, COLOR_TEXT_SECONDARY)
        surface.blit(obj, (rect.x + 20, rect.y + 36))

        timer_txt = font_med.render(f"TIME: {self.time_remaining:.1f}s", True, COLOR_WARNING if self.time_remaining < 5.0 else COLOR_NOMINAL)
        surface.blit(timer_txt, (rect.right - timer_txt.get_width() - 20, rect.y + 14))

        # Main Arena Area
        arena_x = rect.x + 20
        arena_y = rect.y + 64
        arena_w = modal_w - 40
        arena_h = 140

        # =====================================================================
        # 1. CIRCUIT_SEQUENCE RENDER (Glowing Neon Arrow Blocks)
        # =====================================================================
        if self.mode == "CIRCUIT_SEQUENCE":
            pygame.draw.rect(surface, (14, 18, 28), (arena_x, arena_y, arena_w, arena_h))
            pygame.draw.rect(surface, (40, 60, 85), (arena_x, arena_y, arena_w, arena_h), width=1)

            arrow_map = {"UP": "▲", "DOWN": "▼", "LEFT": "◄", "RIGHT": "►"}
            num_steps = len(self.sequence)
            box_size = 72
            spacing = 24
            total_w = num_steps * box_size + (num_steps - 1) * spacing
            start_x = arena_x + (arena_w - total_w) // 2
            box_y = arena_y + (arena_h - box_size) // 2

            for i, d in enumerate(self.sequence):
                bx = start_x + i * (box_size + spacing)
                is_done = (i < self.sequence_index)
                is_curr = (i == self.sequence_index)

                if is_done:
                    border_col = (0, 255, 120)
                    fill_col = (10, 45, 25)
                    text_col = (0, 255, 120)
                    symbol = "✓"
                elif is_curr:
                    pulse = abs(math.sin(self.anim_clock * 6.0))
                    border_col = (255, int(200 + pulse * 55), 0)
                    fill_col = (45, 38, 12)
                    text_col = (255, 230, 80)
                    symbol = arrow_map[d]
                else:
                    border_col = (50, 70, 95)
                    fill_col = (20, 26, 38)
                    text_col = (110, 130, 155)
                    symbol = arrow_map[d]

                pygame.draw.rect(surface, fill_col, (bx, box_y, box_size, box_size))
                pygame.draw.rect(surface, border_col, (bx, box_y, box_size, box_size), width=2 if not is_curr else 3)

                sym_surf = font_giant.render(symbol, True, text_col)
                surface.blit(sym_surf, (bx + (box_size - sym_surf.get_width()) // 2, box_y + (box_size - sym_surf.get_height()) // 2))

                lbl = font_small.render(f"WIRE #{i+1}", True, (130, 150, 170) if not is_curr else (255, 215, 0))
                surface.blit(lbl, (bx + (box_size - lbl.get_width()) // 2, box_y + box_size + 6))

        # =====================================================================
        # 2. PRESSURE_VALVE RENDER (Vertical Chamber & Balance Zone)
        # =====================================================================
        elif self.mode == "PRESSURE_VALVE":
            pygame.draw.rect(surface, (14, 18, 28), (arena_x, arena_y, arena_w, arena_h))
            pygame.draw.rect(surface, (40, 60, 85), (arena_x, arena_y, arena_w, arena_h), width=1)

            # Left: Horizontal Pressure Tank
            gauge_w = 420
            gauge_h = 36
            gx = arena_x + 30
            gy = arena_y + 35

            pygame.draw.rect(surface, (20, 25, 38), (gx, gy, gauge_w, gauge_h))
            pygame.draw.rect(surface, (70, 90, 115), (gx, gy, gauge_w, gauge_h), width=2)

            # Target green band
            zx = int(gx + self.pressure_target_min * gauge_w)
            zw = int((self.pressure_target_max - self.pressure_target_min) * gauge_w)
            pygame.draw.rect(surface, (30, 130, 70), (zx, gy + 2, zw, gauge_h - 4))
            pygame.draw.rect(surface, (0, 255, 140), (zx, gy, zw, gauge_h), width=2)

            # Pressure level fill
            pw = int(self.pressure * gauge_w)
            pygame.draw.rect(surface, (255, 255, 255), (gx + pw - 3, gy - 6, 6, gauge_h + 12))

            # Labels
            p_lbl = font_small.render(f"PRESSURE: {int(self.pressure * 100)}% (TARGET: {int(self.pressure_target_min*100)}%-{int(self.pressure_target_max*100)}%)", True, (240, 245, 250))
            surface.blit(p_lbl, (gx, gy - 20))

            # Right: Vertical Stability Battery
            bx = arena_x + 480
            by = arena_y + 15
            bw = 110
            bh = 95
            pygame.draw.rect(surface, (20, 25, 38), (bx, by, bw, bh))
            pygame.draw.rect(surface, (0, 229, 255), (bx, by, bw, bh), width=2)

            stab_h = int(self.stability_progress * (bh - 6))
            if stab_h > 0:
                pygame.draw.rect(surface, (0, 255, 140), (bx + 3, by + bh - 3 - stab_h, bw - 6, stab_h))

            st_title = font_small.render("STABILITY", True, (0, 229, 255))
            surface.blit(st_title, (bx + (bw - st_title.get_width()) // 2, by + 12))
            st_val = font_large.render(f"{int(self.stability_progress * 100)}%", True, (255, 255, 255))
            surface.blit(st_val, (bx + (bw - st_val.get_width()) // 2, by + 34))

        # =====================================================================
        # 3. FREQUENCY_TUNE RENDER (Oscilloscope Dual-Wave Display)
        # =====================================================================
        elif self.mode == "FREQUENCY_TUNE":
            pygame.draw.rect(surface, (10, 16, 22), (arena_x, arena_y, arena_w, arena_h))
            pygame.draw.rect(surface, (0, 229, 255), (arena_x, arena_y, arena_w, arena_h), width=1)

            # Oscilloscope grid
            for gx in range(arena_x + 40, arena_x + arena_w, 40):
                pygame.draw.line(surface, (20, 35, 45), (gx, arena_y), (gx, arena_y + arena_h), 1)
            for gy in range(arena_y + 20, arena_y + arena_h, 20):
                pygame.draw.line(surface, (20, 35, 45), (arena_x, gy), (arena_x + arena_w, gy), 1)

            # Center line
            cy = arena_y + arena_h // 2
            pygame.draw.line(surface, (35, 55, 75), (arena_x, cy), (arena_x + arena_w, cy), 1)

            # Wave points
            t = self.anim_clock * 3.5
            prev_t_pt = None
            prev_p_pt = None
            for x_rel in range(0, arena_w, 3):
                px = arena_x + x_rel
                norm_x = (x_rel / arena_w) * math.pi * 4.0

                # Target Amber wave
                ty = cy + int(math.sin(norm_x * (self.target_freq * 0.4) + t) * 32)
                if prev_t_pt:
                    pygame.draw.line(surface, (255, 175, 40), prev_t_pt, (px, ty), 2)
                prev_t_pt = (px, ty)

                # Player Cyan wave
                py_pt = cy + int(math.sin(norm_x * (self.player_freq * 0.4) + t) * 32)
                if prev_p_pt:
                    pygame.draw.line(surface, (0, 255, 220), prev_p_pt, (px, py_pt), 2)
                prev_p_pt = (px, py_pt)

            diff = abs(self.player_freq - self.target_freq)
            resonance = max(0.0, 1.0 - diff / 2.0)
            res_txt = font_large.render(f"RESONANCE: {int(resonance * 100)}%", True, (0, 255, 140) if resonance >= 0.85 else (255, 200, 50))
            surface.blit(res_txt, (arena_x + 16, arena_y + 10))

            dial_txt = font_small.render(f"CARRIER FREQ: {self.player_freq:.1f} GHz  [A]/[D] Adjust  |  [SPACE] Transmit", True, (180, 205, 230))
            surface.blit(dial_txt, (arena_x + 16, arena_y + arena_h - 22))

        # =====================================================================
        # 4. TARGET_STRIKE RENDER (Radar Scan Grid & Crosshair)
        # =====================================================================
        elif self.mode == "TARGET_STRIKE":
            pygame.draw.rect(surface, (10, 16, 24), (arena_x, arena_y, arena_w, arena_h))
            pygame.draw.rect(surface, (0, 229, 255), (arena_x, arena_y, arena_w, arena_h), width=1)

            # Sweep bar
            rx = int(arena_x + self.reticle_x * arena_w)
            pygame.draw.line(surface, (255, 215, 0), (rx, arena_y + 2), (rx, arena_y + arena_h - 2), 2)
            pygame.draw.circle(surface, (255, 215, 0), (rx, arena_y + arena_h // 2), 16, width=2)
            pygame.draw.line(surface, (255, 215, 0), (rx - 20, arena_y + arena_h // 2), (rx + 20, arena_y + arena_h // 2), 1)

            # Targets
            for idx, t in enumerate(self.strike_targets):
                tx = int(arena_x + t["x"] * arena_w)
                ty = arena_y + 35 + idx * 35
                if not t["hit"]:
                    pulse = math.sin(self.anim_clock * 8.0 + idx) * 3
                    r = int(10 + pulse)
                    pygame.draw.circle(surface, (255, 80, 60), (tx, ty), r)
                    pygame.draw.circle(surface, (255, 220, 100), (tx, ty), r, width=2)
                    lbl = font_small.render(f"NODE #{idx+1}", True, (255, 200, 180))
                    surface.blit(lbl, (tx - lbl.get_width() // 2, ty + 12))
                else:
                    pygame.draw.circle(surface, (0, 255, 140), (tx, ty), 6)
                    chk = font_small.render("LOCKED ✓", True, (0, 255, 140))
                    surface.blit(chk, (tx - chk.get_width() // 2, ty - 8))

            hits_lbl = font_med.render(f"TARGETS NEUTRALIZED: [{self.hits_achieved}/{self.hits_required}]", True, (0, 255, 180))
            surface.blit(hits_lbl, (arena_x + 16, arena_y + 10))

        # =====================================================================
        # 5. RAPID_TAP RENDER (Turbo Heat Gauge)
        # =====================================================================
        elif self.mode == "RAPID_TAP":
            pygame.draw.rect(surface, (14, 18, 28), (arena_x, arena_y, arena_w, arena_h))
            pygame.draw.rect(surface, (255, 179, 0), (arena_x, arena_y, arena_w, arena_h), width=1)

            bw = arena_w - 60
            bh = 40
            bx = arena_x + 30
            by = arena_y + 35

            pygame.draw.rect(surface, (24, 28, 40), (bx, by, bw, bh))
            pygame.draw.rect(surface, (255, 179, 0), (bx, by, bw, bh), width=2)

            fw = int(self.tap_progress * (bw - 4))
            if fw > 0:
                col = (0, 255, 120) if self.tap_progress > 0.8 else ((255, 200, 40) if self.tap_progress > 0.4 else (255, 80, 50))
                pygame.draw.rect(surface, col, (bx + 2, by + 2, fw, bh - 4))

            pct_txt = font_giant.render(f"CHARGE: {int(self.tap_progress * 100)}%", True, (255, 255, 255))
            surface.blit(pct_txt, (bx + (bw - pct_txt.get_width()) // 2, by + 6))

            prompt = font_large.render(">>> MASH [SPACE] OR [E] AT MAXIMUM SPEED! <<<", True, (255, 220, 0))
            surface.blit(prompt, (arena_x + (arena_w - prompt.get_width()) // 2, arena_y + 95))

        # =====================================================================
        # 6. SWEET_SPOT RENDER (Precision Needle)
        # =====================================================================
        else:
            pygame.draw.rect(surface, (14, 18, 28), (arena_x, arena_y, arena_w, arena_h))
            pygame.draw.rect(surface, (50, 70, 95), (arena_x, arena_y, arena_w, arena_h), width=1)

            bw = arena_w - 60
            bh = 38
            bx = arena_x + 30
            by = arena_y + 35

            pygame.draw.rect(surface, (20, 25, 38), (bx, by, bw, bh))
            pygame.draw.rect(surface, (70, 90, 115), (bx, by, bw, bh), width=2)

            low, high = self.target_zone
            zx = int(bx + low * bw)
            zw = int((high - low) * bw)
            pygame.draw.rect(surface, (40, 180, 90), (zx, by + 2, zw, bh - 4))
            pygame.draw.rect(surface, (0, 255, 140), (zx, by, zw, bh), width=2)

            nx = int(bx + self.needle_pos * bw)
            pygame.draw.rect(surface, (255, 255, 255), (nx - 3, by - 6, 6, bh + 12))

            l_str = f"PRECISION LOCKS: [{self.locks_achieved}/{self.locks_required}]"
            surface.blit(font_med.render(l_str, True, (0, 255, 200)), (bx, arena_y + 90))

        # Status & Feedback Bar
        fb_surf = font_med.render(self.feedback_text, True, self.feedback_color)
        surface.blit(fb_surf, (arena_x + 10, rect.bottom - 45))

        # Controls Hint
        ctrl_hint = {
            "CIRCUIT_SEQUENCE": "Arrow Keys / [WASD]  |  [ESC] Abort",
            "PRESSURE_VALVE": "[SPACE] Pump  |  [ESC] Abort",
            "FREQUENCY_TUNE": "[A]/[D] Tune  |  [SPACE] Transmit  |  [ESC] Abort",
            "TARGET_STRIKE": "[SPACE] Strike Reticle  |  [ESC] Abort",
            "RAPID_TAP": "Mash [SPACE] or [E]  |  [ESC] Abort",
            "SWEET_SPOT": "[SPACE] Lock  |  [ESC] Abort",
        }.get(self.mode, "[SPACE] Action  |  [ESC] Abort")

        helper = font_small.render(ctrl_hint, True, (130, 150, 175))
        surface.blit(helper, (rect.right - helper.get_width() - 20, rect.bottom - 24))
