"""Realtime control of the Blimp client (one Blimp per server).

The Blimp keeps a control websocket open at /xiaozhi/control/ on the
conversation port, authenticated like the conversation websocket. The first
device to connect owns the slot; while it is online other devices are refused
(close code 4003) and listed as blocked. The same device reconnecting replaces
its old socket (close code 4002).

Client -> server: {"type": "state", ...} on every state change, {"type": "ping"}
Server -> client: {"type": "welcome"}, {"type": "settings", barge_in} (after welcome
                  and when the portal saves it), {"type": "play", kind, id, title, path},
                  {"type": "videos", videos: [{id, title, mime, size, path}]} (after
                  welcome and on every library change; the Blimp prefetches them),
                  {"type": "stop_audio" | "pause_media" | "resume_media"},
                  {"type": "set_loop", loop}, {"type": "answer_call" | "decline_call" | "end_call"},
                  {"type": "pong"}
"""

import asyncio
import json
import time

import websockets

from config.logger import setup_logging

TAG = __name__

CLOSE_REPLACED = 4002
CLOSE_BLOCKED = 4003
# The client pings every 15 s; a silent socket is dead after this long
IDLE_TIMEOUT = 45
MAX_BLOCKED = 10


class BlimpControl:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.websocket = None
        self.device_id = None
        self.connected_at = None
        self.state = {}
        self.state_at = None
        self.blocked = {}  # device-id -> last refused time
        self.version = 0
        self._changed = asyncio.Condition()
        # async callable run after each welcome (the portal pushes the video list)
        self.on_connect = None

    @property
    def online(self) -> bool:
        return self.websocket is not None

    def snapshot(self) -> dict:
        return {
            "online": self.online,
            "device_id": self.device_id if self.online else None,
            "connected_at": self.connected_at if self.online else None,
            "state": self.state if self.online else {},
            "state_at": self.state_at,
            "blocked": [
                {"device_id": d, "at": t}
                for d, t in sorted(self.blocked.items(), key=lambda kv: -kv[1])
            ],
            "now": time.time(),
        }

    async def _notify(self):
        async with self._changed:
            self.version += 1
            self._changed.notify_all()

    async def wait_change(self, seen: int, timeout: float) -> int:
        """Wait until the snapshot changes from version `seen`; returns the new version."""
        async with self._changed:
            try:
                await asyncio.wait_for(
                    self._changed.wait_for(lambda: self.version != seen), timeout
                )
            except asyncio.TimeoutError:
                pass
            return self.version

    # ---------- the Blimp's socket ----------

    async def handle(self, websocket, device_id: str):
        if self.online and device_id != self.device_id:
            self.blocked[device_id] = time.time()
            while len(self.blocked) > MAX_BLOCKED:
                self.blocked.pop(min(self.blocked, key=self.blocked.get))
            self.logger.bind(tag=TAG).warning(
                f"Blimp control: refused {device_id}, {self.device_id} is already connected"
            )
            await self._notify()
            await websocket.close(CLOSE_BLOCKED, "another Blimp is connected")
            return

        old = self.websocket
        self.websocket, self.device_id = websocket, device_id
        self.connected_at, self.state, self.state_at = time.time(), {}, None
        self.blocked.pop(device_id, None)
        if old is not None:
            self.logger.bind(tag=TAG).info(f"Blimp control: {device_id} reconnected; replacing the old socket")
            await old.close(CLOSE_REPLACED, "replaced by a new connection")
        else:
            self.logger.bind(tag=TAG).info(f"Blimp control: {device_id} online")
        await self._notify()

        try:
            await websocket.send(json.dumps({"type": "welcome", "device_id": device_id}))
            if self.on_connect is not None:
                try:
                    await self.on_connect()
                except websockets.ConnectionClosed:
                    raise
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Blimp control: on_connect failed: {e}")
            while True:
                raw = await asyncio.wait_for(websocket.recv(), IDLE_TIMEOUT)
                await self._on_message(websocket, raw)
        except asyncio.TimeoutError:
            self.logger.bind(tag=TAG).warning(f"Blimp control: {device_id} went silent; closing")
        except websockets.ConnectionClosed:
            pass
        finally:
            if self.websocket is websocket:
                self.websocket = None
                self.state = {}
                self.logger.bind(tag=TAG).info(f"Blimp control: {device_id} offline")
                await self._notify()
            try:
                await websocket.close()
            except Exception:
                pass

    async def _on_message(self, websocket, raw):
        if not isinstance(raw, str):
            return
        try:
            msg = json.loads(raw)
        except ValueError:
            return
        if not isinstance(msg, dict):
            return
        if msg.get("type") == "ping":
            await websocket.send(json.dumps({"type": "pong"}))
        elif msg.get("type") == "state" and websocket is self.websocket:
            self.state = {k: v for k, v in msg.items() if k != "type"}
            self.state_at = time.time()
            await self._notify()

    # ---------- commands ----------

    async def send(self, message: dict) -> bool:
        ws = self.websocket
        if ws is None:
            return False
        try:
            await ws.send(json.dumps(message))
            return True
        except websockets.ConnectionClosed:
            return False
