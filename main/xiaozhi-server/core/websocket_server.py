import asyncio
import logging

import websockets
from urllib.parse import urlparse
from config.logger import setup_logging


class SuppressInvalidHandshakeFilter(logging.Filter):
    """Filter out invalid handshake error logs (e.g. HTTPS requests to the WS port)"""

    def filter(self, record):
        msg = record.getMessage()
        suppress_keywords = [
            "opening handshake failed",
            "did not receive a valid HTTP request",
            "connection closed while reading HTTP request",
            "line without CRLF",
        ]
        return not any(keyword in msg for keyword in suppress_keywords)


def _setup_websockets_logger():
    """Configure all websockets-related loggers to filter invalid handshake errors"""
    filter_instance = SuppressInvalidHandshakeFilter()
    for logger_name in ["websockets", "websockets.server", "websockets.client"]:
        logger = logging.getLogger(logger_name)
        logger.addFilter(filter_instance)


_setup_websockets_logger()


from core.connection import ConnectionHandler
from config.config_loader import get_config_from_api_async
from core.auth import AuthManager, AuthenticationError
from core.blimp_control import BlimpControl
from core.utils.modules_initialize import initialize_modules
from core.utils.util import check_vad_update, check_asr_update

TAG = __name__


class WebSocketServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging(config)
        self.config_lock = asyncio.Lock()
        # device-id -> live ConnectionHandler (used to attach photos to a conversation)
        self.active_connections = {}
        # The Blimp's always-on control socket (online status, portal commands)
        self.blimp_control = BlimpControl(config)
        modules = initialize_modules(
            self.logger,
            self.config,
            "VAD" in self.config["selected_module"],
            "ASR" in self.config["selected_module"],
            "LLM" in self.config["selected_module"],
            False,
            "Memory" in self.config["selected_module"],
            "Intent" in self.config["selected_module"],
        )
        self._vad = modules["vad"] if "vad" in modules else None
        self._asr = modules["asr"] if "asr" in modules else None
        self._llm = modules["llm"] if "llm" in modules else None
        self._intent = modules["intent"] if "intent" in modules else None
        self._memory = modules["memory"] if "memory" in modules else None

        auth_config = self.config["server"].get("auth", {})
        self.auth_enable = auth_config.get("enabled", False)
        # Device whitelist
        self.allowed_devices = set(auth_config.get("allowed_devices", []))
        secret_key = self.config["server"]["auth_key"]
        expire_seconds = auth_config.get("expire_seconds", None)
        self.auth = AuthManager(secret_key=secret_key, expire_seconds=expire_seconds)

    async def start(self):
        server_config = self.config["server"]
        host = server_config.get("ip", "0.0.0.0")
        port = int(server_config.get("port", 8000))

        async with websockets.serve(
            self._handle_connection,
            host,
            port,
            process_request=self._http_response,
            ping_interval=None,
        ):
            await asyncio.Future()

    async def _handle_connection(self, websocket: websockets.ServerConnection):
        headers = dict(websocket.request.headers)
        if headers.get("device-id", None) is None:
            # Try to obtain device-id from the URL query parameters
            from urllib.parse import parse_qs

            # Get the path from the WebSocket request
            request_path = websocket.request.path
            if not request_path:
                self.logger.bind(tag=TAG).error("Unable to get request path")
                await websocket.close()
                return
            parsed_url = urlparse(request_path)
            query_params = parse_qs(parsed_url.query)
            if "device-id" not in query_params:
                await websocket.send("Port is up. To test the connection, start the digital human test")
                await websocket.close()
                return
            else:
                websocket.request.headers["device-id"] = query_params["device-id"][0]
            if "client-id" in query_params:
                websocket.request.headers["client-id"] = query_params["client-id"][0]
            if "authorization" in query_params:
                websocket.request.headers["authorization"] = query_params[
                    "authorization"
                ][0]

        """Handle a new connection, creating an independent ConnectionHandler each time"""
        # Authenticate first, then establish the connection
        try:
            await self._handle_auth(websocket)
        except AuthenticationError:
            await websocket.send("Authentication failed")
            await websocket.close()
            return
        device_id = websocket.request.headers.get("device-id")
        if urlparse(websocket.request.path).path.rstrip("/").endswith("/control"):
            await self.blimp_control.handle(websocket, device_id)
            return
        # Pass the current server instance when creating the ConnectionHandler
        handler = ConnectionHandler(
            self.config,
            self._vad,
            self._asr,
            self._llm,
            self._memory,
            self._intent,
            self,  # pass in the server instance
        )
        self.active_connections[device_id] = handler
        try:
            await handler.handle_connection(websocket)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error while handling connection: {e}")
        finally:
            if self.active_connections.get(device_id) is handler:
                del self.active_connections[device_id]
            # Force close the connection (if not already closed)
            try:
                # Safely check the WebSocket state and close it
                if hasattr(websocket, "closed") and not websocket.closed:
                    await websocket.close()
                elif hasattr(websocket, "state") and websocket.state.name != "CLOSED":
                    await websocket.close()
                else:
                    # If there is no closed attribute, just try to close
                    await websocket.close()
            except Exception as close_error:
                self.logger.bind(tag=TAG).error(
                    f"Error while force-closing the connection on the server side: {close_error}"
                )

    async def _http_response(self, websocket, request_headers):
        # Check whether this is a WebSocket upgrade request
        if request_headers.headers.get("connection", "").lower() == "upgrade":
            # For a WebSocket request, return None to let the handshake continue
            return None
        else:
            # For a plain HTTP request, return "server is running"
            return websocket.respond(200, "Server is running\n")

    async def update_config(self) -> bool:
        """Update the server configuration and re-initialize the components.

        Returns:
            bool: whether the update succeeded
        """
        try:
            async with self.config_lock:
                # Re-fetch the configuration (async version)
                new_config = await get_config_from_api_async(self.config)
                if new_config is None:
                    self.logger.bind(tag=TAG).error("Failed to fetch the new configuration")
                    return False
                self.logger.bind(tag=TAG).info(f"Fetched the new configuration successfully")
                # Check whether the VAD and ASR types need to be updated
                update_vad = check_vad_update(self.config, new_config)
                update_asr = check_asr_update(self.config, new_config)
                self.logger.bind(tag=TAG).info(
                    f"Checking whether the VAD and ASR types need updating: {update_vad} {update_asr}"
                )
                # Update the configuration
                self.config = new_config
                # Re-initialize the components
                modules = initialize_modules(
                    self.logger,
                    new_config,
                    update_vad,
                    update_asr,
                    "LLM" in new_config["selected_module"],
                    False,
                    "Memory" in new_config["selected_module"],
                    "Intent" in new_config["selected_module"],
                )

                # Update the component instances
                if "vad" in modules:
                    self._vad = modules["vad"]
                if "asr" in modules:
                    self._asr = modules["asr"]
                if "llm" in modules:
                    self._llm = modules["llm"]
                if "intent" in modules:
                    self._intent = modules["intent"]
                if "memory" in modules:
                    self._memory = modules["memory"]
                self.logger.bind(tag=TAG).info(f"Configuration update task finished")
                return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to update the server configuration: {str(e)}")
            return False

    async def reload_local_config(self) -> bool:
        """Re-read config.yaml + data/.config.yaml (standalone mode) and re-initialize
        the shared modules whose config changed. Applies to new connections.
        """
        from config.config_loader import load_config
        from core.utils.cache.manager import cache_manager, CacheType

        try:
            async with self.config_lock:
                cache_manager.delete(CacheType.CONFIG, "main_config")
                new_config = await load_config()
                # Keep the runtime auth key generated at startup
                new_config["server"]["auth_key"] = self.config["server"]["auth_key"]

                def changed(module):
                    old_sel = self.config["selected_module"].get(module)
                    new_sel = new_config["selected_module"].get(module)
                    return old_sel != new_sel or self.config.get(module, {}).get(
                        old_sel
                    ) != new_config.get(module, {}).get(new_sel)

                modules = initialize_modules(
                    self.logger,
                    new_config,
                    False,
                    "ASR" in new_config["selected_module"] and changed("ASR"),
                    "LLM" in new_config["selected_module"],
                    False,
                    "Memory" in new_config["selected_module"],
                    "Intent" in new_config["selected_module"],
                )
                if "asr" in modules:
                    self._asr = modules["asr"]
                if "llm" in modules:
                    self._llm = modules["llm"]
                if "intent" in modules:
                    self._intent = modules["intent"]
                if "memory" in modules:
                    self._memory = modules["memory"]
                # Update in place: the HTTP handlers share this dict
                self.config.clear()
                self.config.update(new_config)
                self.logger.bind(tag=TAG).info("Local configuration reloaded")
                return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to reload the local configuration: {str(e)}")
            return False

    async def _handle_auth(self, websocket: websockets.ServerConnection):
        # Authenticate first, then establish the connection
        if self.auth_enable:
            headers = dict(websocket.request.headers)
            device_id = headers.get("device-id", None)
            client_id = headers.get("client-id", None)
            if self.allowed_devices and device_id in self.allowed_devices:
                # Devices on the whitelist skip token verification
                return
            else:
                # Otherwise verify the token
                token = headers.get("authorization", "")
                if token.startswith("Bearer "):
                    token = token[7:]  # remove the 'Bearer ' prefix
                else:
                    raise AuthenticationError("Missing or invalid Authorization header")
                # Perform authentication
                auth_success = self.auth.verify_token(
                    token, client_id=client_id, username=device_id
                )
                if not auth_success:
                    raise AuthenticationError("Invalid token")
