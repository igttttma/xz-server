import json
import httpx
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# Define the base function description template
SEARCH_FROM_RAGFLOW_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "search_from_ragflow",
        "description": "Query information from the knowledge base",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "The question to query"}},
            "required": ["question"],
        },
    },
}


@register_function(
    "search_from_ragflow", SEARCH_FROM_RAGFLOW_FUNCTION_DESC, ToolType.SYSTEM_CTL
)
async def search_from_ragflow(conn: "ConnectionHandler", question=None):
    # Ensure string arguments are encoded correctly
    if question and isinstance(question, str):
        # Ensure the question argument is a UTF-8 encoded string
        pass
    else:
        question = str(question) if question is not None else ""

    ragflow_config = conn.config.get("plugins", {}).get("search_from_ragflow", {})
    base_url = ragflow_config.get("base_url", "")
    api_key = ragflow_config.get("api_key", "")
    dataset_ids = ragflow_config.get("dataset_ids", [])

    url = base_url + "/api/v1/retrieval"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Ensure all strings in the payload are UTF-8 encoded
    payload = {"question": question, "dataset_ids": dataset_ids}

    try:
        # Use ensure_ascii=False to handle non-ASCII text correctly during JSON serialization
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0), verify=False) as client:
            response = await client.post(url, json=payload, headers=headers)

        # Explicitly set the response encoding to utf-8
        response.encoding = "utf-8"

        response.raise_for_status()

        # Get the text content first, then handle the JSON decoding manually
        response_text = response.text

        result = json.loads(response_text)

        if result.get("code") != 0:
            error_detail = result.get("error", {}).get("detail", "unknown error")
            error_message = result.get("error", {}).get("message", "")
            error_code = result.get("code", "")

            # Log the error information safely
            logger.bind(tag=TAG).error(
                f"RAGFlow API call failed, response code: {error_code}, error detail: {error_detail}, full response: {result}"
            )

            # Build a detailed error response
            error_response = f"The RAG API returned an error (error code: {error_code})"

            if error_message:
                error_response += f": {error_message}"
            if error_detail:
                error_response += f"\nDetail: {error_detail}"

            return ActionResponse(Action.RESPONSE, None, error_response)

        chunks = result.get("data", {}).get("chunks", [])
        contents = []
        for chunk in chunks:
            content = chunk.get("content", "")
            if content:
                # Safely handle the content string
                if isinstance(content, str):
                    contents.append(content)
                elif isinstance(content, bytes):
                    contents.append(content.decode("utf-8", errors="replace"))
                else:
                    contents.append(str(content))

        if contents:
            # Organize the knowledge base content in citation mode
            context_text = f"# The knowledge base returned the following for the question [{question}]\n"
            context_text += "```\n\n\n".join(contents[:5])
            context_text += "\n```"
        else:
            context_text = "No relevant information was found in the knowledge base."
        return ActionResponse(Action.REQLLM, context_text, None)

    except httpx.TimeoutException as e:
        error_response = "The RAG API request timed out"
        error_response += "\nPossible reason: the RAGflow service is responding slowly or there is network latency"
        error_response += "\nSolution: please try again later or check the RAGflow service performance"
        return ActionResponse(Action.RESPONSE, None, error_response)

    except httpx.HTTPStatusError as e:
        if hasattr(e.response, "status_code"):
            status_code = e.response.status_code
            error_response = f"RAG API HTTP error (status code: {status_code})"
            try:
                error_detail = e.response.json().get("error", {}).get("message", "")
                if error_detail:
                    error_response += f"\nError detail: {error_detail}"
            except:
                pass
        else:
            error_response = f"RAG API HTTP exception: {str(e)}"
        return ActionResponse(Action.RESPONSE, None, error_response)

    except httpx.HTTPError as e:
        error_response = "Unable to connect to the RAG API"
        error_response += "\nPossible reason: the RAGflow service address is wrong or the service is not running"
        error_response += "\nSolution: please check the RAGflow service address config and service status"
        return ActionResponse(Action.RESPONSE, None, error_response)

    except Exception as e:
        # Other exceptions
        error_type = type(e).__name__
        logger.bind(tag=TAG).error(
            f"RAGflow processing exception, exception type: {error_type}, detail: {str(e)}"
        )

        # Provide detailed error information
        error_response = f"RAG API processing exception ({error_type}): {str(e)}"
        return ActionResponse(Action.RESPONSE, None, error_response)
