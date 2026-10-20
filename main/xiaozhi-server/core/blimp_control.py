"""Realtime control of the Blimp clients (any number per server).

Each Blimp keeps a control websocket open at /xiaozhi/control/ on the
conversation port, authenticated like the conversation websocket. All of them
are listed in the portal; the portal controls the selected one. The same
device reconnecting replaces its old socket (close code 4002).

Client -> server: {"type": "state", ..., "client": {user_agent, platform}} on every
                  state change, {"type": "ping"}
Server -> client: {"type": "welcome"}, {"type": "settings", barge_in} (after welcome
                  and when the portal saves it), {"type": "play", kind, id, title, path},
                  {"type": "videos", videos: [{id, title, mime, size, path}]} (after
                  welcome and on every library change; the Blimp prefetches them),
                  {"type": "stop_audio" | "pause_media" | "resume_media"},
                  {"type": "set_loop", loop}, {"type": "answer_call" | "decline_call" | "end_call"},
                  {"type": "avatar", expression?, blink?, auto_blink?, auto_recover?},
                  {"type": "conversation", action: connect | disconnect | start | interrupt
                  | send_text, text?}, {"type": "pong"}
Settings and the video list go to every Blimp; the other commands to the selected one.
"""

import asyncio
import json
import time

import websockets

from config.logger import setup_logging

TAG = __name__

CLOSE_REPLACED = 4002
# The client pings every 15 s; a silent socket is dead after this long
IDLE_TIMEOUT = 45


class _Device:
    def __init__(self, websocket):
        self.websocket = websocket
        self.connected_at = time.time()
        self.state = {}
        self.state_at = None


class BlimpControl:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.devices = {}  # device-id -> _Device, online devices only
        # The device the portal controls; kept while it is offline so a reconnect resumes it
        self.selected = None
        self.version = 0
        self._changed = asyncio.Condition()
        # async callable(send) run after each welcome; send(message) reaches that
        # device only (the portal pushes its settings and the video list)
        self.on_connect = None

    # ---------- the selected device ----------

    @property
    def online(self) -> bool:
        return self.selected in self.devices

    @property
    def device_id(self):
        return self.selected

    @property
    def state(self) -> dict:
        device = self.devices.get(self.selected)
        return device.state if device else {}

    async def select(self, device_id: str) -> bool:
        if device_id not in self.devices:
            return False
        if device_id != self.selected:
            self.selected = device_id
            self.logger.bind(tag=TAG).info(f"Blimp control: portal now controls {device_id}")
            await self._notify()
        return True

    def snapshot(self) -> dict:
        device = self.devices.get(self.selected)
        return {
            "online": device is not None,
            "device_id": self.selected,
            "connected_at": device.connected_at if device else None,
            "state": device.state if device else {},
            "state_at": device.state_at if device else None,
            "devices": [
                {
                    "device_id": device_id,
                    "connected_at": d.connected_at,
                    "client": d.state.get("client") or {},
                    "activity": d.state.get("activity"),
                }
                for device_id, d in sorted(self.devices.items(), key=lambda kv: kv[1].connected_at)
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

    # ---------- a Blimp's socket ----------

    async def handle(self, websocket, device_id: str):
        old = self.devices.get(device_id)
        device = _Device(websocket)
        self.devices[device_id] = device
        if old is not None:
            self.logger.bind(tag=TAG).info(f"Blimp control: {device_id} reconnected; replacing the old socket")
            await old.websocket.close(CLOSE_REPLACED, "replaced by a new connection")
        else:
            self.logger.bind(tag=TAG).info(f"Blimp control: {device_id} online ({len(self.devices)} connected)")
        if not self.online:
            self.selected = device_id
        await self._notify()

        async def send_here(message: dict):
            await websocket.send(json.dumps(message))

        try:
            await websocket.send(json.dumps({"type": "welcome", "device_id": device_id}))
            if self.on_connect is not None:
                try:
                    await self.on_connect(send_here)
                except websockets.ConnectionClosed:
                    raise
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Blimp control: on_connect failed: {e}")
            while True:
                raw = await asyncio.wait_for(websocket.recv(), IDLE_TIMEOUT)
                await self._on_message(device, raw)
        except asyncio.TimeoutError:
            self.logger.bind(tag=TAG).warning(f"Blimp control: {device_id} went silent; closing")
        except websockets.ConnectionClosed:
            pass
        finally:
            if self.devices.get(device_id) is device:
                del self.devices[device_id]
                self.logger.bind(tag=TAG).info(f"Blimp control: {device_id} offline")
                await self._notify()
            try:
                await websocket.close()
            except Exception:
                pass

    async def _on_message(self, device: _Device, raw):
        if not isinstance(raw, str):
            return
        try:
            msg = json.loads(raw)
        except ValueError:
            return
        if not isinstance(msg, dict):
            return
        if msg.get("type") == "ping":
            await device.websocket.send(json.dumps({"type": "pong"}))
        elif msg.get("type") == "state":
            device.state = {k: v for k, v in msg.items() if k != "type"}
            device.state_at = time.time()
            await self._notify()

    # ---------- commands ----------

    async def send(self, message: dict) -> bool:
        """Send to the selected Blimp; False when it is offline."""
        device = self.devices.get(self.selected)
        if device is None:
            return False
        try:
            await device.websocket.send(json.dumps(message))
            return True
        except websockets.ConnectionClosed:
            return False

    async def broadcast(self, message: dict):
        """Send to every connected Blimp (settings, the video list)."""
        text = json.dumps(message)
        for device in list(self.devices.values()):
            try:
                await device.websocket.send(text)
            except websockets.ConnectionClosed:
                pass
