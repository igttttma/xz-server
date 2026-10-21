"""Lightweight settings portal for standalone deployments.

Edits a handful of settings in data/.config.yaml (comments preserved) and
hot-reloads the server; changes apply to new connections. Also shows whether
the Blimp is online (live, over server-sent events) and keeps an audio
library and a video library the Blimp can be told to play (it prefetches
the videos so they start at once). Access: requests from this machine are
allowed; remote requests only with `portal.password` (HTTP Basic auth, any
user name). The Blimp fetches media through short-lived signed URLs instead.
"""

import io
import json
import time
import asyncio
import hashlib
import os
import re
import hmac
import base64
import ipaddress

import yaml
from aiohttp import web
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import LiteralScalarString

from config.config_loader import get_project_dir
from core.media_library import AUDIO_TYPES, VIDEO_TYPES, MediaLibrary, UploadError
from config.logger import setup_logging
from plugins_func.register import all_function_registry

TAG = __name__

CONFIG_PATH = get_project_dir() + "data/.config.yaml"
# The shipped defaults (data/.config.yaml overrides them)
DEFAULT_CONFIG_PATH = get_project_dir() + "config.yaml"
# An edit value that removes the key from data/.config.yaml (back to the default)
REMOVE = object()
MEMORY_PATH = get_project_dir() + "data/.memory.yaml"
PAGE_PATH = os.path.join(os.path.dirname(__file__), "portal", "index.html")

# Modules that share the platform API key and have an editable model name;
# the settings field for each is "<module>_model" (e.g. "asr_model")
KEY_MODULES = ("ASR", "LLM", "TTS")  # images go to the LLM, so VLLM is unused
# Tools the server always provides; not switchable
NECESSARY_TOOLS = ("handle_exit_intent", "get_lunar")
# Plugins removed from this deployment (need services we don't run, or conflict
# with the persona); never shown or enabled by the portal
REMOVED_TOOLS = (
    "web_search", "play_music", "change_role", "call_device", "search_from_ragflow",
    "hass_get_state", "hass_set_state", "hass_play_music",
)
WAKE_GREETING_MODES = ("cached", "none", "llm")
MEMORY_ON, MEMORY_OFF = "mem_local_short", "nomem"
LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")
# How long a signed media link stays valid (covers range requests while playing
# and prefetching; every video list push signs fresh links)
MEDIA_URL_TTL = 6 * 3600


def _mask(key: str) -> str:
    if not key or "your" in key:
        return ""
    return key[:3] + "****" + key[-4:] if len(key) > 10 else "****"


def _last_leaf(node):
    """The (map, key) whose comment holds the trailing blank lines of a ruamel map."""
    while isinstance(node, CommentedMap) and len(node):
        key = list(node.keys())[-1]
        if isinstance(node[key], CommentedMap) and len(node[key]):
            node = node[key]
            continue
        return node, key
    return None, None


def _add(node, key, value):
    """Set node[key]; a new key goes before the previous last key's trailing blank lines."""
    if key in node:
        node[key] = value
        return
    tail_map, tail_key = _last_leaf(node)
    tail = tail_map.ca.items.pop(tail_key, None) if tail_map is not None else None
    node[key] = value
    if tail:
        new_map, new_key = (node, key) if not isinstance(value, CommentedMap) else _last_leaf(node)
        new_map.ca.items[new_key] = tail


def _set_in(doc, path, value):
    """Set a nested key in a ruamel document, creating maps as needed; REMOVE deletes it."""
    if value is REMOVE:
        for key in path[:-1]:
            doc = doc.get(key)
            if doc is None:
                return
        doc.pop(path[-1], None)
        return
    for key in path[:-1]:
        if doc.get(key) is None:
            _add(doc, key, CommentedMap())
        doc = doc[key]
    _add(doc, path[-1], value)


class PortalHandler:
    def __init__(self, config: dict, ws_server):
        self.config = config  # shared with the server; updated in place on reload
        self.ws_server = ws_server
        self.logger = setup_logging()
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.width = 4096
        self._yaml.indent(mapping=2, sequence=4, offset=2)
        self.audio = MediaLibrary("audio", AUDIO_TYPES, max_mb=50)
        self.video = MediaLibrary("video", VIDEO_TYPES, max_mb=500)
        self.libraries = {"audio": self.audio, "video": self.video}
        # When the Blimp connects it gets its settings and the video list (to prefetch)
        ws_server.blimp_control.on_connect = self._on_blimp_connect

    # ---------- access control ----------

    def _allowed(self, request: web.Request) -> bool:
        password = str((self.config.get("portal") or {}).get("password") or "")
        try:
            local = ipaddress.ip_address(request.remote or "").is_loopback
        except ValueError:
            local = False
        # Host check blocks DNS-rebinding pages from reaching the local portal
        host = request.host.rsplit(":", 1)[0] if not request.host.startswith("[") else request.host.split("]")[0] + "]"
        if local and host in LOCAL_HOSTS:
            return True
        if not password:
            return False
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return False
        try:
            supplied = base64.b64decode(auth[6:]).decode("utf-8").split(":", 1)[1]
        except Exception:
            return False
        return hmac.compare_digest(supplied.encode(), password.encode())

    def _guard(self, request: web.Request, mutating: bool = False):
        if not self._allowed(request):
            return web.Response(
                status=401,
                text="Portal is local-only. Set portal.password in data/.config.yaml for remote access.",
                headers={"WWW-Authenticate": 'Basic realm="BlimpMate portal"'},
            )
        # A custom header forces a CORS preflight, so other sites can't post here
        if mutating and request.headers.get("X-Portal") != "1":
            return web.Response(status=403, text="missing X-Portal header")
        return None

    # ---------- settings ----------

    def _selected(self, module: str) -> str:
        return self.config.get("selected_module", {}).get(module, "")

    def _module_cfg(self, module: str) -> dict:
        return self.config.get(module, {}).get(self._selected(module), {}) or {}

    def _model_key(self, module: str) -> str:
        """Providers name the model setting either `model_name` or `model`."""
        cfg = self._module_cfg(module)
        for key in ("model_name", "model"):
            if key in cfg:
                return key
        return "model_name" if cfg.get("type") == "openai" else "model"

    def _settings(self) -> dict:
        llm, tts = self._module_cfg("LLM"), self._module_cfg("TTS")
        intent = self._module_cfg("Intent")
        enabled = set(intent.get("functions", []) or [])
        tools = [
            {
                "name": name,
                "enabled": name in enabled,
                "description": (item.description or {}).get("function", {}).get("description", "").split("\n")[0][:140],
            }
            for name, item in sorted(all_function_registry.items())
            if name not in NECESSARY_TOOLS and name not in REMOVED_TOOLS
        ]
        return {
            "api_key": _mask(llm.get("api_key", "")),
            "key_modules": [f"{m}: {self._selected(m)}" for m in KEY_MODULES if self._selected(m)],
            "providers": {m: self._selected(m) for m in KEY_MODULES},
            **{
                f"{m.lower()}_model": self._module_cfg(m).get(self._model_key(m), "")
                for m in KEY_MODULES
            },
            "voice": tts.get("voice", ""),
            "prompt": self.config.get("prompt", ""),
            "default_prompt": self._default_prompt(),
            "memory_enabled": self._selected("Memory") == MEMORY_ON,
            "tools_supported": "functions" in intent,
            "tools": tools,
            "wake_greeting": self.config.get("wake_greeting", "cached"),
            "barge_in": bool(self.config.get("barge_in", False)),
            "max_tokens": llm.get("max_tokens", 500),
            "idle_timeout": self.config.get("close_connection_no_voice_time", 120),
        }

    def _default_prompt(self) -> str:
        """The persona prompt shipped in config.yaml, trimmed."""
        try:
            with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
                return str((yaml.safe_load(f) or {}).get("prompt", "")).replace("\r\n", "\n").strip()
        except (OSError, yaml.YAMLError):
            return ""

    def _validate(self, body: dict) -> list:
        """Turn a (partial) settings payload into [(path, value)] edits."""
        edits = []

        def int_in(name, lo, hi):
            try:
                value = int(body[name])
            except (TypeError, ValueError):
                raise ValueError(f"{name} must be a number")
            if not lo <= value <= hi:
                raise ValueError(f"{name} must be between {lo} and {hi}")
            return value

        if body.get("api_key"):
            key = str(body["api_key"]).strip()
            for module in KEY_MODULES:
                if self._selected(module):
                    edits.append(((module, self._selected(module), "api_key"), key))
        for module in KEY_MODULES:
            field = f"{module.lower()}_model"
            if field in body and self._selected(module):
                model = str(body[field]).strip()
                if not model:
                    raise ValueError(f"{module} model name is required")
                edits.append(((module, self._selected(module), self._model_key(module)), model))
        if "voice" in body:
            voice = str(body["voice"]).strip()
            if not voice:
                raise ValueError("voice is required")
            edits.append((("TTS", self._selected("TTS"), "voice"), voice))
        if "prompt" in body:
            prompt = str(body["prompt"]).replace("\r\n", "\n").strip()
            if not prompt:
                raise ValueError("persona prompt is required")
            if prompt == self._default_prompt():
                # The default: drop the override so later changes to the default apply
                edits.append((("prompt",), REMOVE))
            else:
                edits.append((("prompt",), LiteralScalarString(prompt + "\n")))
        if "memory_enabled" in body:
            if body["memory_enabled"]:
                edits.append((("selected_module", "Memory"), MEMORY_ON))
                # Summarize with the selected LLM (the upstream default needs its own key)
                edits.append((("Memory", MEMORY_ON, "llm"), self._selected("LLM")))
            else:
                edits.append((("selected_module", "Memory"), MEMORY_OFF))
        if "tools" in body:
            known = set(all_function_registry) - set(NECESSARY_TOOLS) - set(REMOVED_TOOLS)
            tools = [t for t in body["tools"] if t in known]
            edits.append((("Intent", self._selected("Intent"), "functions"), tools))
        if "wake_greeting" in body:
            if body["wake_greeting"] not in WAKE_GREETING_MODES:
                raise ValueError("unknown wake greeting mode")
            edits.append((("wake_greeting",), body["wake_greeting"]))
        if "barge_in" in body:
            if not isinstance(body["barge_in"], bool):
                raise ValueError("barge_in must be true or false")
            edits.append((("barge_in",), body["barge_in"]))
        if "max_tokens" in body:
            edits.append((("LLM", self._selected("LLM"), "max_tokens"), int_in("max_tokens", 50, 8000)))
        if "idle_timeout" in body:
            edits.append((("close_connection_no_voice_time",), int_in("idle_timeout", 10, 3600)))
        return edits

    def _write(self, edits: list):
        with open(CONFIG_PATH, "r", encoding="utf-8", newline="") as f:
            raw = f.read()
        doc = self._yaml.load(raw) or CommentedMap()
        top_level = set(doc.keys())
        for path, value in edits:
            _set_in(doc, path, value)
        out = io.StringIO()
        self._yaml.dump(doc, out)
        text = out.getvalue()
        # Blank line before newly added top-level sections, like the rest of the file
        for key in set(doc.keys()) - top_level:
            text = re.sub(rf"(?<=[^\n])\n(?={re.escape(key)}:)", "\n\n", text)
        if "\r\n" in raw:
            text = text.replace("\n", "\r\n")
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, CONFIG_PATH)

    # ---------- memory ----------

    def _read_memory(self) -> dict:
        if not os.path.exists(MEMORY_PATH):
            return {}
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # ---------- routes ----------

    async def handle_redirect(self, request: web.Request):
        raise web.HTTPFound("/portal/")

    async def handle_page(self, request: web.Request):
        if (denied := self._guard(request)) is not None:
            return denied
        return web.FileResponse(PAGE_PATH, headers={"Cache-Control": "no-store"})

    async def handle_get_settings(self, request: web.Request):
        if (denied := self._guard(request)) is not None:
            return denied
        return web.json_response(self._settings())

    async def handle_post_settings(self, request: web.Request):
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        try:
            body = await request.json()
            edits = self._validate(body if isinstance(body, dict) else {})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        if not edits:
            return web.json_response({"settings": self._settings(), "reloaded": False})
        self._write(edits)
        self.logger.bind(tag=TAG).info(f"Portal saved: {', '.join(sorted(k for k in body))}")
        ok = await self.ws_server.reload_local_config()
        if not ok:
            return web.json_response(
                {"error": "Saved, but reloading failed; check the server log", "settings": self._settings()},
                status=500,
            )
        if "barge_in" in body:
            await self._push_blimp_settings()
        return web.json_response({"settings": self._settings(), "reloaded": True})

    async def handle_get_memory(self, request: web.Request):
        if (denied := self._guard(request)) is not None:
            return denied
        entries = [
            {"device": str(device), "summary": summary if isinstance(summary, str) else yaml.safe_dump(summary, allow_unicode=True)}
            for device, summary in self._read_memory().items()
        ]
        return web.json_response({"entries": entries})

    async def handle_delete_memory(self, request: web.Request):
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        device = request.query.get("device")
        memory = self._read_memory()
        if device:
            memory.pop(device, None)
        else:
            memory = {}
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            yaml.dump(memory, f, allow_unicode=True)
        self.logger.bind(tag=TAG).info(f"Portal cleared memory: {device or 'all devices'}")
        return web.json_response({"ok": True})

    # ---------- Blimp control ----------

    @property
    def _control(self):
        return self.ws_server.blimp_control

    async def _on_blimp_connect(self, send):
        """A Blimp connected: send it its settings and the video list."""
        await send(self._settings_message())
        await send(self._videos_message())

    def _settings_message(self) -> dict:
        """Client-side settings; the Blimp applies them the next time it starts listening."""
        return {"type": "settings", "barge_in": bool(self.config.get("barge_in", False))}

    async def _push_blimp_settings(self):
        await self._control.broadcast(self._settings_message())

    async def handle_get_blimp(self, request: web.Request):
        if (denied := self._guard(request)) is not None:
            return denied
        return web.json_response(self._control.snapshot())

    async def handle_blimp_select(self, request: web.Request):
        """Choose which connected Blimp the portal controls: {device_id}."""
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        device_id = (await self._json_body(request)).get("device_id")
        if not isinstance(device_id, str) or not await self._control.select(device_id):
            return web.json_response({"error": "That Blimp is not connected"}, status=409)
        return web.json_response({"ok": True})

    async def handle_blimp_events(self, request: web.Request):
        """Server-sent events: the Blimp snapshot on every change."""
        if (denied := self._guard(request)) is not None:
            return denied
        resp = web.StreamResponse(headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        })
        await resp.prepare(request)
        control = self._control
        seen = control.version
        try:
            await resp.write(f"data: {json.dumps(control.snapshot())}\n\n".encode())
            while True:
                version = await control.wait_change(seen, timeout=15)
                if version == seen:
                    await resp.write(b": keepalive\n\n")
                    continue
                seen = version
                await resp.write(f"data: {json.dumps(control.snapshot())}\n\n".encode())
        except (ConnectionResetError, asyncio.CancelledError):
            pass
        return resp

    async def handle_blimp_stop(self, request: web.Request):
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        if not await self._control.send({"type": "stop_audio"}):
            return web.json_response({"error": "The Blimp is offline"}, status=409)
        return web.json_response({"ok": True})

    async def _state_command(self, request, message: dict, allowed, idle_message: str):
        """Send `message` to the Blimp; a no-op unless allowed(reported state)."""
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        control = self._control
        if not control.online:
            return web.json_response({"error": "The Blimp is offline"}, status=409)
        if not allowed(control.state):
            return web.json_response({"done": False, "message": idle_message})
        # The Blimp checks its state again before acting
        if not await control.send(message):
            return web.json_response({"error": "The Blimp is offline"}, status=409)
        self.logger.bind(tag=TAG).info(f"Portal: {message['type']}")
        return web.json_response({"done": True})

    async def _call_command(self, request, command: str, states: tuple, idle_message: str):
        """Fallback call controls; a no-op unless the Blimp's call is in one of `states`."""
        return await self._state_command(
            request, {"type": command}, lambda s: s.get("call") in states, idle_message
        )

    def _playback_in(self, *statuses):
        return lambda s: (s.get("playback") or {}).get("status") in statuses

    async def handle_blimp_pause(self, request: web.Request):
        return await self._state_command(
            request, {"type": "pause_media"}, self._playback_in("playing"), "Nothing is playing"
        )

    async def handle_blimp_resume(self, request: web.Request):
        return await self._state_command(
            request, {"type": "resume_media"}, self._playback_in("paused"), "Nothing is paused"
        )

    async def handle_blimp_loop(self, request: web.Request):
        """Loop on/off: applies to the current clip and to the next ones."""
        try:
            loop = (await request.json()).get("loop")
        except Exception:
            loop = None
        if not isinstance(loop, bool):
            return web.json_response({"error": "Expected {\"loop\": true|false}"}, status=400)
        return await self._state_command(request, {"type": "set_loop", "loop": loop}, lambda s: True, "")

    async def handle_blimp_answer(self, request: web.Request):
        """Fallback for the spoken "answer"."""
        return await self._call_command(request, "answer_call", ("ringing",), "No call is ringing")

    async def handle_blimp_decline(self, request: web.Request):
        return await self._call_command(request, "decline_call", ("ringing",), "No call is ringing")

    async def handle_blimp_end_call(self, request: web.Request):
        return await self._call_command(request, "end_call", ("calling", "in_call"), "No call to end")

    async def _json_body(self, request: web.Request) -> dict:
        try:
            body = await request.json()
        except Exception:
            return {}
        return body if isinstance(body, dict) else {}

    async def handle_blimp_avatar(self, request: web.Request):
        """Avatar controls, like the client's Debug panel: any of
        {expression: name | "None", blink: true, auto_blink: bool, auto_recover: bool}."""
        body = await self._json_body(request)
        message = {"type": "avatar"}
        if "expression" in body:
            expressions = (self._control.state.get("avatar") or {}).get("expressions") or []
            if body["expression"] not in expressions:
                return web.json_response({"error": "Unknown expression"}, status=400)
            message["expression"] = body["expression"]
        if body.get("blink") is True:
            message["blink"] = True
        for key in ("auto_blink", "auto_recover"):
            if key in body:
                if not isinstance(body[key], bool):
                    return web.json_response({"error": f"{key} must be true or false"}, status=400)
                message[key] = body[key]
        if len(message) == 1:
            return web.json_response({"error": "Nothing to change"}, status=400)
        return await self._state_command(request, message, lambda s: True, "")

    async def handle_blimp_conversation(self, request: web.Request):
        """Conversation controls, like the client's Chat panel:
        {action: connect | disconnect | start | interrupt | send_text, text}. "start" is
        the wake word without saying it."""
        body = await self._json_body(request)
        action = body.get("action")
        message = {"type": "conversation", "action": action}
        if action == "send_text":
            text = body.get("text")
            if not isinstance(text, str) or not text.strip():
                return web.json_response({"error": "Type a message first"}, status=400)
            if len(text) > 1000:
                return web.json_response({"error": "The message is too long (1000 characters at most)"}, status=400)
            message["text"] = text.strip()
        elif action not in ("connect", "disconnect", "start", "interrupt"):
            return web.json_response({"error": "Unknown action"}, status=400)
        # A ringing or active video call owns the Blimp's microphone
        needs_mic = action in ("connect", "start", "send_text")
        return await self._state_command(
            request,
            message,
            lambda s: not (needs_mic and s.get("call") in ("ringing", "calling", "in_call")),
            "The Blimp is in a video call",
        )

    # ---------- media libraries (audio and video) ----------

    def _library(self, request: web.Request):
        return self.libraries.get(request.match_info["kind"])

    def _sign(self, kind: str, clip_id: str, expires: int) -> str:
        key = str(self.config["server"]["auth_key"]).encode()
        return hmac.new(key, f"{kind}/{clip_id}:{expires}".encode(), hashlib.sha256).hexdigest()

    def _blimp_path(self, kind: str, clip_id: str) -> str:
        expires = int(time.time()) + MEDIA_URL_TTL
        return f"/blimp/{kind}/{clip_id}?exp={expires}&sig={self._sign(kind, clip_id, expires)}"

    @property
    def _http_port(self) -> int:
        return int(self.config["server"].get("http_port", 8003))

    def _videos_message(self) -> dict:
        """The video list; each Blimp prefetches what it lacks and drops the rest."""
        videos = [
            {k: e[k] for k in ("id", "title", "mime", "size")} | {"path": self._blimp_path("video", e["id"])}
            for e in self.video.list()
        ]
        return {"type": "videos", "videos": videos, "http_port": self._http_port}

    async def _push_videos(self):
        await self._control.broadcast(self._videos_message())

    async def handle_list_media(self, request: web.Request):
        if (denied := self._guard(request)) is not None:
            return denied
        return web.json_response({"clips": self._library(request).list()})

    async def handle_upload_media(self, request: web.Request):
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        library = self._library(request)
        try:
            reader = await request.multipart()
        except Exception:
            return web.json_response({"error": "Expected a multipart upload"}, status=400)
        added, errors = [], []
        while (part := await reader.next()) is not None:
            if part.name != "file":
                continue
            try:
                added.append(await library.add(part))
            except UploadError as e:
                errors.append(str(e))
        if not added and not errors:
            errors.append("No file uploaded")
        for entry in added:
            self.logger.bind(tag=TAG).info(f"Portal uploaded {library.kind} {entry['id']} ({entry['size']} bytes)")
        if added and library is self.video:
            await self._push_videos()
        body = {"clips": added, "errors": errors}
        if not added:
            return web.json_response({**body, "error": "; ".join(errors)}, status=400)
        return web.json_response(body)

    async def handle_delete_media(self, request: web.Request):
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        library = self._library(request)
        if not library.delete(request.match_info["id"]):
            return web.json_response({"error": "No such clip"}, status=404)
        if library is self.video:
            await self._push_videos()
        return web.json_response({"ok": True})

    async def handle_media_file(self, request: web.Request):
        """The file itself, for previewing in the portal."""
        if (denied := self._guard(request)) is not None:
            return denied
        library = self._library(request)
        entry = library.get(request.match_info["id"])
        if entry is None:
            return web.Response(status=404, text="No such clip")
        return web.FileResponse(library.path(entry), headers={"Content-Type": entry["mime"]})

    async def handle_play_media(self, request: web.Request):
        if (denied := self._guard(request, mutating=True)) is not None:
            return denied
        library = self._library(request)
        entry = library.get(request.match_info["id"])
        if entry is None:
            return web.json_response({"error": "No such clip"}, status=404)
        # Videos play from the Blimp's cache when prefetched; the link is the fallback
        sent = await self._control.send({
            "type": "play",
            "kind": library.kind,
            "id": entry["id"],
            "title": entry["title"],
            "mime": entry["mime"],
            "path": self._blimp_path(library.kind, entry["id"]),
            "http_port": self._http_port,
        })
        if not sent:
            return web.json_response({"error": "The Blimp is offline"}, status=409)
        self.logger.bind(tag=TAG).info(f"Portal: play {library.kind} {entry['id']} on {self._control.device_id}")
        return web.json_response({"ok": True})

    async def handle_blimp_media(self, request: web.Request):
        """A file for the Blimp, authorized by a signed link (play command or video list)."""
        library = self._library(request)
        clip_id = request.match_info["id"]
        try:
            expires = int(request.query.get("exp", "0"))
        except ValueError:
            expires = 0
        sig = request.query.get("sig", "")
        if expires < time.time() or not hmac.compare_digest(sig, self._sign(library.kind, clip_id, expires)):
            return web.Response(status=403, text="Link expired or invalid")
        entry = library.get(clip_id)
        if entry is None:
            return web.Response(status=404, text="No such clip")
        # CORS lets the Blimp page analyse audio (its mouth follows the sound) and
        # fetch videos into its cache; Range requests resume interrupted downloads
        return web.FileResponse(library.path(entry), headers={
            "Content-Type": entry["mime"],
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range",
        })
