"""
System prompt manager module.
Manages and updates the system prompt, including fast initialization and async enhancement.
"""

import os
import asyncio
import threading
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from config.logger import setup_logging
from jinja2 import Template
from core.utils.util import get_ip_info

TAG = __name__

WEEKDAY_MAP = {
    "Monday": "Monday",
    "Tuesday": "Tuesday",
    "Wednesday": "Wednesday",
    "Thursday": "Thursday",
    "Friday": "Friday",
    "Saturday": "Saturday",
    "Sunday": "Sunday",
}

EMOJI_List = [
    "😶",
    "🙂",
    "😆",
    "😂",
    "😔",
    "😠",
    "😭",
    "😍",
    "😳",
    "😲",
    "😱",
    "🤔",
    "😉",
    "😎",
    "😌",
    "🤤",
    "😘",
    "😏",
    "😴",
    "😜",
    "🙄",
]


class PromptManager:
    """System prompt manager, responsible for managing and updating the system prompt"""

    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger or setup_logging()
        self.base_prompt_template = None
        self.last_update_time = 0

        # Import the global cache manager
        from core.utils.cache.manager import cache_manager, CacheType

        self.cache_manager = cache_manager
        self.CacheType = CacheType

        # Initialize the context provider
        from core.utils.context_provider import ContextDataProvider

        self.context_provider = ContextDataProvider(config, self.logger)
        self.context_data = {}
        # Per-connection location and pre-fetched weather (see update_context_info)
        self.local_address = ""
        self.weather_location = None
        self.weather_info = ""

        self._load_base_template()

    def _load_base_template(self):
        """Load the base prompt template"""
        try:
            template_path = self.config.get("prompt_template", None)
            if not template_path:
                template_path = "agent-base-prompt.txt"
            cache_key = f"prompt_template:{template_path}"

            # Try the cache first
            cached_template = self.cache_manager.get(self.CacheType.CONFIG, cache_key)
            if cached_template is not None:
                self.base_prompt_template = cached_template
                self.logger.bind(tag=TAG).debug("Loading the base prompt template from cache")
                return

            # Cache miss; read from the file
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    template_content = f.read()

                # Store in the cache (CONFIG entries do not expire automatically; invalidate them manually)
                self.cache_manager.set(
                    self.CacheType.CONFIG, cache_key, template_content
                )
                self.base_prompt_template = template_content
                self.logger.bind(tag=TAG).debug("Base prompt template loaded and cached successfully")
            else:
                self.logger.bind(tag=TAG).warning(f"File not found: {template_path}")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to load the prompt template: {e}")

    def get_quick_prompt(self, user_prompt: str, device_id: str = None) -> str:
        """Get the system prompt quickly (using the user configuration)"""
        device_cache_key = f"device_prompt:{device_id}"
        cached_device_prompt = self.cache_manager.get(
            self.CacheType.DEVICE_PROMPT, device_cache_key
        )
        if cached_device_prompt is not None:
            self.logger.bind(tag=TAG).debug(f"Using the cached prompt for device {device_id}")
            return cached_device_prompt
        else:
            self.logger.bind(tag=TAG).debug(
                f"Device {device_id} has no cached prompt; using the supplied prompt"
            )

        # Use the supplied prompt and cache it (if there is a device ID)
        if device_id:
            device_cache_key = f"device_prompt:{device_id}"
            self.cache_manager.set(self.CacheType.DEVICE_PROMPT, device_cache_key, user_prompt)
            self.logger.bind(tag=TAG).debug(f"Prompt for device {device_id} cached")

        self.logger.bind(tag=TAG).info(f"Using quick prompt: {user_prompt[:50]}...")
        return user_prompt

    def _get_current_time_info(self) -> tuple:
        """Get the current time information"""
        from .current_time import (
            get_current_date,
            get_current_weekday,
            get_current_lunar_date,
        )

        today_date = get_current_date()
        today_weekday = get_current_weekday()
        lunar_date = get_current_lunar_date() + "\n"

        return today_date, today_weekday, lunar_date

    def update_context_info(self, conn, client_ip: str):
        """Resolve the user's location from the client IP and pre-fetch its weather
        (blocking; runs in the connection's worker thread before the first LLM call)."""
        template = self.base_prompt_template or ""
        try:
            if "local_address" in template or "weather_info" in template:
                info = get_ip_info(client_ip or "", self.logger, self.config.get("test_client_ip"))
                self.local_address = ", ".join(
                    part for part in (info.get("city"), info.get("region"), info.get("country")) if part
                )
                if info.get("lat") and info.get("lon"):
                    # QWeather takes "lon,lat" and returns the nearest city
                    self.weather_location = f"{float(info['lon']):.2f},{float(info['lat']):.2f}"
                else:
                    self.weather_location = info.get("city") or None

            if "weather_info" in template:
                self.weather_info = self._prefetch_weather(conn)

            # Get the configured context data
            if hasattr(conn, "device_id") and conn.device_id:
                if "dynamic_context" in template:
                    self.context_data = self.context_provider.fetch_all(conn.device_id)
                else:
                    self.context_data = ""

            self.logger.bind(tag=TAG).info(
                f"Context: location '{self.local_address or 'unknown'}', weather "
                f"{'pre-fetched' if self.weather_info and not self.weather_info.startswith('Unavailable') else 'unavailable'}"
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to update context information: {e}")

    def _prefetch_weather(self, conn) -> str:
        from plugins_func.functions.get_weather import fetch_weather_report, WeatherUnavailable

        weather_config = self.config.get("plugins", {}).get("get_weather", {})
        location = self.weather_location or weather_config.get("default_location", "")
        try:
            # This runs in a worker thread, so a private event loop is fine here
            return asyncio.run(fetch_weather_report(weather_config, location))
        except WeatherUnavailable as e:
            return f"Unavailable ({e}) Call get_weather if the user asks about the weather."
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Weather pre-fetch failed: {e}")
            return "Unavailable. Call get_weather if the user asks about the weather."

    def build_enhanced_prompt(
        self, user_prompt: str, device_id: str, client_ip: str = None, *args, **kwargs
    ) -> str:
        """Build the enhanced system prompt"""
        if not self.base_prompt_template:
            return user_prompt

        try:
            # Get the latest time information (not cached)
            today_date, today_weekday, lunar_date = self._get_current_time_info()

            # Resolved by update_context_info for this connection
            local_address = self.local_address or "unknown"
            weather_info = self.weather_info or "Unavailable. Call get_weather if the user asks about the weather."

            # Get the language selected by TTS, defaulting to English
            language = (
                self.config.get("TTS", {})
                .get(self.config.get("selected_module", {}).get("TTS", ""), {})
                .get("language")
                or "English"
            )
            self.logger.bind(tag=TAG).debug(f"Selected language: {language}")

            # Substitute the template variables
            template = Template(self.base_prompt_template)
            enhanced_prompt = template.render(
                base_prompt=user_prompt,
                current_time="{{current_time}}",
                today_date=today_date,
                today_weekday=today_weekday,
                lunar_date=lunar_date,
                local_address=local_address,
                weather_info=weather_info,
                emojiList=EMOJI_List,
                device_id=device_id,
                client_ip=client_ip,
                dynamic_context=self.context_data,
                language=language,
                *args,
                **kwargs,
            )
            device_cache_key = f"device_prompt:{device_id}"
            self.cache_manager.set(
                self.CacheType.DEVICE_PROMPT, device_cache_key, enhanced_prompt
            )
            self.logger.bind(tag=TAG).info(
                f"Enhanced prompt built successfully, length: {len(enhanced_prompt)}"
            )
            return enhanced_prompt

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to build the enhanced prompt: {e}")
            return user_prompt
