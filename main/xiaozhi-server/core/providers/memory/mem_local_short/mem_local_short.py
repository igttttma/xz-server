from ..base import MemoryProviderBase, logger
import time
import json
import os
import yaml
from config.config_loader import get_project_dir
from config.manage_api_client import generate_and_save_chat_summary
import asyncio
from core.utils.util import check_model_key


short_term_memory_prompt = """
# Spatiotemporal Memory Weaver

## Core mission
Build a growable dynamic memory network that retains key information within limited space while intelligently maintaining the evolution trail of information.
Based on the conversation records, summarize important information about the user so as to provide more personalized service in future conversations.

## Memory rules
### 1. Three-dimensional memory assessment (perform on every update)
| Dimension  | Assessment criteria                       | Weight |
|------------|-------------------------------------------|--------|
| Timeliness | Information freshness (by conversation turn) | 40%    |
| Emotional intensity | 💖 markers / number of repeated mentions | 35%    |
| Association density | Number of connections to other information | 25%    |

### 2. Dynamic update mechanism
**Example of handling a name change:**
Original memory: "former_names": ["John"], "current_name": "John Smith"
Trigger condition: when naming signals such as "my name is X" or "call me Y" are detected
Procedure:
1. Move the old name into the "former_names" list
2. Record the naming timeline: "2024-02-15 14:32: enabled John Smith"
3. Append to the memory cube: "identity transformation from John to John Smith"

### 3. Space optimization strategy
- **Information compression**: use a symbolic system to increase density
  - ✅"John Smith[Beijing/SE/🐱]"
  - ❌"software engineer in Beijing, owns a cat"
- **Eviction warning**: triggered when the total character count is >= 900
  1. Delete information with a weight score < 60 that has not been mentioned in 3 turns
  2. Merge similar entries (keeping the most recent timestamp)

## Memory structure
The output format must be a parseable JSON string with no explanation, comments, or notes. When saving memory, extract information only from the conversation and do not mix in sample content.
```json
{
  "spatiotemporal_profile": {
    "identity_map": {
      "current_name": "",
      "trait_tags": []
    },
    "memory_cube": [
      {
        "event": "joined a new company",
        "timestamp": "2024-03-20",
        "emotion_score": 0.9,
        "related_items": ["afternoon tea"],
        "retention_days": 30
      }
    ]
  },
  "relationship_network": {
    "frequent_topics": {"workplace": 12},
    "hidden_connections": [""]
  },
  "pending_responses": {
    "urgent_items": ["tasks that need immediate handling"],
    "potential_care": ["help that can be offered proactively"]
  },
  "highlight_quotes": [
    "the most touching moment, a strong emotional expression, the user's exact words"
  ]
}
```
"""


def extract_json_data(json_code):
    start = json_code.find("```json")
    # Starting from start, find the next ``` as the end
    end = json_code.find("```", start + 1)
    # print("start:", start, "end:", end)
    if start == -1 or end == -1:
        try:
            jsonData = json.loads(json_code)
            return json_code
        except Exception as e:
            print("Error:", e)
        return ""
    jsonData = json_code[start + 7 : end]
    return jsonData


TAG = __name__


class MemoryProvider(MemoryProviderBase):
    def __init__(self, config, summary_memory):
        super().__init__(config)
        self.short_memory = ""
        self.save_to_file = True
        self.memory_path = get_project_dir() + "data/.memory.yaml"
        self.load_memory(summary_memory)

    def init_memory(
        self, role_id, llm, summary_memory=None, save_to_file=True, **kwargs
    ):
        super().init_memory(role_id, llm, **kwargs)
        self.save_to_file = save_to_file
        self.load_memory(summary_memory)

    def load_memory(self, summary_memory):
        # Return directly after obtaining the summarized memory from the API
        if summary_memory or not self.save_to_file:
            self.short_memory = summary_memory
            return

        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        if self.role_id in all_memory:
            self.short_memory = all_memory[self.role_id]

    def save_memory_to_file(self):
        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        all_memory[self.role_id] = self.short_memory
        with open(self.memory_path, "w", encoding="utf-8") as f:
            yaml.dump(all_memory, f, allow_unicode=True)

    async def save_memory(self, msgs, session_id=None):
        # Log the model information in use
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"Memory save model: {model_info}")
        api_key = getattr(self.llm, "api_key", None)
        memory_key_msg = check_model_key("memory summarization LLM", api_key)
        if memory_key_msg:
            logger.bind(tag=TAG).error(memory_key_msg)
        if self.llm is None:
            logger.bind(tag=TAG).error("LLM is not set for memory provider")
            return None

        if len(msgs) < 2:
            return None

        msgStr = ""
        for msg in msgs:
            content = msg.content

            # Extract content from JSON format if present (for ASR with emotion/language tags)
            try:
                if content and content.strip().startswith("{") and content.strip().endswith("}"):
                    data = json.loads(content)
                    if "content" in data:
                        content = data["content"]
            except (json.JSONDecodeError, KeyError, TypeError):
                # If parsing fails, use original content
                pass

            if msg.role == "user":
                msgStr += f"User: {content}\n"
            elif msg.role == "assistant":
                msgStr += f"Assistant: {content}\n"
        if self.short_memory and len(self.short_memory) > 0:
            msgStr += "Historical memory:\n"
            msgStr += self.short_memory

        # Current time
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msgStr += f"Current time: {time_str}"

        if self.save_to_file:
            try:
                result = self.llm.response_no_stream(
                    short_term_memory_prompt,
                    msgStr,
                    max_tokens=2000,
                    temperature=0.2,
                )
                json_str = extract_json_data(result)
                json.loads(json_str)  # Check whether the JSON format is valid
                self.short_memory = json_str
                self.save_memory_to_file()
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error in saving memory: {e}")
        else:
            # When save_to_file is False, call the Java-side chat summary API
            summary_id = session_id if session_id else self.role_id
            await generate_and_save_chat_summary(summary_id)
        logger.bind(tag=TAG).info(
            f"Save memory successful - Role: {self.role_id}, Session: {session_id}"
        )

        return self.short_memory

    async def query_memory(self, query: str) -> str:
        return self.short_memory
