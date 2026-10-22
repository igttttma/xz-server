import asyncio
from aiohttp import web
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler
from core.api.portal_handler import PortalHandler

TAG = __name__


class SimpleHttpServer:
    def __init__(self, config: dict, ws_server=None):
        self.config = config
        self.logger = setup_logging()
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config, ws_server)
        self.portal_handler = PortalHandler(config, ws_server) if ws_server else None

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        """Get the websocket address.

        Args:
            local_ip: local IP address
            port: port number

        Returns:
            str: websocket address
        """
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket")

        if websocket_config and "you" not in websocket_config:
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    async def start(self):
        try:
            server_config = self.config["server"]
            read_config_from_api = self.config.get("read_config_from_api", False)
            host = server_config.get("ip", "0.0.0.0")
            port = int(server_config.get("http_port", 8003))

            if port:
                app = web.Application()

                if not read_config_from_api:
                    # If the Control Panel is not enabled and only a single module runs, add the simple OTA endpoints to deliver the websocket address
                    app.add_routes(
                        [
                            web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                            web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                            web.options(
                                "/xiaozhi/ota/", self.ota_handler.handle_options
                            ),
                            # Download endpoint, only serves data/bin/*.bin files
                            web.get(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_download,
                            ),
                            web.options(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_options,
                            ),
                        ]
                    )
                    if self.portal_handler:
                        # Settings portal (edits data/.config.yaml, local-only by default)
                        portal = self.portal_handler
                        app.add_routes(
                            [
                                web.get("/portal", portal.handle_redirect),
                                web.get("/portal/", portal.handle_page),
                                web.get("/portal/api/settings", portal.handle_get_settings),
                                web.post("/portal/api/settings", portal.handle_post_settings),
                                web.get("/portal/api/memory", portal.handle_get_memory),
                                web.delete("/portal/api/memory", portal.handle_delete_memory),
                                web.get("/portal/api/blimp", portal.handle_get_blimp),
                                web.get("/portal/api/blimp/events", portal.handle_blimp_events),
                                web.post("/portal/api/blimp/select", portal.handle_blimp_select),
                                web.post("/portal/api/blimp/stop", portal.handle_blimp_stop),
                                web.post("/portal/api/blimp/pause", portal.handle_blimp_pause),
                                web.post("/portal/api/blimp/resume", portal.handle_blimp_resume),
                                web.post("/portal/api/blimp/loop", portal.handle_blimp_loop),
                                web.post("/portal/api/blimp/answer", portal.handle_blimp_answer),
                                web.post("/portal/api/blimp/decline", portal.handle_blimp_decline),
                                web.post("/portal/api/blimp/end_call", portal.handle_blimp_end_call),
                                web.post("/portal/api/blimp/avatar", portal.handle_blimp_avatar),
                                web.post("/portal/api/blimp/conversation", portal.handle_blimp_conversation),
                                web.get("/portal/api/{kind:audio|video}", portal.handle_list_media),
                                web.post("/portal/api/{kind:audio|video}", portal.handle_upload_media),
                                web.delete("/portal/api/{kind:audio|video}/{id}", portal.handle_delete_media),
                                web.get("/portal/api/{kind:audio|video}/{id}/file", portal.handle_media_file),
                                web.post("/portal/api/{kind:audio|video}/{id}/play", portal.handle_play_media),
                                # Signed links for the Blimp; not behind the portal guard
                                web.get("/blimp/{kind:audio|video}/{id}", portal.handle_blimp_media),
                                web.get("/blimp/greeting/{folder}/{name}", portal.handle_blimp_greeting),
                            ]
                        )
                # Add routes
                app.add_routes(
                    [
                        web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                        web.post(
                            "/mcp/vision/explain", self.vision_handler.handle_post
                        ),
                        web.options(
                            "/mcp/vision/explain", self.vision_handler.handle_options
                        ),
                    ]
                )

                # Run the service
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, host, port)
                await site.start()

                # Keep the service running
                while True:
                    await asyncio.sleep(3600)  # check once per hour
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to start HTTP server: {e}")
            import traceback

            self.logger.bind(tag=TAG).error(f"Error stack: {traceback.format_exc()}")
            raise
