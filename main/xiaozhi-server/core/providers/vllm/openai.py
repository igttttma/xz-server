import openai
import json
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.vllm.base import VLLMProviderBase

TAG = __name__
logger = setup_logging()


class VLLMProvider(VLLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        if "base_url" in config:
            self.base_url = config.get("base_url")
        else:
            self.base_url = config.get("url")

        param_defaults = {
            "max_tokens": (300, int),
            "temperature": (0.7, lambda x: round(float(x), 1)),
            "top_p": (1.0, lambda x: round(float(x), 1)),
        }

        for param, (default, converter) in param_defaults.items():
            value = config.get(param)
            try:
                setattr(
                    self,
                    param,
                    converter(value) if value not in (None, "") else default,
                )
            except (ValueError, TypeError):
                setattr(self, param, default)

        model_key_msg = check_model_key("VLLM", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)
        # A photo description is waited on mid-conversation: fail fast instead of
        # the SDK's 10-minute timeout and two retries
        self.timeout = float(config.get("timeout") or 12)
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url,
                                    timeout=self.timeout, max_retries=1)
        # Qwen models on DashScope think by default: 4-6 s per photo instead of 1-2 s
        self.extra_body = {}
        if "dashscope" in str(self.base_url or ""):
            self.extra_body["enable_thinking"] = bool(config.get("enable_thinking", False))

    def response(self, question, base64_image):
        question = question + "(Please reply in English)"
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model_name, messages=messages, stream=False,
                max_tokens=self.max_tokens, extra_body=self.extra_body or None,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response generation: {e}")
            raise
