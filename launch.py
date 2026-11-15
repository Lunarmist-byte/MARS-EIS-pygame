"""MARS SURVIVAL — Integrated Game & Simulation Launcher.

One-click launcher that starts the MARS-EIS environmental simulation engine
on http://127.0.0.1:8000 in a dedicated background worker and immediately
launches the Pygame survival client connected to it.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import os
import sys
import time
import socket
import threading
import logging

# Ensure ssosalien package path is discoverable
ssosalien_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ssosalien"))
if os.path.exists(ssosalien_dir) and ssosalien_dir not in sys.path:
    sys.path.insert(0, ssosalien_dir)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [Launcher]: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Launcher")


def is_port_in_use(port: int = 8000, host: str = "127.0.0.1") -> bool:
    """Check if target port is already open and accepting connections."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.4)
    try:
        res = s.connect_ex((host, port))
        return res == 0
    except Exception:
        return False
    finally:
        s.close()


def start_mars_eis_server(port: int = 8000) -> threading.Thread:
    """Start MARS-EIS FastAPI server in a background daemon thread."""
    from mars_eis.api.app import create_app
    from mars_eis.storage.database import SimulationStorageDatabase
    from mars_eis.core.engine import MarsSimulationEngine
    import uvicorn

    # Use workspace data directory for database persistence
    db = SimulationStorageDatabase("data/simulation_history.db")
    engine = MarsSimulationEngine(seed=42)
    app = create_app(engine=engine, db=db, time_scale=10.0, tick_rate_hz=1.0)

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True, name="MARS-EIS-Server")
    server_thread.start()
    return server_thread


def main() -> int:
    """Check backend, auto-start if needed, and run Pygame client."""
    port = 8000
    host = "127.0.0.1"

    if is_port_in_use(port, host):
        logger.info("Found existing MARS-EIS backend running at http://%s:%d. Connecting...", host, port)
    else:
        logger.info("MARS-EIS backend not detected at port %d. Starting server...", port)
        start_mars_eis_server(port=port)

        # Wait up to 5 seconds for port to open
        ready = False
        for _ in range(25):
            time.sleep(0.2)
            if is_port_in_use(port, host):
                ready = True
                break

        if ready:
            logger.info("MARS-EIS backend online and listening at http://%s:%d!", host, port)
        else:
            logger.warning("Backend did not respond in time, launching client anyway...")

    # Now launch Pygame main game loop
    import main as game_main
    return game_main.main()


if __name__ == "__main__":
    sys.exit(main())
