from __future__ import annotations

from .exceptions import CacheClientError


def _apply_common_cache_kwargs(kwargs: dict) -> dict:
    cleaned = dict(kwargs)
    if "cache_dir" in cleaned and "cachedir" not in cleaned:
        cleaned["cachedir"] = cleaned.pop("cache_dir")
    return cleaned


def make_openai_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    try:
        if use_cache:
            from cachesaver.models.openai import OpenAI
            return OpenAI(**kwargs)
        else:
            from openai import OpenAI
            kwargs.pop("namespace", None)
            kwargs.pop("cachedir", None)
            kwargs.pop("batch_size", None)
            return OpenAI(**kwargs)
    except Exception as exc:
        raise CacheClientError(f"Failed to build OpenAI client: {exc}") from exc


def make_anthropic_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    try:
        if use_cache:
            from cachesaver.models.anthropic import Anthropic
            return Anthropic(**kwargs)
        else:
            from anthropic import Anthropic
            kwargs.pop("namespace", None)
            kwargs.pop("cachedir", None)
            kwargs.pop("batch_size", None)
            return Anthropic(**kwargs)
    except Exception as exc:
        raise CacheClientError(f"Failed to build Anthropic client: {exc}") from exc


def make_gemini_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    try:
        if use_cache:
            from cachesaver.models.gemini import Gemini
            return Gemini(**kwargs)
        else:
            from google import genai
            kwargs.pop("namespace", None)
            kwargs.pop("cachedir", None)
            kwargs.pop("batch_size", None)
            return genai.Client(**kwargs)
    except Exception as exc:
        raise CacheClientError(f"Failed to build Gemini client: {exc}") from exc


def make_openrouter_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    try:
        if use_cache:
            from cachesaver.models.openrouter import OpenRouter
            return OpenRouter(**kwargs)
        else:
            from openai import OpenAI
            kwargs.pop("namespace", None)
            kwargs.pop("cachedir", None)
            kwargs.pop("batch_size", None)

            base_url = kwargs.get("base_url")
            if not base_url:
                raise CacheClientError(
                    "OpenRouter client requires base_url in non-cached mode."
                )

            return OpenAI(**kwargs)
    except Exception as exc:
        raise CacheClientError(f"Failed to build OpenRouter client: {exc}") from exc


def make_transformers_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    try:
        if use_cache:
            from cachesaver.models.transformers import HFTransformers
            return HFTransformers(**kwargs)
        else:
            return None
    except Exception as exc:
        raise CacheClientError(f"Failed to build HF Transformers client: {exc}") from exc
