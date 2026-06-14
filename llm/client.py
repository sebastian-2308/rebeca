from __future__ import annotations

import json
import os
from typing import Generator

from ..config import Config


class LLMClient:
    def __init__(self, config: Config):
        self.config = config
        self._client = self._build_client()

    def _build_client(self):
        provider = self.config.provider.lower()
        if provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=self.config.api_key or os.getenv("OPENAI_API_KEY", ""))
        elif provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=self.config.api_key or os.getenv("ANTHROPIC_API_KEY", ""))
        elif provider == "deepseek":
            from openai import OpenAI
            return OpenAI(
                api_key=self.config.api_key or os.getenv("DEEPSEEK_API_KEY", ""),
                base_url=os.getenv("REBECA_BASE_URL", os.getenv("GACE_BASE_URL", "https://api.deepseek.com")),
            )
        else:
            from openai import OpenAI
            base_url = os.getenv("REBECA_BASE_URL", os.getenv("GACE_BASE_URL", "http://localhost:11434/v1"))
            return OpenAI(
                api_key=self.config.api_key or "ollama",
                base_url=base_url,
            )

    def send_message(self, messages: list[dict]) -> str:
        model = self.config.model
        provider = self.config.provider.lower()

        if provider == "anthropic":
            return self._send_anthropic(messages, model)
        else:
            return self._send_openai(messages, model)

    def send_message_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        model = self.config.model
        provider = self.config.provider.lower()

        if provider == "anthropic":
            yield from self._send_anthropic_stream(messages, model)
        else:
            yield from self._send_openai_stream(messages, model)

    def _send_openai(self, messages: list[dict], model: str) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    def _send_openai_stream(self, messages: list[dict], model: str) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": False},
            max_tokens=4096,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    def _send_anthropic(self, messages: list[dict], model: str) -> str:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system += m["content"] + "\n"
            else:
                filtered.append(m)

        kwargs = {"system": system.strip()} if system else {}

        response = self._client.messages.create(
            model=model,
            max_tokens=4096,
            messages=filtered,
            **kwargs,
        )
        return response.content[0].text

    def _send_anthropic_stream(self, messages: list[dict], model: str) -> Generator[str, None, None]:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system += m["content"] + "\n"
            else:
                filtered.append(m)

        kwargs = {"system": system.strip()} if system else {}

        with self._client.messages.stream(
            model=model,
            max_tokens=4096,
            messages=filtered,
            **kwargs,
        ) as stream:
            for text in stream.text_stream:
                yield text
