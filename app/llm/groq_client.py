from __future__ import annotations

import os
from typing import Any

import headroom
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class GroqClient:

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

        self.client = Groq(api_key=api_key)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> Any:

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        # =========================================================
        # HEADROOM
        # =========================================================

        compression = headroom.compress(
            messages,
            model=self.model,
            optimize=True,
        )

        optimized_messages = compression.messages

        # =========================================================
        # GROQ REQUEST
        # =========================================================

        request = {
            "model": self.model,
            "temperature": 0,
            "messages": optimized_messages,
        }

        if json_mode:
            request["response_format"] = {
                "type": "json_object"
            }

        response = self.client.chat.completions.create(
            **request
        )

        # =========================================================
        # TOKEN METRICS
        # =========================================================

        usage = getattr(response, "usage", None)

        input_tokens = getattr(
            usage,
            "prompt_tokens",
            0,
        ) if usage else 0

        output_tokens = getattr(
            usage,
            "completion_tokens",
            0,
        ) if usage else 0

        total_tokens = getattr(
            usage,
            "total_tokens",
            input_tokens + output_tokens,
        ) if usage else input_tokens + output_tokens

        # Attach our metrics to the response object.
        response._okf_metrics = {
            "headroom": {
                "tokens_before": compression.tokens_before,
                "tokens_after": compression.tokens_after,
                "tokens_saved": compression.tokens_saved,
                "compression_ratio": compression.compression_ratio,
                "transforms_applied": compression.transforms_applied,
            },
            "groq": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
        }

        return response