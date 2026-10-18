import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.handle.textMessageHandlerRegistry import TextMessageHandlerRegistry

TAG = __name__


class TextMessageProcessor:
    """Main message processor class"""

    def __init__(self, registry: TextMessageHandlerRegistry):
        self.registry = registry

    async def process_message(self, conn: "ConnectionHandler", message: str) -> None:
        """Main entry point for processing messages"""
        try:
            # Parse the JSON message
            msg_json = json.loads(message)

            # Handle the JSON message
            if isinstance(msg_json, dict):
                message_type = msg_json.get("type")

                # Log the message
                conn.logger.bind(tag=TAG).info(f"Received message of type {message_type}: {message}")

                # Get and execute the handler
                handler = self.registry.get_handler(message_type)
                if handler:
                    await handler.handle(conn, msg_json)
                else:
                    conn.logger.bind(tag=TAG).error(f"Received message of unknown type: {message}")
            # Handle a plain numeric message
            elif isinstance(msg_json, int):
                conn.logger.bind(tag=TAG).info(f"Received numeric message: {message}")
                await conn.websocket.send(message)

        except json.JSONDecodeError:
            # Forward non-JSON messages as-is
            conn.logger.bind(tag=TAG).error(f"Failed to parse message: {message}")
            await conn.websocket.send(message)
