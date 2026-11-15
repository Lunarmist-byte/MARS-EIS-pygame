"""MARS SURVIVAL — Environmental & Catastrophe Animator.

Authoritative visual and physics effects driven directly by MARS-EIS telemetry:
- Procedural camera screen-shake and structural trauma from marsquakes
- Dynamic diurnal Day/Night/Twilight cycle with NASA Martian blue sunset scattering
- Real-time wind-driven dust particle and storm particle system
- Catastrophe visual effects (dust storm blackout, radiation glitch, frost vignette, hull breach fog)
- Environmental audio coordinator (marsquakes, alarm sirens, wind howling, Geiger clicks)

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
import math
import random
from typing import Dict, Any, List, Optional, Tuple
import pygame

from config import WINDOW_WIDTH, WINDOW_HEIGHT
from world.world_state import WorldState


class DustParticle:
    """Represents a simulated grain of suspended Martian ferric oxide regolith."""

    __slots__ = ("x", "y", "size", "speed_mult", "alpha", "life", "max_life")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.size = random.uniform(1.0, 3.2)
        self.speed_mult = random.uniform(0.6, 1.4)
        self.alpha = random.randint(40, 160)
        self.life = random.uniform(0.0, 1.0)
        self.max_life = random.uniform(3.0, 7.0)


class EnvironmentAnimator:
    """Manages full-screen environmental simulation graphics and trauma animations."""

    def __init__(self) -> None:
        # 1. Camera screen-shake / trauma parameters
        self.trauma: float = 0.0  # [0.0, 1.0], shake = trauma^2
        self.trauma_decay: float = 0.75
        self.shake_offset_x: float = 0.0
        self.shake_offset_y: float = 0.0
        self.noise_time: float = 0.0

        # 2. Dust particle system
        self.max_particles = 180
        self.particles: List[DustParticle] = []
        for _ in range(self.max_particles):
            self.particles.append(
                DustParticle(
                    random.uniform(0, WINDOW_WIDTH),
                    random.uniform(0, WINDOW_HEIGHT),
                )
            )

        # 3. Dynamic day/night and atmospheric surfaces
        self.lighting_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.overlay_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.vignette_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self._precalculate_vignette()

        # 4. Catastrophe tracking & visual flash
        self.active_catastrophes: List[str] = []
        self.catastrophe_flash_alpha: float = 0.0
        self.glitch_timer: float = 0.0
        self.glitch_lines: List[Tuple[int, int, int, int]] = []
        self.total_time: float = 0.0

        # 5. Sound effects
        self.audio_cooldowns: Dict[str, float] = {}
        self.sounds: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self._load_sounds()

    def _precalculate_vignette(self) -> None:
        """Pre-bake smooth vignette gradient mask for screen borders."""
        self.vignette_surface.fill((0, 0, 0, 0))
        # Radial gradient from center outward
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2
        max_dist = math.hypot(cx, cy)
        for r in range(int(max_dist), 0, -20):
            norm = r / max_dist
            if norm > 0.6:
                alpha = int(((norm - 0.6) / 0.4) ** 2 * 140)
                pygame.draw.circle(self.vignette_surface, (0, 0, 0, alpha), (cx, cy), r, width=22)

    def _load_sounds(self) -> None:
        """Attempt to load catastrophe audio cues."""
        if not pygame.mixer.get_init():
            return
        files = {
            "marsquake": "assets/audio/marsquake.wav",
            "alarm": "assets/audio/alarm_siren.wav",
            "wind": "assets/audio/wind_howl.wav",
            "geiger": "assets/audio/geiger.wav",
        }
        for key, path in files.items():
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(0.35)
                    self.sounds[key] = snd
                except Exception:
                    self.sounds[key] = None
            else:
                self.sounds[key] = None

    def play_sound(self, sound_key: str, min_interval: float = 2.0) -> None:
        """Play catastrophe sound with interval cooldown."""
        snd = self.sounds.get(sound_key)
        if not snd:
            return
        last_t = self.audio_cooldowns.get(sound_key, 0.0)
        if self.total_time - last_t >= min_interval:
            try:
                snd.play()
                self.audio_cooldowns[sound_key] = self.total_time
            except Exception:
                pass

    def add_trauma(self, amount: float) -> None:
        """Inject camera trauma from marsquakes or concussive impacts."""
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt: float, world_state: WorldState) -> None:
        """Update particles, lighting, screen shake, and catastrophe states."""
        self.total_time += dt
        self.noise_time += dt * 32.0

        # 1. Update Camera Screen Shake
        if self.trauma > 0.0:
            self.trauma = max(0.0, self.trauma - self.trauma_decay * dt)
            shake = self.trauma * self.trauma
            max_shake_px = 16.0
            self.shake_offset_x = (
                math.sin(self.noise_time * 1.3) * max_shake_px * shake
                + math.sin(self.noise_time * 3.7) * (max_shake_px * 0.4) * shake
            )
            self.shake_offset_y = (
                math.cos(self.noise_time * 1.7) * max_shake_px * shake
                + math.cos(self.noise_time * 4.1) * (max_shake_px * 0.4) * shake
            )
        else:
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0

        # 2. Extract MARS-EIS Telemetry
        env = world_state.environment
        wind_speed = env.wind_speed_m_s if env.wind_speed_m_s is not None else 6.0
        wind_dir_deg = env.wind_direction_deg if env.wind_direction_deg is not None else 135.0
        tau = env.dust_opacity_tau if env.dust_opacity_tau is not None else 0.40

        # Calculate wind velocity components
        wind_rad = math.radians(wind_dir_deg)
        base_wind_px = (wind_speed / 5.0) * 110.0  # pixels per second
        vx = math.cos(wind_rad) * base_wind_px
        vy = math.sin(wind_rad) * base_wind_px

        # 3. Update Dust Particles
        active_count = min(self.max_particles, int(50 + tau * 80))
        for i in range(active_count):
            p = self.particles[i]
            p.x += vx * p.speed_mult * dt
            p.y += vy * p.speed_mult * dt
            p.life += dt
            # Screen wrap-around
            if p.x > WINDOW_WIDTH + 20:
                p.x = -20
                p.y = random.uniform(0, WINDOW_HEIGHT)
            elif p.x < -20:
                p.x = WINDOW_WIDTH + 20
                p.y = random.uniform(0, WINDOW_HEIGHT)

            if p.y > WINDOW_HEIGHT + 20:
                p.y = -20
                p.x = random.uniform(0, WINDOW_WIDTH)
            elif p.y < -20:
                p.y = WINDOW_HEIGHT + 20
                p.x = random.uniform(0, WINDOW_WIDTH)

        # 4. Check Active Catastrophes & Trigger Animations
        cats = world_state.catastrophes
        self.active_catastrophes = [
            c.get("type", c.get("catastrophe_type", "")) for c in cats if c.get("active", True)
        ]

        for cat in cats:
            if not cat.get("active", True):
                continue
            cat_type = cat.get("type", cat.get("catastrophe_type", ""))
            shake_amp = float(cat.get("screen_shake_intensity", 0.0))
            if shake_amp > 0:
                self.add_trauma(shake_amp * 0.15)

            # Trigger audio
            if "MARSQUAKE" in cat_type:
                self.play_sound("marsquake", min_interval=4.0)
            elif "HULL_BREACH" in cat_type:
                self.play_sound("alarm", min_interval=2.5)
            elif "DUST_STORM" in cat_type:
                self.play_sound("wind", min_interval=5.0)
            elif "RADIATION" in cat_type or "PARTICLE" in cat_type:
                self.play_sound("geiger", min_interval=1.2)

        # High wind audio cue
        if wind_speed > 16.0:
            self.play_sound("wind", min_interval=6.0)

        # 5. Glitch generator for Radiation Events
        if any("RADIATION" in c or "PARTICLE" in c for c in self.active_catastrophes):
            self.glitch_timer += dt
            if self.glitch_timer > 0.08:
                self.glitch_timer = 0.0
                self.glitch_lines = [
                    (
                        random.randint(0, WINDOW_WIDTH // 2),
                        random.randint(0, WINDOW_HEIGHT),
                        random.randint(40, 240),
                        random.randint(1, 4),
                    )
                    for _ in range(random.randint(2, 6))
                ]
        else:
            self.glitch_lines.clear()

    def render(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render atmospheric lighting, dust particles, and emergency overlays."""
        # 1. Day / Night & NASA Martian Twilight Lighting
        self._render_lighting(surface, world_state)

        # 2. Animated Wind & Dust Particles
        self._render_particles(surface, world_state)

        # 3. Catastrophe Overlays (Dust Blackout, Marsquake Alarms, Frost, Glitches)
        self._render_catastrophes(surface, world_state)

    def _render_lighting(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Simulate Mars Sol diurnal cycle & forward Mie scattering blue sunset."""
        gv = world_state.godot_visuals
        frac = world_state.fractional_sol
        # Map Sol time to zenith angle (Noon=0.5 sol -> zenith ~18deg, Night=0.0/1.0 -> zenith ~160deg)
        noon_offset = abs(frac - 0.5) * 2.0  # 0.0 at noon, 1.0 at midnight
        zenith_deg = 18.0 + noon_offset * 142.0

        env = world_state.environment
        tau = env.dust_opacity_tau if env.dust_opacity_tau is not None else 0.40

        self.lighting_surface.fill((0, 0, 0, 0))

        # Check if MARS-EIS live feed computed Mie scattering blue twilight directly
        is_blue_twilight = gv.get("is_blue_twilight", (78.0 <= zenith_deg <= 96.0))

        # Night condition (zenith > 96 deg)
        if zenith_deg > 96.0 and not is_blue_twilight:
            night_darkness = min(180, int((zenith_deg - 96.0) / 40.0 * 180))
            # Cold deep space navy/black tint
            self.lighting_surface.fill((10, 14, 25, night_darkness))

        # Martian Blue Twilight (zenith between 78 and 96 deg or live feed flagged)
        elif is_blue_twilight:
            blend = 1.0 - abs(zenith_deg - 87.0) / 9.0 if 78.0 <= zenith_deg <= 96.0 else 0.8
            twilight_alpha = int(blend * 110)
            # NASA forward scattering Martian blue twilight: (45, 90, 160)
            self.lighting_surface.fill((45, 90, 160, twilight_alpha))

        # Day condition: Atmospheric dust tint scaled by tau & live feed fog density
        else:
            fog_d = gv.get("fog_density")
            if fog_d is not None:
                dust_tint = min(160, int(fog_d * 1200))
            else:
                dust_tint = min(140, int(tau * 45))

            if dust_tint > 15:
                # Ferric oxide atmospheric ochre tint: (160, 95, 45)
                self.lighting_surface.fill((160, 95, 45, dust_tint))

        surface.blit(self.lighting_surface, (0, 0))

    def _render_particles(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render floating regolith dust grains and high-wind dust streaks."""
        gv = world_state.godot_visuals
        env = world_state.environment
        tau = env.dust_opacity_tau if env.dust_opacity_tau is not None else 0.40
        particle_scale = gv.get("wind_particle_scale", 1.0)
        active_count = min(self.max_particles, int((50 + tau * 80) * min(2.0, max(0.5, particle_scale))))
        wind_speed = env.wind_speed_m_s if env.wind_speed_m_s is not None else 6.0

        dust_color = (210, 135, 80)
        is_storm = tau > 1.2 or wind_speed > 18.0 or particle_scale > 2.5

        for i in range(min(active_count, len(self.particles))):
            p = self.particles[i]
            alpha = min(220, int(p.alpha * (0.8 + tau * 0.4)))
            col = (*dust_color, alpha)

            if is_storm:
                # Elongated wind streak
                streak_len = int(p.size * (3.0 + wind_speed * 0.4) * min(2.0, particle_scale))
                pygame.draw.line(surface, col, (int(p.x), int(p.y)), (int(p.x + streak_len), int(p.y + streak_len * 0.3)), width=max(1, int(p.size)))
            else:
                # Fine atmospheric dust grain
                pygame.draw.circle(surface, col, (int(p.x), int(p.y)), int(p.size))

    def _render_catastrophes(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render full-screen emergency visual effects for active catastrophes."""
        cats = self.active_catastrophes
        if not cats and not world_state.active_events:
            return

        self.overlay_surface.fill((0, 0, 0, 0))

        # 1. Global Dust Storm Blackout
        if any("DUST_STORM" in c for c in cats):
            pulse = 0.8 + 0.2 * math.sin(self.total_time * 2.0)
            storm_alpha = int(140 * pulse)
            self.overlay_surface.fill((140, 65, 25, storm_alpha))

        # 2. Severe Marsquake Structural Warning & Alert Strobe
        if any("MARSQUAKE" in c for c in cats):
            flash = 0.5 + 0.5 * math.sin(self.total_time * 12.0)
            red_alpha = int(flash * 85)
            # Red emergency border vignette
            pygame.draw.rect(self.overlay_surface, (230, 25, 25, red_alpha), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), width=18)

        # 3. Solar Particle Radiation Glitch Noise
        if any("RADIATION" in c or "PARTICLE" in c for c in cats):
            # Emerald/amber radiation haze
            pulse = 0.5 + 0.5 * math.sin(self.total_time * 4.0)
            self.overlay_surface.fill((25, 120, 45, int(45 * pulse)))
            # Glitch lines
            for gx, gy, gw, gh in self.glitch_lines:
                pygame.draw.rect(self.overlay_surface, (180, 255, 180, 180), (gx, gy, gw, gh))

        # 4. Cryogenic Flash Freeze Frost Vignette
        if any("FREEZE" in c for c in cats) or (world_state.environment.surface_temperature_c and world_state.environment.surface_temperature_c < -100.0):
            # Cyan/white frost border
            frost_col = (180, 225, 255, 90)
            pygame.draw.rect(self.overlay_surface, frost_col, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), width=16)

        # 5. Habitat Hull Breach Rapid Decompression
        if any("HULL_BREACH" in c for c in cats):
            strobe = 0.5 + 0.5 * math.sin(self.total_time * 14.0)
            breach_alpha = int(strobe * 105)
            # Flashing critical red strobe border
            pygame.draw.rect(self.overlay_surface, (255, 20, 20, breach_alpha), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), width=24)

        surface.blit(self.overlay_surface, (0, 0))

