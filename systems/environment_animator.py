"""MARS SURVIVAL — Environmental & Catastrophe Animator.

Authoritative visual and physics effects driven directly by MARS-EIS telemetry:
- Procedural camera screen-shake and structural trauma from marsquakes
- Dynamic diurnal Day/Night/Twilight cycle with NASA Martian blue sunset scattering
- Original Martian ferric oxide dust particle system (micro-aerosols, regolith grains, and catastrophe storm streaks)
- Catastrophe atmospheric visual effects (dust storm blackout, radiation glitch, frost vignette, hull breach strobe)
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
    """Represents a simulated grain of suspended Martian ferric oxide regolith.
    
    Tiers:
      0: Background micro-aerosol (slow drift, distant atmospheric suspension)
      1: Midground ferric regolith grain (varying terracotta/basalt hues, organic eddy curl)
      2: Catastrophe storm streak & vortex grain (high-speed wind streaks, whipped by gale gusts)
    """

    __slots__ = (
        "x", "y", "size", "speed_mult", "base_alpha", "life", "max_life",
        "tier", "color", "eddy_phase", "eddy_freq", "eddy_amp"
    )

    def __init__(self, x: float, y: float, tier: int = 1) -> None:
        self.x = x
        self.y = y
        self.tier = tier

        if tier == 0:
            # Fine background aerosol
            self.size = random.uniform(0.9, 1.8)
            self.speed_mult = random.uniform(0.35, 0.70)
            self.base_alpha = random.randint(35, 75)
            self.color = random.choice([
                (195, 110, 60),
                (180, 95, 45),
                (210, 130, 75),
            ])
        elif tier == 1:
            # Medium ferric regolith grain
            self.size = random.uniform(1.8, 3.2)
            self.speed_mult = random.uniform(0.85, 1.35)
            self.base_alpha = random.randint(70, 160)
            self.color = random.choice([
                (225, 125, 65),   # Martian Terracotta
                (205, 100, 50),   # Ferric Red Oxide
                (235, 160, 85),   # Desert Gold
                (175, 80, 40),    # Basalt Ochre
            ])
        else:
            # Violent catastrophe storm streak
            self.size = random.uniform(2.4, 4.2)
            self.speed_mult = random.uniform(1.6, 2.5)
            self.base_alpha = random.randint(130, 220)
            self.color = random.choice([
                (245, 175, 95),   # Specular Silt Grain
                (230, 130, 70),   # High-wind Ferric Streak
                (255, 195, 120),  # Solar-backlit Amber
            ])

        self.life = random.uniform(0.0, 5.0)
        self.max_life = random.uniform(4.0, 9.0)
        self.eddy_phase = random.uniform(0.0, 6.28)
        self.eddy_freq = random.uniform(1.2, 3.0)
        self.eddy_amp = random.uniform(8.0, 24.0)


class EnvironmentAnimator:
    """Manages full-screen environmental simulation graphics, trauma animations, and dust particles."""

    def __init__(self) -> None:
        # 1. Camera screen-shake / trauma parameters
        self.trauma: float = 0.0  # [0.0, 1.0], shake = trauma^2
        self.trauma_decay: float = 0.75
        self.shake_offset_x: float = 0.0
        self.shake_offset_y: float = 0.0
        self.noise_time: float = 0.0

        # 2. Authentic Martian Dust Particle System (Tier 0, 1, and 2)
        self.particles: List[DustParticle] = []
        # Pre-allocate particles: 120 micro + 140 midground + 90 catastrophe streaks
        for _ in range(120):
            self.particles.append(DustParticle(random.uniform(0, WINDOW_WIDTH), random.uniform(0, WINDOW_HEIGHT), tier=0))
        for _ in range(140):
            self.particles.append(DustParticle(random.uniform(0, WINDOW_WIDTH), random.uniform(0, WINDOW_HEIGHT), tier=1))
        for _ in range(90):
            self.particles.append(DustParticle(random.uniform(0, WINDOW_WIDTH), random.uniform(0, WINDOW_HEIGHT), tier=2))
        self.max_particles = len(self.particles)

        # 3. Dedicated transparent surfaces for True Alpha Blending
        self.particle_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.lighting_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.overlay_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.vignette_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self._precalculate_vignette()

        # 4. Catastrophe tracking & visual state
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

        # Check Active Catastrophes
        cats = world_state.catastrophes
        self.active_catastrophes = [
            c.get("type", c.get("catastrophe_type", "")) for c in cats if c.get("active", True)
        ]
        is_dust_storm_catastrophe = any("DUST" in c or "STORM" in c for c in self.active_catastrophes) or (tau >= 1.0)
        is_any_catastrophe = len(self.active_catastrophes) > 0

        # Calculate wind velocity components
        wind_rad = math.radians(wind_dir_deg)
        base_wind_px = (wind_speed / 5.0) * 110.0  # pixels per second

        # In a dust storm catastrophe, wind velocity surges with turbulent gusts
        if is_dust_storm_catastrophe:
            storm_boost = 1.8 + min(1.6, tau * 0.6)
            base_wind_px *= storm_boost

        vx = math.cos(wind_rad) * base_wind_px
        vy = math.sin(wind_rad) * base_wind_px

        # 3. Update Dust Particles with Sinusoidal Eddy Swirls
        # Scale active particles: ambient calm has ~35-50 subtle grains, catastrophes unleash up to 350 particles!
        if is_dust_storm_catastrophe:
            active_count = min(self.max_particles, int(180 + tau * 75))
        elif is_any_catastrophe:
            active_count = 140
        else:
            # Ambient condition: subtle, elegant suspension
            active_count = min(70, int(30 + tau * 45))

        for i in range(active_count):
            p = self.particles[i]

            # Organic eddy perturbation
            eddy_x = math.sin(p.life * p.eddy_freq + p.eddy_phase) * p.eddy_amp
            eddy_y = math.cos(p.life * p.eddy_freq * 0.8 + p.eddy_phase) * (p.eddy_amp * 0.6)

            p.x += (vx * p.speed_mult + eddy_x) * dt
            p.y += (vy * p.speed_mult + eddy_y) * dt
            p.life += dt

            # Wrap-around boundaries (with margin for streaks)
            margin = 50
            if p.x > WINDOW_WIDTH + margin:
                p.x = -margin
                p.y = random.uniform(0, WINDOW_HEIGHT)
            elif p.x < -margin:
                p.x = WINDOW_WIDTH + margin
                p.y = random.uniform(0, WINDOW_HEIGHT)

            if p.y > WINDOW_HEIGHT + margin:
                p.y = -margin
                p.x = random.uniform(0, WINDOW_WIDTH)
            elif p.y < -margin:
                p.y = WINDOW_HEIGHT + margin
                p.x = random.uniform(0, WINDOW_WIDTH)

            # Re-seed life cycle when expired
            if p.life >= p.max_life:
                p.life = 0.0

        # 4. Trigger Catastrophe-specific effects & audio
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
        """Render atmospheric diurnal lighting, authentic catastrophe dust particles, and emergency overlays."""
        # 1. Day / Night & NASA Martian Twilight Lighting
        self._render_lighting(surface, world_state)

        # 2. Original Martian Dust Particles (Micro-dust, Regolith Grains & Storm Streaks)
        self._render_particles(surface, world_state)

        # 3. Active Catastrophe Overlays
        self._render_catastrophes(surface, world_state)

    def _render_lighting(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Simulate Mars Sol diurnal cycle & forward Mie scattering blue sunset."""
        gv = world_state.godot_visuals
        frac = world_state.fractional_sol
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
            self.lighting_surface.fill((10, 14, 25, night_darkness))

        # Martian Blue Twilight (zenith between 78 and 96 deg or live feed flagged)
        elif is_blue_twilight:
            blend = 1.0 - abs(zenith_deg - 87.0) / 9.0 if 78.0 <= zenith_deg <= 96.0 else 0.8
            twilight_alpha = int(blend * 110)
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
        """Render multi-tier original Martian dust particles with true alpha blending."""
        env = world_state.environment
        tau = env.dust_opacity_tau if env.dust_opacity_tau is not None else 0.40
        wind_speed = env.wind_speed_m_s if env.wind_speed_m_s is not None else 6.0
        wind_dir_deg = env.wind_direction_deg if env.wind_direction_deg is not None else 135.0

        cats = self.active_catastrophes
        is_dust_storm = any("DUST" in c or "STORM" in c for c in cats) or (tau >= 1.0)
        is_catastrophe = len(cats) > 0 or is_dust_storm

        # Active particle slice
        if is_dust_storm:
            active_count = min(self.max_particles, int(180 + tau * 75))
        elif is_catastrophe:
            active_count = 140
        else:
            active_count = min(70, int(30 + tau * 45))

        # Clear transparent particle canvas
        self.particle_surface.fill((0, 0, 0, 0))

        # Unit vector along wind direction for elongated streaks
        wind_rad = math.radians(wind_dir_deg)
        dir_x = math.cos(wind_rad)
        dir_y = math.sin(wind_rad)

        # 1. Catastrophe Atmospheric Dust Haze Veil
        if is_dust_storm:
            pulse = 0.85 + 0.15 * math.sin(self.total_time * 2.5)
            haze_alpha = min(160, int((70 + tau * 35) * pulse))
            self.particle_surface.fill((165, 80, 35, haze_alpha))

        # 2. Render Individual Particles
        for i in range(min(active_count, len(self.particles))):
            p = self.particles[i]

            # Smooth sinusoidal fade in / fade out life factor
            life_norm = min(1.0, max(0.0, p.life / p.max_life))
            fade = math.sin(math.pi * life_norm)

            if is_dust_storm:
                alpha = min(240, int(p.base_alpha * fade * (1.1 + tau * 0.3)))
            else:
                alpha = min(200, int(p.base_alpha * fade * 0.85))

            if alpha <= 4:
                continue

            # Tier 2: Catastrophe High-Wind Streaks
            if p.tier == 2 and (is_catastrophe or wind_speed > 12.0 or tau > 0.8):
                streak_len = int(p.size * (4.0 + wind_speed * 0.45))
                end_x = int(p.x + dir_x * streak_len)
                end_y = int(p.y + dir_y * streak_len)
                col = (*p.color, alpha)

                # Wind streak line
                pygame.draw.line(
                    self.particle_surface,
                    col,
                    (int(p.x), int(p.y)),
                    (end_x, end_y),
                    width=max(1, int(p.size * 0.75))
                )
                # Specular head grain
                head_col = (min(255, p.color[0] + 25), min(255, p.color[1] + 25), min(255, p.color[2] + 20), min(255, alpha + 30))
                pygame.draw.circle(self.particle_surface, head_col, (end_x, end_y), max(1, int(p.size * 0.5)))

            # Tier 1: Midground Ferric Regolith Grains with Soft Halo
            elif p.tier == 1:
                # Soft outer glow
                glow_col = (*p.color, max(5, alpha // 4))
                pygame.draw.circle(self.particle_surface, glow_col, (int(p.x), int(p.y)), int(p.size * 1.8))
                # Dense solid grain core
                core_col = (*p.color, alpha)
                pygame.draw.circle(self.particle_surface, core_col, (int(p.x), int(p.y)), int(p.size))

            # Tier 0: Background Micro-Aerosols
            else:
                col = (*p.color, alpha)
                pygame.draw.circle(self.particle_surface, col, (int(p.x), int(p.y)), int(p.size))

        # Blit smoothly with true alpha blending over scene
        surface.blit(self.particle_surface, (0, 0))

    def _render_catastrophes(self, surface: pygame.Surface, world_state: WorldState) -> None:
        """Render subtle emergency visual effects for active catastrophes."""
        cats = self.active_catastrophes
        if not cats and not world_state.active_events:
            return

        self.overlay_surface.fill((0, 0, 0, 0))

        # 1. Severe Marsquake Structural Alert Strobe
        if any("MARSQUAKE" in c for c in cats):
            flash = 0.5 + 0.5 * math.sin(self.total_time * 12.0)
            red_alpha = int(flash * 85)
            pygame.draw.rect(self.overlay_surface, (230, 25, 25, red_alpha), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), width=18)

        # 2. Solar Particle Radiation Glitch Lines
        if any("RADIATION" in c or "PARTICLE" in c for c in cats):
            pulse = 0.5 + 0.5 * math.sin(self.total_time * 4.0)
            self.overlay_surface.fill((25, 120, 45, int(40 * pulse)))
            for gx, gy, gw, gh in self.glitch_lines:
                pygame.draw.rect(self.overlay_surface, (180, 255, 180, 180), (gx, gy, gw, gh))

        # 3. Cryogenic Flash Freeze Frost Vignette
        if any("FREEZE" in c for c in cats) or (world_state.environment.surface_temperature_c and world_state.environment.surface_temperature_c < -100.0):
            frost_col = (180, 225, 255, 80)
            pygame.draw.rect(self.overlay_surface, frost_col, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), width=16)

        # 4. Habitat Hull Breach Decompression Flashing Border
        if any("HULL_BREACH" in c for c in cats):
            strobe = 0.5 + 0.5 * math.sin(self.total_time * 14.0)
            breach_alpha = int(strobe * 95)
            pygame.draw.rect(self.overlay_surface, (255, 20, 20, breach_alpha), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), width=22)

        surface.blit(self.overlay_surface, (0, 0))
