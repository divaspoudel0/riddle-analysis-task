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


def make_together_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    try:
        if use_cache:
            # CacheSaver's Together wrapper builds its own together.AsyncClient(),
            # which reads the API key from the TOGETHER_API_KEY environment
            # variable. It does not accept api_key/base_url, so only the cache
            # parameters are forwarded. The sync wrapper drives the same
            # underlying model as AsyncTogether but is callable from our
            # synchronous adapters.
            from cachesaver.models.together import Together

            wrapper_kwargs = {}
            if kwargs.get("namespace") is not None:
                wrapper_kwargs["namespace"] = kwargs["namespace"]
            if kwargs.get("cachedir") is not None:
                wrapper_kwargs["cachedir"] = kwargs["cachedir"]
            if kwargs.get("batch_size") is not None:
                wrapper_kwargs["batch_size"] = kwargs["batch_size"]
            return Together(**wrapper_kwargs)

        from openai import OpenAI
        kwargs.pop("namespace", None)
        kwargs.pop("cachedir", None)
        kwargs.pop("batch_size", None)

        base_url = kwargs.get("base_url")
        if not base_url:
            raise CacheClientError(
                "Together client requires base_url in non-cached mode."
            )

        return OpenAI(**kwargs)
    except CacheClientError:
        raise
    except Exception as exc:
        raise CacheClientError(f"Failed to build Together client: {exc}") from exc


def make_cohere_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    # Cohere is reached through its OpenAI-compatible endpoint so it can share
    # the OpenAI SDK and CacheSaver's OpenAI wrapper.
    if not kwargs.get("base_url"):
        kwargs["base_url"] = "https://api.cohere.ai/compatibility/v1"
    try:
        if use_cache:
            from cachesaver.models.openai import OpenAI

            # The sync OpenAI wrapper takes namespace/cachedir plus OpenAI client
            # kwargs (api_key/base_url); None cache params would clobber its defaults.
            kwargs.pop("batch_size", None)
            if kwargs.get("namespace") is None:
                kwargs.pop("namespace", None)
            if kwargs.get("cachedir") is None:
                kwargs.pop("cachedir", None)
            return OpenAI(**kwargs)

        from openai import OpenAI
        kwargs.pop("namespace", None)
        kwargs.pop("cachedir", None)
        kwargs.pop("batch_size", None)
        return OpenAI(**kwargs)
    except CacheClientError:
        raise
    except Exception as exc:
        raise CacheClientError(f"Failed to build Cohere client: {exc}") from exc


def make_transformers_client(use_cache: bool, **kwargs):
    kwargs = _apply_common_cache_kwargs(kwargs)
    try:
        if use_cache:
            from cachesaver.models import transformers as cache_transformers

            client_mode = kwargs.pop("client_mode", "sync")
            if client_mode not in {"sync", "async"}:
                raise CacheClientError(
                    "HF Transformers client_mode must be 'sync' or 'async'."
                )

            model_name = kwargs.pop("model_name", None)
            if not model_name:
                raise CacheClientError(
                    "HF Transformers client requires model_name in cached mode."
                )

            kwargs = {
                key: value
                for key, value in kwargs.items()
                if value is not None
            }

            class_name = (
                "AsyncHFTransformers"
                if client_mode == "async"
                else "HFTransformers"
            )
            client_cls = getattr(cache_transformers, class_name, None)
            if client_cls is not None:
                client = client_cls(
                    model_name=model_name,
                    **kwargs,
                )
                try:
                    client._riddles_transformers_client_mode = client_mode
                    client._riddles_transformers_interface = "chat"
                except Exception:
                    pass
                return client

            if client_mode == "sync" and hasattr(cache_transformers, "AutoModelForCausalLM"):
                client = cache_transformers.AutoModelForCausalLM.from_pretrained(
                    model_name,
                    **kwargs,
                )
                try:
                    client._riddles_transformers_client_mode = "sync"
                    client._riddles_transformers_interface = "generate"
                except Exception:
                    pass
                return client

            if client_mode == "async":
                raise CacheClientError(
                    "CacheSaver transformers module does not expose "
                    "AsyncHFTransformers, so local_cache_client_mode='async' "
                    "is not available with this CacheSaver version."
                )

            raise CacheClientError(
                "CacheSaver transformers module exposes neither HFTransformers "
                "nor the sync AutoModelForCausalLM compatibility wrapper."
            )
        else:
            return None
    except CacheClientError:
        raise
    except Exception as exc:
        raise CacheClientError(f"Failed to build HF Transformers client: {exc}") from exc
