from __future__ import annotations

import time
from typing import Any

from ..cache_clients import make_cohere_client
from ..constants import GenerationStatus
from ..schemas import GenerationResult, ModelSpec
from ..utils import getenv_required, looks_like_refusal, safe_int
from .base import Model


class CohereAdapter(Model):
    def __init__(self, spec: ModelSpec, cfg: dict) -> None:
        super().__init__(spec)

        api_key_env_var = cfg.get("api_key_env_var", "COHERE_API_KEY")
        api_key = getenv_required(api_key_env_var)

        client_kwargs = {
            "api_key": api_key,
        }

        if cfg.get("base_url"):
            client_kwargs["base_url"] = cfg["base_url"]

        if cfg.get("cache_enabled", False):
            client_kwargs["namespace"] = cfg.get("cache_namespace")
            if cfg.get("cache_dir"):
                client_kwargs["cache_dir"] = cfg["cache_dir"]
            if cfg.get("batch_size"):
                client_kwargs["batch_size"] = cfg["batch_size"]

        self.client = make_cohere_client(cfg.get("cache_enabled", False), **client_kwargs)

    def generate(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_output_tokens: int = 256,
        seed: int | None = None,
        reasoning_mode: str | None = None,
        search_enabled: bool = False,
        response_format: str = "json",
        model_params: dict[str, Any] | None = None,
    ) -> GenerationResult:
        start = time.time()
        try:
            kwargs: dict[str, Any] = {
                "model": self.provider_model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_output_tokens,
            }

            if temperature is not None:
                kwargs["temperature"] = temperature

            if seed is not None:
                kwargs["seed"] = seed

            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            # Merge arbitrary user-supplied model params LAST.
            if model_params:
                kwargs.update(model_params)

            resp = self.client.chat(**kwargs)

            # Cohere V2 returns message.content as a list of typed blocks;
            # collect only the text blocks (skip thinking/tool blocks).
            text_parts = []
            message = getattr(resp, "message", None)
            for block in getattr(message, "content", None) or []:
                if getattr(block, "type", None) == "text":
                    text_parts.append(getattr(block, "text", ""))

            text = "\n".join(t for t in text_parts if t).strip() or None

            # Token counts live under usage.tokens (nested), not usage directly.
            usage = getattr(resp, "usage", None)
            tokens = getattr(usage, "tokens", None) if usage else None
            latency_ms = int((time.time() - start) * 1000)

            status = GenerationStatus.SUCCESS
            if text is None:
                status = GenerationStatus.EMPTY
            elif looks_like_refusal(text):
                status = GenerationStatus.REFUSAL

            return GenerationResult(
                raw_response=text,
                status=status,
                input_tokens=safe_int(getattr(tokens, "input_tokens", None)) if tokens else None,
                output_tokens=safe_int(getattr(tokens, "output_tokens", None)) if tokens else None,
                latency_ms=latency_ms,
                provider_details={
                    "id": getattr(resp, "id", None),
                    "finish_reason": getattr(resp, "finish_reason", None),
                },
            )
        except Exception as exc:
            return GenerationResult(
                raw_response=None,
                status=GenerationStatus.ERROR,
                error_message=str(exc),
                latency_ms=int((time.time() - start) * 1000),
            )
