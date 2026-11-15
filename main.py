"""DUSTFALL — Pygame Simulation Game Client.
Connected to MARS-EIS (Mars Environmental Intelligence & Simulation Engine).

Entry point for initializing the Pygame display, starting the background
simulation synchronizer, managing the 60 FPS delta-time game loop, and cleanly
releasing resources upon exit.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import argparse
import logging
import sys
import os
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    TARGET_FPS,
    BACKEND_CONFIG,
    CREDIT_INFO,
)
from backend.backend_config import BackendConfig
from backend.simulation_sync import SimulationSync
from scenes.main_scene import MainScene

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Dustfall")


def parse_arguments() -> argparse.Namespace:
    """Parse command line configuration flags."""
    parser = argparse.ArgumentParser(
        description="DUSTFALL — Pygame Simulation Client for MARS-EIS",
        epilog=f"{CREDIT_INFO['text']} | {CREDIT_INFO['github']}"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default=BACKEND_CONFIG["base_url"],
        help=f"MARS-EIS backend base URL (default: {BACKEND_CONFIG['base_url']})"
    )
    parser.add_argument(
        "--sync-interval",
        type=float,
        default=BACKEND_CONFIG["sync_interval_seconds"],
        help=f"World state polling interval in seconds (default: {BACKEND_CONFIG['sync_interval_seconds']})"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=TARGET_FPS,
        help=f"Maximum render frame rate (default: {TARGET_FPS})"
    )
    parser.add_argument(
        "--no-auto-advance",
        action="store_true",
        help="Disable automatic backend simulation time stepping"
    )
    parser.add_argument(
        "--with-backend", "-b",
        action="store_true",
        help="Explicitly launch MARS-EIS backend on port 8000"
    )
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Run client in standalone offline mode without auto-starting backend"
    )
    parser.add_argument(
        "--skip-intro",
        action="store_true",
        help="Skip opening cinematic video intro"
    )
    return parser.parse_args()


def print_banner() -> None:
    """Print terminal startup banner."""
    print("================================================================")
    print("   DUSTFALL — SIMULATION CLIENT (PYGAME 2.x)")
    print("   Integration with MARS-EIS Environmental Backend")
    print("================================================================")


def main() -> int:
    """Initialize systems, run main game loop, and cleanly terminate."""
    args = parse_arguments()
    print_banner()

    # Auto-detect and connect to MARS-EIS simulation backend
    from launch import is_port_in_use, start_mars_eis_server
    if not is_port_in_use(8000, "127.0.0.1"):
        if not args.no_backend:
            logger.info("MARS-EIS backend not detected on port 8000. Auto-starting local engine...")
            start_mars_eis_server(port=8000)
            import time
            for _ in range(25):
                time.sleep(0.2)
                if is_port_in_use(8000, "127.0.0.1"):
                    logger.info("MARS-EIS backend online and responding on http://127.0.0.1:8000!")
                    break
        else:
            logger.info("Standalone offline mode enabled (--no-backend).")
    else:
        logger.info("Detected running MARS-EIS simulation backend on port 8000.")

    # 1. Initialize Pygame core subsystems
    pygame.init()
    pygame.font.init()

    # Set window title, icon, and display surface
    pygame.display.set_caption(WINDOW_TITLE)
    icon_path = "assets/characters/avatar_1.png"
    if os.path.exists(icon_path):
        try:
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception:
            pass
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.DOUBLEBUF)

    clock = pygame.time.Clock()

    # 2. Configure and launch backend synchronization worker
    sync_config = BackendConfig(
        base_url=args.backend_url,
        sync_interval_seconds=args.sync_interval,
        automatic_advance=not args.no_auto_advance,
    )
    sync = SimulationSync(sync_config)
    sync.start()

    # 3. Check and instantiate intro scene or main scene
    intro_scene = None
    if not args.skip_intro and os.path.exists("assets/intro/intro_video.mp4"):
        try:
            from scenes.intro_scene import IntroScene
            intro_scene = IntroScene()
            logger.info("Opening cinematic video intro initialized.")
        except Exception as exc:
            logger.warning("Could not load intro video scene: %s. Starting main simulation directly.", exc)
            intro_scene = None

    main_scene = MainScene(sync)
    current_scene = intro_scene if (intro_scene and not intro_scene.finished) else main_scene
    logger.info("DUSTFALL client initialized. Entering main loop at %d FPS.", args.fps)

    # 4. Main Pygame delta-time loop
    running = True
    try:
        while running:
            # Calculate delta time in seconds, clamped to avoid spiral of death on lag spikes
            raw_dt_ms = clock.tick(args.fps)
            dt = min(raw_dt_ms / 1000.0, 0.05)

            if current_scene is intro_scene:
                running, intro_finished = intro_scene.update(dt)
                intro_scene.render(screen)
                if intro_finished:
                    intro_scene.cleanup()
                    current_scene = main_scene
            else:
                running = main_scene.update(dt)
                main_scene.render(screen)

            # Flip double buffer
            pygame.display.flip()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    except Exception as exc:
        logger.exception("Unexpected exception in main loop: %s", exc)
        return 1
    finally:
        # Clean shutdown: stop background thread and release Pygame resources
        logger.info("Shutting down DUSTFALL client...")
        if intro_scene:
            intro_scene.cleanup()
        sync.stop()
        pygame.quit()
        logger.info("All resources released. Goodbye.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
