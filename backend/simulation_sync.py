"""MARS SURVIVAL — Simulation Synchronization Layer.

Non-blocking background thread worker managing communication between Pygame
and the MARS-EIS simulation engine. Dispatches HTTP requests asynchronously,
delivers updates via thread-safe queues, enforces concurrency limits on advance
requests, preserves last valid simulation state during disconnections, and
never blocks the Pygame main rendering loop.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import logging
import queue
import threading
import time
from typing import Dict, Any, Optional, Tuple, List

from .api_client import ApiClient
from .backend_config import BackendConfig
from .live_feed import LiveFeedClient
from world.world_state import WorldState
from world.player_state import PlayerState

logger = logging.getLogger(__name__)


class SimulationSync:
    """Thread-safe asynchronous synchronizer for MARS-EIS with WebSocket Live Feed & REST fallback."""

    def __init__(self, config: Optional[BackendConfig] = None) -> None:
        self.config = config or BackendConfig()
        self.client = ApiClient(self.config)
        self.live_feed = LiveFeedClient(self.config)

        # Thread synchronization primitives
        self._command_queue: queue.Queue = queue.Queue()
        self._results_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()

        # Concurrency guards
        self._advance_in_flight = False
        self._lock = threading.Lock()

        # Thread reference
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="MarsSimulationSyncWorker",
            daemon=True
        )

    def start(self) -> None:
        """Launch non-blocking background synchronization worker and live telemetry feed."""
        self._stop_event.clear()
        self.live_feed.start()
        if not self._worker_thread.is_alive():
            self._worker_thread.start()
            logger.info("[Sync] MARS-EIS synchronization worker thread and live feed started.")

    def stop(self) -> None:
        """Signal worker thread and live feed to gracefully terminate."""
        self._stop_event.set()
        self.live_feed.stop()
        self._command_queue.put(("SHUTDOWN", {}))
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.5)
            logger.info("[Sync] Worker thread terminated cleanly.")

    # -------------------------------------------------------------------------
    # Public Command Submission (Called from Main Thread)
    # -------------------------------------------------------------------------
    def request_state_sync(self) -> None:
        """Queue immediate state poll."""
        self._command_queue.put(("POLL_STATE", {}))

    def request_advance(self, dt_seconds: Optional[float] = None, sols: float = 0.0) -> bool:
        """Queue simulation time advancement if not already in-flight."""
        with self._lock:
            if self._advance_in_flight:
                return False  # Prevent overlapping advance requests
            self._advance_in_flight = True

        dt = dt_seconds if dt_seconds is not None else self.config.delta_simulation_seconds
        self._command_queue.put(("ADVANCE", {"dt_seconds": dt, "sols": sols}))
        return True

    def dispatch_action(self, action_type: str, parameters: Dict[str, Any], action_id: str = "") -> None:
        """Queue player or robotic action for backend processing.
        
        Attempts low-latency WebSocket live dispatch if connected, otherwise routes via REST.
        """
        if self.live_feed.is_connected:
            sent = self.live_feed.send_player_action(action_type, parameters)
            if sent:
                return
        self._command_queue.put(("ACTION", {
            "action_type": action_type,
            "parameters": parameters,
            "action_id": action_id
        }))

    def report_movement(
        self,
        distance_meters: float,
        speed_ms: float = 1.2,
        heading_deg: float = 0.0,
        world_position: Optional[List[float]] = None
    ) -> None:
        """Queue continuous movement report for regolith disturbance calculation.
        
        Uses real-time WebSocket live feed if streaming, falling back to HTTP REST.
        """
        if self.live_feed.is_connected:
            sent = self.live_feed.send_player_move(distance_meters, speed_ms)
            if sent:
                return
        self._command_queue.put(("MOVEMENT", {
            "distance_meters": distance_meters,
            "speed_ms": speed_ms,
            "heading_deg": heading_deg,
            "world_position": world_position or [0.0, 0.0, 0.0],
        }))

    def trigger_catastrophe(self, catastrophe_type: str, severity: float = 0.8) -> None:
        """Queue procedural or manual environmental catastrophe injection into MARS-EIS."""
        if self.live_feed.is_connected:
            sent = self.live_feed.send_trigger_catastrophe(catastrophe_type, severity)
            if sent:
                return
        self._command_queue.put(("TRIGGER_CATASTROPHE", {
            "catastrophe_type": catastrophe_type,
            "severity": float(severity),
        }))

    def apply_scenario(self, scenario_id: str) -> None:
        """Queue loading and activating a preset scientific scenario in MARS-EIS."""
        self._command_queue.put(("APPLY_SCENARIO", {
            "scenario_id": scenario_id,
        }))

    # -------------------------------------------------------------------------
    # Main Thread Frame Update (Called once per Pygame frame)
    # -------------------------------------------------------------------------
    def poll_results(self, world_state: WorldState, player_state: Optional[PlayerState] = None) -> None:
        """Drain live WebSocket stream and REST results queue to update models on the main thread."""
        # 1. Process High-Frequency Live Feed Telemetry Packets
        live_packets = self.live_feed.get_packets()
        for msg_type, payload in live_packets:
            if msg_type == "TELEMETRY_UPDATE":
                world_state.update_from_backend(payload)
                world_state.is_live_feed = True
                world_state.live_feed_packets = self.live_feed.packets_received
                world_state.live_feed_rate_hz = self.live_feed.packet_rate_hz
                world_state.simulation_status = f"LIVE FEED ({self.live_feed.packet_rate_hz:.1f} Hz)"
                world_state.connection_error = None

            elif msg_type == "MOVE_ACK":
                telemetry = payload.get("telemetry")
                if telemetry and isinstance(telemetry, dict):
                    world_state.update_from_backend(telemetry)
                if "catastrophes" in payload and isinstance(payload["catastrophes"], list):
                    world_state.catastrophes = payload["catastrophes"]

            elif msg_type == "ACTION_ACK":
                success = payload.get("success", True)
                message = payload.get("message", f"Action {payload.get('action_type', '')} executed.")
                if player_state:
                    player_state.set_action_feedback(message, success)
                telemetry = payload.get("telemetry")
                if telemetry and isinstance(telemetry, dict):
                    world_state.update_from_backend(telemetry)
                if "catastrophes" in payload and isinstance(payload["catastrophes"], list):
                    world_state.catastrophes = payload["catastrophes"]

            elif msg_type == "CATASTROPHE_ALERT":
                cat = payload.get("catastrophe")
                if cat:
                    cat_dict = cat if isinstance(cat, dict) else {"name": str(cat)}
                    world_state.catastrophes.append(cat_dict)
                    if player_state:
                        c_name = cat_dict.get("name", "Catastrophe")
                        player_state.set_action_feedback(f"CRITICAL ALERT: {c_name.upper()} ACTIVE!", False)
                telemetry = payload.get("telemetry")
                if telemetry and isinstance(telemetry, dict):
                    world_state.update_from_backend(telemetry)

            elif msg_type == "STATUS":
                status = payload.get("status")
                if status == "DISCONNECTED":
                    world_state.is_live_feed = False
                    if world_state.simulation_status.startswith("LIVE FEED"):
                        world_state.simulation_status = "REST FALLBACK"

        # 2. Process REST Background Worker Queue
        while not self._results_queue.empty():
            try:
                msg_type, payload = self._results_queue.get_nowait()
            except queue.Empty:
                break

            if msg_type == "STATE_UPDATE":
                data = payload.get("data", {})
                version = payload.get("version")
                # Update if not streaming live feed or if REST has newer authoritative data
                if not world_state.is_live_feed or not self.live_feed.is_connected:
                    world_state.update_from_backend(data, version=version)

            elif msg_type == "CONNECTION_STATUS":
                status = payload.get("status", "DISCONNECTED")
                error = payload.get("error")
                if not world_state.is_live_feed:
                    world_state.simulation_status = status
                    world_state.connection_error = error

            elif msg_type == "ACTION_RESULT":
                success = payload.get("success", False)
                message = payload.get("message", "")
                if player_state:
                    player_state.set_action_feedback(message, success)

            elif msg_type == "EVENTS_UPDATE":
                events = payload.get("events", [])
                world_state.active_events = events

            elif msg_type == "CATASTROPHE_RESULT":
                success = payload.get("success", False)
                message = payload.get("message", "")
                if player_state:
                    player_state.set_action_feedback(message, success)
                data = payload.get("data", {})
                if "world_state" in data:
                    world_state.update_from_backend(data["world_state"])
                if "catastrophe" in data and isinstance(data["catastrophe"], dict):
                    world_state.catastrophes.append(data["catastrophe"])

            elif msg_type == "SCENARIO_RESULT":
                success = payload.get("success", False)
                message = payload.get("message", "")
                if player_state:
                    player_state.set_action_feedback(message, success)
                data = payload.get("data", {})
                if "world_state" in data:
                    world_state.update_from_backend(data["world_state"])

    # -------------------------------------------------------------------------
    # Background Worker Loop (Executes on Worker Thread)
    # -------------------------------------------------------------------------
    def _worker_loop(self) -> None:
        """Long-running background network coordinator."""
        last_sync_time = 0.0
        last_advance_time = 0.0
        is_connected = False

        # Attempt initial handshake immediately
        self._notify_status("CONNECTING", None)
        ok, data, msg = self.client.get_world_state()
        if ok and data:
            is_connected = True
            self._notify_status("CONNECTED", None)
            self._results_queue.put(("STATE_UPDATE", {"data": data}))
            last_sync_time = time.time()
        else:
            is_connected = False
            self._notify_status("DISCONNECTED", msg)

        while not self._stop_event.is_set():
            now = time.time()

            # 1. Process queued commands from main game loop
            while not self._command_queue.empty():
                try:
                    cmd_type, args = self._command_queue.get_nowait()
                except queue.Empty:
                    break

                if cmd_type == "SHUTDOWN":
                    return

                elif cmd_type == "POLL_STATE":
                    ok, data, msg = self.client.get_world_state()
                    if ok and data:
                        is_connected = True
                        self._notify_status("CONNECTED", None)
                        self._results_queue.put(("STATE_UPDATE", {"data": data}))
                        last_sync_time = now
                    else:
                        is_connected = False
                        self._notify_status("DISCONNECTED", msg)

                elif cmd_type == "ADVANCE":
                    dt = args.get("dt_seconds", self.config.delta_simulation_seconds)
                    sols = args.get("sols", 0.0)
                    ok, data, msg = self.client.advance_simulation(delta_simulation_seconds=dt, sols=sols)
                    with self._lock:
                        self._advance_in_flight = False

                    if ok and data:
                        is_connected = True
                        self._notify_status("CONNECTED", None)
                        self._results_queue.put(("STATE_UPDATE", {"data": data}))
                        last_advance_time = now
                        last_sync_time = now
                    else:
                        self._notify_status("DISCONNECTED", msg)

                elif cmd_type == "ACTION":
                    act_type = args.get("action_type", "")
                    params = args.get("parameters", {})
                    ok, data, msg = self.client.send_action(act_type, params)
                    self._results_queue.put(("ACTION_RESULT", {
                        "success": ok,
                        "message": msg,
                        "action_type": act_type,
                        "data": data,
                    }))
                    # If action modified state, immediately refresh state
                    if ok:
                        s_ok, s_data, _ = self.client.get_world_state()
                        if s_ok and s_data:
                            self._results_queue.put(("STATE_UPDATE", {"data": s_data}))

                elif cmd_type == "MOVEMENT":
                    dist = args.get("distance_meters", 1.0)
                    spd = args.get("speed_ms", 1.2)
                    hdg = args.get("heading_deg", 0.0)
                    wpos = args.get("world_position")
                    ok, data, msg = self.client.send_movement(dist, spd, hdg, world_position=wpos)
                    if ok and data and "world_state" in data:
                        self._results_queue.put(("STATE_UPDATE", {"data": data["world_state"]}))

                elif cmd_type == "TRIGGER_CATASTROPHE":
                    cat_type = args.get("catastrophe_type", "")
                    sev = args.get("severity", 0.8)
                    ok, data, msg = self.client.trigger_catastrophe(cat_type, sev)
                    self._results_queue.put(("CATASTROPHE_RESULT", {
                        "success": ok,
                        "message": msg,
                        "data": data or {},
                    }))
                    if ok and data and "world_state" in data:
                        self._results_queue.put(("STATE_UPDATE", {"data": data["world_state"]}))
                    elif ok:
                        s_ok, s_data, _ = self.client.get_world_state()
                        if s_ok and s_data:
                            self._results_queue.put(("STATE_UPDATE", {"data": s_data}))

                elif cmd_type == "APPLY_SCENARIO":
                    scen_id = args.get("scenario_id", "")
                    ok, data, msg = self.client.apply_scenario(scen_id)
                    self._results_queue.put(("SCENARIO_RESULT", {
                        "success": ok,
                        "message": msg,
                        "data": data or {},
                    }))
                    if ok and data and "world_state" in data:
                        self._results_queue.put(("STATE_UPDATE", {"data": data["world_state"]}))
                    elif ok:
                        s_ok, s_data, _ = self.client.get_world_state()
                        if s_ok and s_data:
                            self._results_queue.put(("STATE_UPDATE", {"data": s_data}))

            # 2. Periodic state polling and automatic simulation advance
            if is_connected:
                # Automatic simulation advance (if enabled)
                if self.config.automatic_advance and (now - last_advance_time >= self.config.sync_interval_seconds * 2):
                    with self._lock:
                        can_advance = not self._advance_in_flight
                        if can_advance:
                            self._advance_in_flight = True
                    if can_advance:
                        ok, data, msg = self.client.advance_simulation(
                            delta_simulation_seconds=self.config.delta_simulation_seconds
                        )
                        with self._lock:
                            self._advance_in_flight = False
                        if ok and data:
                            self._results_queue.put(("STATE_UPDATE", {"data": data}))
                            last_advance_time = now
                            last_sync_time = now
                        else:
                            is_connected = False
                            self._notify_status("DISCONNECTED", msg)

                # Periodic world state sync (active only when live feed is not streaming)
                elif now - last_sync_time >= self.config.sync_interval_seconds:
                    live_feed_active = self.live_feed.is_connected and (now - self.live_feed.last_packet_timestamp < 3.0)
                    if not live_feed_active:
                        ok, data, msg = self.client.get_world_state()
                        if ok and data:
                            self._results_queue.put(("STATE_UPDATE", {"data": data}))
                            last_sync_time = now
                        else:
                            is_connected = False
                            self._notify_status("DISCONNECTED", msg)
                    else:
                        last_sync_time = now

            else:
                # In disconnected state: retry connection at reconnect intervals
                if now - last_sync_time >= self.config.reconnect_interval_seconds:
                    ok, data, msg = self.client.get_world_state()
                    if ok and data:
                        is_connected = True
                        self._notify_status("CONNECTED", None)
                        self._results_queue.put(("STATE_UPDATE", {"data": data}))
                        last_sync_time = now
                    else:
                        self._notify_status("DISCONNECTED", msg)
                        last_sync_time = now

            # Sleep briefly to avoid busy-spinning
            time.sleep(0.05)

    def _notify_status(self, status: str, error: Optional[str]) -> None:
        """Post connection status update to main thread queue."""
        self._results_queue.put(("CONNECTION_STATUS", {"status": status, "error": error}))
