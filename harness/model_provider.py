from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

import httpx


@dataclass
class ModelResponse:
    content: str = ""
    finish_reason: str = "stop"
    model_used: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


class ModelProvider(BaseModel):
    model: str = "google/gemini-2.0-flash-001"
    temperature: float = 0.7
    max_tokens: int = 4096
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_seconds: int = 120

    def _headers(self) -> Dict[str, str]:
        import os
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY env var not set")
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://harness.local",
            "X-Title": "Harness Pipeline",
        }

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> ModelResponse:
        body = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=body)
            resp.raise_for_status()
            data = resp.json()
        choice = data["choices"][0]
        return ModelResponse(
            content=choice["message"].get("content", ""),
            finish_reason=choice.get("finish_reason", "stop"),
            model_used=data.get("model", self.model),
            usage=data.get("usage", {}),
        )
