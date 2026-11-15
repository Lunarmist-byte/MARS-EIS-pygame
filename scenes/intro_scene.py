"""DUSTFALL — Cinematic Video Intro & NASA Mariner 9 Interactive Scene.

Plays the opening cinematic video introduction before transitioning to the main game.
At 15.0 - 20.0 seconds of the video, renders the Mariner 9 spacecraft hologram
with an interactive hyperlink connection to the NASA mission archive:
https://science.nasa.gov/mission/mariner-9/

Controls:
- [SPACE] / [ESC]: Skip Intro to Game
- Click Mariner 9 Card / [ENTER] (at 15s-20s): Open NASA Mariner 9 Archive in Browser

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
import time
import webbrowser
from typing import Tuple, Optional
import pygame

try:
    import cv2
except ImportError:
    cv2 = None

from config import WINDOW_WIDTH, WINDOW_HEIGHT
from ui.font_manager import FontManager


class IntroScene:
    """Manages video decoding, audio synchronization, and Mariner 9 hyperlink overlay."""

    MARINER_URL = "https://science.nasa.gov/mission/mariner-9/"

    def __init__(
        self,
        video_path: str = "assets/intro/intro_video.mp4",
        audio_path: str = "assets/intro/intro_audio.wav",
        mariner_img_path: str = "assets/intro/mariner_9.png",
    ) -> None:
        self.video_path = video_path
        self.audio_path = audio_path
        self.mariner_img_path = mariner_img_path

        self.finished: bool = False
        self.elapsed_time: float = 0.0
        self.duration: float = 38.6
        self.fps: float = 30.0

        # Video state
        self.cap = None
        self.current_frame_surface: Optional[pygame.Surface] = None
        self.has_video: bool = False
        self.last_decoded_frame: int = -1
        self.start_time: float = time.perf_counter()

        # Mariner 9 interactive popup state (bottom-right, transparent with no additional background)
        self.mariner_img: Optional[pygame.Surface] = None
        card_w, card_h = 250, 195
        card_x = WINDOW_WIDTH - card_w - 20
        card_y = WINDOW_HEIGHT - card_h - 45
        self.card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        self.link_button_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        self.skip_button_rect = pygame.Rect(20, WINDOW_HEIGHT - 45, 135, 32)
        self.is_hovering_link: bool = False
        self.feedback_msg: str = ""
        self.feedback_timer: float = 0.0

        self._init_video_and_assets()

    def _init_video_and_assets(self) -> None:
        """Initialize video capture, audio playback, and load Mariner 9 graphic."""
        if cv2 and os.path.exists(self.video_path):
            try:
                self.cap = cv2.VideoCapture(self.video_path)
                if self.cap.isOpened():
                    self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
                    frame_count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1.0
                    self.duration = frame_count / self.fps
                    self.has_video = True
            except Exception:
                self.has_video = False

        if not self.has_video:
            # Fallback if video file is missing or OpenCV unreadable
            self.finished = True
            return

        # Start audio playback
        if os.path.exists(self.audio_path):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                pygame.mixer.music.load(self.audio_path)
                pygame.mixer.music.play()
            except Exception:
                pass

        # Load Mariner 9 probe image with preserved aspect ratio
        if os.path.exists(self.mariner_img_path):
            try:
                loaded = pygame.image.load(self.mariner_img_path)
                w, h = loaded.get_size()
                max_w, max_h = 240, 150
                scale = min(max_w / w, max_h / h)
                target_size = (int(w * scale), int(h * scale))
                self.mariner_img = pygame.transform.smoothscale(loaded, target_size)
            except Exception:
                self.mariner_img = None

    def open_mariner_link(self) -> None:
        """Launch NASA Mariner 9 mission archive in default browser."""
        try:
            webbrowser.open(self.MARINER_URL)
            self.feedback_msg = "Opened NASA Mariner 9 Archive in Browser!"
            self.feedback_timer = 3.0
        except Exception:
            self.feedback_msg = "Link: https://science.nasa.gov/mission/mariner-9/"
            self.feedback_timer = 4.0

    def update(self, dt: float) -> Tuple[bool, bool]:
        """Update video frames, handle user input, and check timeline.
        
        Returns:
            (running, finished):
            - running: False if user requested window close / quit.
            - finished: True when intro finishes or is skipped, ready for MainScene.
        """
        if self.finished:
            return True, True

        if self.feedback_timer > 0:
            self.feedback_timer -= dt

        mouse_pos = pygame.mouse.get_pos()
        is_mariner_window = 15.0 <= self.elapsed_time <= 20.0
        self.is_hovering_link = is_mariner_window and (self.card_rect.collidepoint(mouse_pos) or self.link_button_rect.collidepoint(mouse_pos))

        # Set hand cursor if hovering clickable link
        if self.is_hovering_link or self.skip_button_rect.collidepoint(mouse_pos):
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            except Exception:
                pass
        else:
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            except Exception:
                pass

        # Process input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.cleanup()
                return False, True

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                    # Skip intro immediately
                    self.cleanup()
                    return True, True
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if is_mariner_window:
                        self.open_mariner_link()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if is_mariner_window and (self.card_rect.collidepoint(event.pos) or self.link_button_rect.collidepoint(event.pos)):
                    self.open_mariner_link()
                elif self.skip_button_rect.collidepoint(event.pos):
                    self.cleanup()
                    return True, True

        # Advance timeline smoothly with audio clock synchronization
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            music_pos_ms = pygame.mixer.music.get_pos()
            if music_pos_ms >= 0:
                audio_sec = music_pos_ms / 1000.0
                # Drift protection: lock to audio clock if within reasonable threshold
                if abs(audio_sec - self.elapsed_time) < 0.25:
                    self.elapsed_time = audio_sec
                else:
                    self.elapsed_time += dt
            else:
                self.elapsed_time += dt
        else:
            self.elapsed_time += dt

        # End of video reached
        if self.elapsed_time >= self.duration:
            self.cleanup()
            return True, True

        # Synchronize video frame smoothly without keyframe seeking jitter
        if self.has_video and self.cap:
            target_frame = int(self.elapsed_time * self.fps)

            # Only seek if a massive timeline jump occurred (> 45 frames / 1.5 seconds)
            if target_frame < self.last_decoded_frame or (target_frame - self.last_decoded_frame) > 45:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, target_frame))
                self.last_decoded_frame = target_frame - 1

            # Advance frames sequentially to target_frame
            if target_frame > self.last_decoded_frame:
                while self.last_decoded_frame < target_frame:
                    ret, frame = self.cap.read()
                    if not ret:
                        self.cleanup()
                        return True, True
                    self.last_decoded_frame += 1

                    # Only resize and format the actual target frame to preserve 100% framerate
                    if self.last_decoded_frame == target_frame:
                        frame_resized = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT), interpolation=cv2.INTER_LINEAR)
                        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                        self.current_frame_surface = pygame.image.frombuffer(
                            frame_rgb.tobytes(), (WINDOW_WIDTH, WINDOW_HEIGHT), "RGB"
                        )

        return True, False

    def render(self, surface: pygame.Surface) -> None:
        """Render active video frame, NASA Mariner 9 card (at 15s-20s), and HUD elements."""
        # 1. Render active video frame or solid background
        if self.current_frame_surface:
            surface.blit(self.current_frame_surface, (0, 0))
        else:
            surface.fill((8, 10, 15))

        # 2. Render Mariner 9 Hyperlink Card strictly at 15.0s - 20.0s of the video
        if 15.0 <= self.elapsed_time <= 20.0:
            self._render_mariner_card(surface)

        # 3. Subtle bottom telemetry bar
        self._render_bottom_bar(surface)

    def _render_mariner_card(self, surface: pygame.Surface) -> None:
        """Render transparent NASA Mariner 9 popup at the bottom-right with NO background box."""
        font_link = FontManager.get(11, bold=True)
        font_url = FontManager.get(9)
        font_sub = FontManager.get(10, bold=True)

        r = self.card_rect

        # 1. Render transparent Mariner 9 Spacecraft Image directly (NO background whatsoever)
        if self.mariner_img:
            img_x = r.x + (r.width - self.mariner_img.get_width()) // 2
            img_y = r.y
            surface.blit(self.mariner_img, (img_x, img_y))

            # Subtle tactical corner tick marks only when hovered
            if self.is_hovering_link:
                glow_col = (255, 220, 0)
                c_len = 10
                for cx, cy in [(img_x, img_y), (img_x + self.mariner_img.get_width(), img_y),
                               (img_x, img_y + self.mariner_img.get_height()),
                               (img_x + self.mariner_img.get_width(), img_y + self.mariner_img.get_height())]:
                    sx = 1 if cx == img_x else -1
                    sy = 1 if cy == img_y else -1
                    pygame.draw.line(surface, glow_col, (cx, cy), (cx + sx * c_len, cy), 2)
                    pygame.draw.line(surface, glow_col, (cx, cy), (cx, cy + sy * c_len), 2)

        # 2. Hyperlink text floating directly below the probe with text shadow for crisp contrast
        text_y = r.y + (self.mariner_img.get_height() if self.mariner_img else 140) + 4
        link_col = (255, 220, 0) if self.is_hovering_link else (0, 240, 255)

        # Title / Action prompt
        link_text = "🔗 NASA MARINER 9 (1971) ↗"
        t_shadow = font_link.render(link_text, True, (0, 0, 0))
        t_surf = font_link.render(link_text, True, link_col)
        tx = r.x + (r.width - t_surf.get_width()) // 2
        surface.blit(t_shadow, (tx + 1, text_y + 1))
        surface.blit(t_surf, (tx, text_y))

        # URL text
        url_text = "science.nasa.gov/mission/mariner-9"
        u_shadow = font_url.render(url_text, True, (0, 0, 0))
        u_surf = font_url.render(url_text, True, (200, 230, 255) if self.is_hovering_link else (150, 190, 220))
        ux = r.x + (r.width - u_surf.get_width()) // 2
        surface.blit(u_shadow, (ux + 1, text_y + 16))
        surface.blit(u_surf, (ux, text_y + 15))

        # Feedback notification when clicked
        if self.feedback_msg and self.feedback_timer > 0:
            fb_shadow = font_sub.render(self.feedback_msg, True, (0, 0, 0))
            fb_surf = font_sub.render(self.feedback_msg, True, (0, 255, 180))
            fx = r.x + (r.width - fb_surf.get_width()) // 2
            surface.blit(fb_shadow, (fx + 1, text_y + 31))
            surface.blit(fb_surf, (fx, text_y + 30))

    def _render_bottom_bar(self, surface: pygame.Surface) -> None:
        """Render video progress bar and skip intro button."""
        font_hud = FontManager.get(10)

        # Video progress bar along the bottom
        bar_h = 4
        bar_w = WINDOW_WIDTH
        prog = min(1.0, max(0.0, self.elapsed_time / max(1.0, self.duration)))
        fill_w = int(bar_w * prog)
        pygame.draw.rect(surface, (25, 30, 40), (0, WINDOW_HEIGHT - bar_h, bar_w, bar_h))
        pygame.draw.rect(surface, (217, 83, 43), (0, WINDOW_HEIGHT - bar_h, fill_w, bar_h))

        # Bottom Left: NASA Mission Archive attribution
        left_text = f"NASA Jet Propulsion Laboratory // Mars Simulation Intro ({self.elapsed_time:.1f}s / {self.duration:.1f}s)"
        l_surf = font_hud.render(left_text, True, (120, 140, 160))
        surface.blit(l_surf, (15, WINDOW_HEIGHT - 32))

        # Bottom Right: Skip Intro Button
        pygame.draw.rect(surface, (20, 25, 35), self.skip_button_rect)
        pygame.draw.rect(surface, (70, 90, 120), self.skip_button_rect, width=1)
        skip_surf = font_hud.render("[SPACE] Skip Intro", True, (200, 215, 230))
        surface.blit(skip_surf, (self.skip_button_rect.x + 12, self.skip_button_rect.y + 8))

    def cleanup(self) -> None:
        """Release video capture, stop audio playback, and reset mouse cursor."""
        self.finished = True
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        except Exception:
            pass
