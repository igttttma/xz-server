from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

handle_exit_intent_function_desc = {
    "type": "function",
    "function": {
        "name": "handle_exit_intent",
        "description": (
            "End the conversation. Call this when the user says goodbye (bye, see you, good night, "
            "that's all, thanks that's it) or asks to stop talking. The device then waits for its wake word."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "say_goodbye": {
                    "type": "string",
                    "description": "One short, friendly farewell sentence, e.g. \"Bye, talk soon!\"",
                }
            },
            "required": ["say_goodbye"],
        },
    },
}


@register_function(
    "handle_exit_intent", handle_exit_intent_function_desc, ToolType.SYSTEM_CTL
)
def handle_exit_intent(conn: "ConnectionHandler", say_goodbye: str | None = None):
    # Handle the exit intent
    try:
        if say_goodbye is None:
            say_goodbye = "Goodbye, have a great day!"
        # End the conversation after the farewell; the connection stays for the next wake
        conn.end_session_after_chat = True
        logger.bind(tag=TAG).info(f"Exit intent handled: {say_goodbye}")
        return ActionResponse(
            action=Action.RESPONSE, result="Exit intent handled", response=say_goodbye
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"Error handling exit intent: {e}")
        return ActionResponse(
            action=Action.NONE, result="Failed to handle exit intent", response=""
        )
