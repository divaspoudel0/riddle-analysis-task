from __future__ import annotations

import time
from typing import Any

from ..cache_clients import make_transformers_client
from ..constants import GenerationStatus
from ..schemas import GenerationResult, ModelSpec
from ..utils import looks_like_refusal
from .base import Model


class LocalTransformersAdapter(Model):
    def __init__(self, spec: ModelSpec, cfg: dict) -> None:
        super().__init__(spec)
        self.use_cache = cfg.get("cache_enabled", False)

        if self.use_cache:
            self.client = make_transformers_client(
                True,
                model_name=self.provider_model_name,
                namespace=cfg.get("cache_namespace"),
                cache_dir=cfg.get("cache_dir"),
                batch_size=cfg.get("batch_size", 1),
            )
            self.pipeline = None
        else:
            from transformers import pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.provider_model_name,
            )
            self.client = None

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
            if self.client is not None:
                resp = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    max_new_tokens=max_output_tokens,
                )
                # CacheSaver transformers interface may differ by version; team can refine.
                text = str(resp)
            else:
                pipe_kwargs: dict[str, Any] = {
                    "max_new_tokens": max_output_tokens,
                    "return_full_text": False,
                }
                if temperature is not None:
                    pipe_kwargs["temperature"] = temperature
                    pipe_kwargs["do_sample"] = temperature > 0.0
                else:
                    # Greedy decoding by default; no sampling.
                    pipe_kwargs["do_sample"] = False

                if model_params:
                    pipe_kwargs.update(model_params)

                outputs = self.pipeline(prompt, **pipe_kwargs)
                text = outputs[0]["generated_text"] if outputs else None

            latency_ms = int((time.time() - start) * 1000)

            status = GenerationStatus.SUCCESS
            if text is None or str(text).strip() == "":
                status = GenerationStatus.EMPTY
            elif looks_like_refusal(text):
                status = GenerationStatus.REFUSAL

            return GenerationResult(
                raw_response=text,
                status=status,
                latency_ms=latency_ms,
                provider_details={"model": self.provider_model_name},
            )
        except Exception as exc:
            return GenerationResult(
                raw_response=None,
                status=GenerationStatus.ERROR,
                error_message=str(exc),
                latency_ms=int((time.time() - start) * 1000),
            )
