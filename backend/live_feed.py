"""MARS SURVIVAL — Live Telemetry WebSocket Feed.

High-frequency, real-time live feed client streaming physical telemetry
from the MARS-EIS simulation engine directly into the Pygame client.
Operates on a non-blocking background asyncio thread with thread-safe queues,
automatic reconnect logic, latency tracking, and bidirectional command dispatch.

Credit:
    Made by Lunarmist-byte
    GitHub: https://github.com/Lunarmist-byte
    LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
"""

from __future__ import annotations
import asyncio
import json
import logging
import queue
import threading
import time
from typing import Dict, Any, Optional, List, Tuple
import aiohttp

from .backend_config import BackendConfig

logger = logging.getLogger(__name__)


class LiveFeedClient:
    """Non-blocking asynchronous WebSocket client for MARS-EIS live feed."""

    def __init__(self, config: Optional[BackendConfig] = None) -> None:
        self.config = config or BackendConfig()
        self.ws_url: str = self.config.get_ws_url()

        # Thread-safe queues
        self.incoming_packets: queue.Queue = queue.Queue()
        self._outgoing_queue: Optional[asyncio.Queue] = None

        # Thread & loop management
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

        # Live feed status metrics
        self.is_connected: bool = False
        self.packets_received: int = 0
        self.last_packet_timestamp: float = 0.0
        self.last_packet_data: Dict[str, Any] = {}
        self.last_error: Optional[str] = None
        self.packet_rate_hz: float = 0.0
        self.latency_ms: float = 0.0

        # Rate estimation sliding window
        self._packet_timestamps: List[float] = []
        self._rate_lock = threading.Lock()

    def start(self) -> None:
        """Start the background live feed worker thread."""
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_event_loop,
            name="MarsLiveFeedWorker",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"[LiveFeed] Worker thread initiated connecting to {self.ws_url}")

    def stop(self) -> None:
        """Stop the background worker thread gracefully."""
        self._is_running = False
        self._stop_event.set()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        logger.info("[LiveFeed] Worker thread stopped.")

    # -------------------------------------------------------------------------
    # Bidirectional Command Dispatch (Thread-Safe from Pygame main thread)
    # -------------------------------------------------------------------------
    def send_player_move(self, distance_meters: float, speed_ms: float = 1.2, slope_pct: float = 0.0) -> bool:
        """Queue instantaneous movement packet to MARS-EIS via live feed."""
        return self._enqueue_outgoing({
            "type": "PLAYER_MOVE",
            "distance_meters": float(distance_meters),
            "speed_ms": float(speed_ms),
            "slope_pct": float(slope_pct),
        })

    def send_player_action(self, action_type: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Queue instantaneous player action packet via live feed."""
        return self._enqueue_outgoing({
            "type": "PLAYER_ACTION",
            "action_type": action_type,
            "parameters": parameters or {},
        })

    def send_trigger_catastrophe(self, catastrophe_type: str, severity: float = 1.0) -> bool:
        """Queue catastrophe injection request via live feed."""
        return self._enqueue_outgoing({
            "type": "TRIGGER_CATASTROPHE",
            "catastrophe_type": catastrophe_type,
            "severity": float(severity),
        })

    def _enqueue_outgoing(self, payload: Dict[str, Any]) -> bool:
        """Dispatch packet into asyncio queue thread-safely."""
        if not self.is_connected or not self._loop or not self._outgoing_queue:
            return False
        try:
            self._loop.call_soon_threadsafe(self._outgoing_queue.put_nowait, payload)
            return True
        except Exception as exc:
            logger.debug(f"[LiveFeed] Failed to enqueue outgoing command: {exc}")
            return False

    # -------------------------------------------------------------------------
    # Main Thread Packet Retrieval
    # -------------------------------------------------------------------------
    def get_packets(self, max_packets: int = 50) -> List[Tuple[str, Dict[str, Any]]]:
        """Drain up to max_packets incoming telemetry messages on Pygame frame."""
        packets = []
        count = 0
        while count < max_packets and not self.incoming_packets.empty():
            try:
                item = self.incoming_packets.get_nowait()
                packets.append(item)
                count += 1
            except queue.Empty:
                break
        return packets

    # -------------------------------------------------------------------------
    # Async Event Loop Runner
    # -------------------------------------------------------------------------
    def _run_event_loop(self) -> None:
        """Dedicated asyncio event loop running on worker thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connection_supervisor())
        except (asyncio.CancelledError, RuntimeError):
            pass
        except Exception as exc:
            logger.warning(f"[LiveFeed] Event loop terminated: {exc}")
        finally:
            self.is_connected = False
            try:
                self._loop.close()
            except Exception:
                pass

    async def _connection_supervisor(self) -> None:
        """Persistent connection supervisor with automatic reconnection loop."""
        self._outgoing_queue = asyncio.Queue()

        while not self._stop_event.is_set():
            try:
                self.incoming_packets.put(("STATUS", {"status": "CONNECTING", "ws_url": self.ws_url}))
                timeout = aiohttp.ClientTimeout(total=self.config.request_timeout_seconds)

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.ws_connect(self.ws_url, heartbeat=15.0) as ws:
                        self.is_connected = True
                        self.last_error = None
                        logger.info(f"[LiveFeed] Connected to MARS-EIS live feed at {self.ws_url}")
                        self.incoming_packets.put(("STATUS", {"status": "CONNECTED", "ws_url": self.ws_url}))

                        # Run sender and receiver concurrently
                        receiver_task = asyncio.create_task(self._receive_loop(ws))
                        sender_task = asyncio.create_task(self._send_loop(ws))

                        done, pending = await asyncio.wait(
                            [receiver_task, sender_task],
                            return_when=asyncio.FIRST_COMPLETED,
                        )

                        for t in pending:
                            t.cancel()

            except aiohttp.ClientConnectorError as conn_err:
                self.is_connected = False
                self.last_error = f"Connection refused ({conn_err})"
                self.incoming_packets.put(("STATUS", {"status": "DISCONNECTED", "error": self.last_error}))
            except Exception as exc:
                self.is_connected = False
                self.last_error = str(exc)
                self.incoming_packets.put(("STATUS", {"status": "DISCONNECTED", "error": self.last_error}))

            # Backoff delay before reconnecting
            if not self._stop_event.is_set():
                reconnect_delay = max(1.0, self.config.reconnect_interval_seconds)
                for _ in range(int(reconnect_delay * 10)):
                    if self._stop_event.is_set():
                        break
                    await asyncio.sleep(0.1)

    async def _receive_loop(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        """Stream incoming messages from MARS-EIS WebSocket."""
        async for msg in ws:
            if self._stop_event.is_set():
                break

            if msg.type == aiohttp.WSMsgType.TEXT:
                now = time.time()
                try:
                    payload = json.loads(msg.data)
                    msg_type = payload.get("type", "TELEMETRY_UPDATE")

                    # Record statistics
                    self.packets_received += 1
                    self.last_packet_timestamp = now
                    self.last_packet_data = payload

                    with self._rate_lock:
                        self._packet_timestamps.append(now)
                        # Keep only timestamps within the last 5 seconds
                        cutoff = now - 5.0
                        self._packet_timestamps = [t for t in self._packet_timestamps if t >= cutoff]
                        if len(self._packet_timestamps) > 1:
                            span = self._packet_timestamps[-1] - self._packet_timestamps[0]
                            self.packet_rate_hz = round((len(self._packet_timestamps) - 1) / max(0.1, span), 2)
                        else:
                            self.packet_rate_hz = 1.0

                    # Deliver parsed message to Pygame main thread
                    self.incoming_packets.put((msg_type, payload))

                except Exception as parse_err:
                    logger.debug(f"[LiveFeed] Failed to parse JSON packet: {parse_err}")

            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                break

    async def _send_loop(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        """Stream outgoing commands from Pygame main thread to MARS-EIS."""
        while not self._stop_event.is_set():
            if self._outgoing_queue is None:
                await asyncio.sleep(0.05)
                continue

            try:
                # Wait for command with periodic cancellation check
                cmd_payload = await asyncio.wait_for(self._outgoing_queue.get(), timeout=0.2)
                text = json.dumps(cmd_payload)
                await ws.send_str(text)
                self._outgoing_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as send_err:
                logger.debug(f"[LiveFeed] Error sending command to websocket: {send_err}")
                break
