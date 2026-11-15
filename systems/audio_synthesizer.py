"""MARS SURVIVAL — Procedural Arcade Sound Synthesizer.

Generates real-time dynamic retro/arcade audio sound effects directly via Pygame
mixer (footsteps, low-g hops, terminal beeps, pickup chimes, success fanfares)
without relying on missing external audio asset files.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import math
import struct
from typing import Dict, Optional
import pygame


class SoundSynthesizer:
    """Procedurally synthesizes and caches crisp 8-bit / 16-bit arcade sound effects."""

    def __init__(self, sample_rate: int = 22050) -> None:
        self.sample_rate = sample_rate
        self.enabled = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
            self.enabled = True
            self._generate_all_sfx()
        except Exception:
            self.enabled = False

    def _generate_all_sfx(self) -> None:
        """Pre-bake all required arcade sound effects into memory."""
        self.sounds["hop"] = self._create_sweep_sound(120.0, 320.0, duration=0.18, wave_type="sine", volume=0.30)
        self.sounds["land"] = self._create_noise_puff(duration=0.08, volume=0.25)
        self.sounds["footstep"] = self._create_noise_puff(duration=0.04, volume=0.12)
        self.sounds["pickup"] = self._create_chime_sound([523.25, 659.25, 783.99, 1046.50], note_dur=0.06, volume=0.35)
        self.sounds["beep"] = self._create_tone(880.0, duration=0.08, wave_type="square", volume=0.20)
        self.sounds["success"] = self._create_chime_sound([440.0, 554.37, 659.25, 880.0], note_dur=0.12, volume=0.45)
        self.sounds["fail"] = self._create_sweep_sound(260.0, 110.0, duration=0.22, wave_type="sawtooth", volume=0.35)
        self.sounds["thruster"] = self._create_noise_puff(duration=0.15, volume=0.20)
        self.sounds["alarm"] = self._create_siren(duration=0.55, volume=0.35)

    def _create_siren(self, duration: float = 0.55, volume: float = 0.35) -> pygame.mixer.Sound:
        """Synthesize two-tone rising emergency klaxon siren."""
        num_samples = int(self.sample_rate * duration)
        samples = bytearray()
        for i in range(num_samples):
            t = float(i) / self.sample_rate
            # 4Hz frequency modulation between 520Hz and 880Hz
            freq = 680.0 + 180.0 * math.sin(2.0 * math.pi * 3.5 * t)
            val = 0.8 * (1.0 if math.sin(2.0 * math.pi * freq * t) >= 0 else -1.0)
            sample_int = int(val * volume * 32767.0)
            samples.extend(struct.pack("<hh", sample_int, sample_int))
        return pygame.mixer.Sound(buffer=bytes(samples))

    def _create_tone(self, freq: float, duration: float, wave_type: str = "sine", volume: float = 0.3) -> pygame.mixer.Sound:
        """Synthesize a single frequency tone."""
        num_samples = int(self.sample_rate * duration)
        samples = bytearray()

        for i in range(num_samples):
            t = float(i) / self.sample_rate
            decay = max(0.0, 1.0 - (float(i) / num_samples))
            
            if wave_type == "sine":
                val = math.sin(2.0 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0 else -1.0
            else:
                val = 2.0 * (t * freq - math.floor(0.5 + t * freq))

            sample_int = int(val * volume * decay * 32767.0)
            sample_bytes = struct.pack("<hh", sample_int, sample_int)
            samples.extend(sample_bytes)

        return pygame.mixer.Sound(buffer=bytes(samples))

    def _create_sweep_sound(self, start_f: float, end_f: float, duration: float, wave_type: str = "sine", volume: float = 0.3) -> pygame.mixer.Sound:
        """Synthesize a frequency pitch sweep (e.g. hop upward or zap)."""
        num_samples = int(self.sample_rate * duration)
        samples = bytearray()
        phase = 0.0

        for i in range(num_samples):
            frac = float(i) / num_samples
            current_f = start_f + (end_f - start_f) * frac
            decay = max(0.0, 1.0 - frac * 0.8)
            phase += 2.0 * math.pi * current_f / self.sample_rate

            if wave_type == "sine":
                val = math.sin(phase)
            elif wave_type == "sawtooth":
                val = 2.0 * ((phase / (2.0 * math.pi)) % 1.0) - 1.0
            else:
                val = 1.0 if math.sin(phase) >= 0 else -1.0

            sample_int = int(val * volume * decay * 32767.0)
            samples.extend(struct.pack("<hh", sample_int, sample_int))

        return pygame.mixer.Sound(buffer=bytes(samples))

    def _create_noise_puff(self, duration: float, volume: float = 0.2) -> pygame.mixer.Sound:
        """Synthesize a low-frequency noise puff for footfalls and regolith displacement."""
        import random
        num_samples = int(self.sample_rate * duration)
        samples = bytearray()
        last_val = 0.0

        for i in range(num_samples):
            frac = float(i) / num_samples
            decay = max(0.0, 1.0 - frac)
            # Low-pass filtered noise
            white = random.uniform(-1.0, 1.0)
            last_val = last_val * 0.85 + white * 0.15
            sample_int = int(last_val * volume * decay * 32767.0)
            samples.extend(struct.pack("<hh", sample_int, sample_int))

        return pygame.mixer.Sound(buffer=bytes(samples))

    def _create_chime_sound(self, notes: list[float], note_dur: float, volume: float = 0.3) -> pygame.mixer.Sound:
        """Synthesize an arpeggiated melodic chime sequence."""
        total_samples = int(self.sample_rate * note_dur * len(notes))
        samples = bytearray()

        for idx, freq in enumerate(notes):
            num_samples = int(self.sample_rate * note_dur)
            for i in range(num_samples):
                t = float(i) / self.sample_rate
                decay = max(0.0, 1.0 - (float(i) / num_samples) * 0.7)
                val = math.sin(2.0 * math.pi * freq * t) * 0.75 + math.sin(4.0 * math.pi * freq * t) * 0.25
                sample_int = int(val * volume * decay * 32767.0)
                samples.extend(struct.pack("<hh", sample_int, sample_int))

        return pygame.mixer.Sound(buffer=bytes(samples))

    def play(self, sound_name: str) -> None:
        """Play sound effect with zero latency."""
        if not self.enabled:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass
