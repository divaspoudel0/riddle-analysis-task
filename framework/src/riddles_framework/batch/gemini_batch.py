"""Gemini Batch backend (CacheSaver-compatible).

The cache entry is a google ``GenerateContentResponse`` keyed by
``gemini_request_key({"model": ..., "contents": prompt})`` (matches the online
Gemini path, confirmed against a real run's cache).

Validated live end-to-end against **google-genai 2.8.0** (inline ``src``
requests, ``JOB_STATE_*`` polling, ``dest.inlined_responses``). That SDK's batch
surface changes between versions — if you upgrade ``google-genai``, re-check
``batches.create`` and the ``dest.inlined_responses`` unwrapping here. Results
are matched to keys by submission order.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from .cache_compat import cache_lookup, cache_store, gemini_request_key


@dataclass
class BatchPlan:
    keys: list[str]          # cache key per miss, in submission order
    prompts: list[str]       # the miss prompts, same order
    hit_count: int


def build_batch_plan(*, prompts: list[str], model: str, cache_dir: str) -> BatchPlan:
    keys: list[str] = []
    miss_prompts: list[str] = []
    hits = 0
    seen: set[str] = set()
    for p in prompts:
        key = gemini_request_key({"model": model, "contents": p})
        if key in seen:
            continue
        seen.add(key)
        if cache_lookup(cache_dir, key):
            hits += 1
            continue
        keys.append(key)
        miss_prompts.append(p)
    return BatchPlan(keys=keys, prompts=miss_prompts, hit_count=hits)


def writeback_responses(cache_dir: str, keys: list[str], responses) -> tuple[int, int]:
    """Store one ``GenerateContentResponse`` per key (same order). -> (ok, err)."""
    ok = err = 0
    for key, resp in zip(keys, responses):
        try:
            cache_store(cache_dir, key, resp)
            ok += 1
        except Exception:
            err += 1
    return ok, err


def run_gemini_batch(
    *,
    prompts: list[str],
    model: str,
    cache_dir: str,
    api_key: str,
    poll_seconds: int = 30,
    max_wait_seconds: int | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    from google import genai

    plan = build_batch_plan(prompts=prompts, model=model, cache_dir=cache_dir)
    log(f"[gemini-batch] {plan.hit_count} cached, {len(plan.prompts)} to submit")
    if not plan.prompts:
        return {"submitted": 0, "cached": plan.hit_count, "written": 0}

    client = genai.Client(api_key=api_key)
    # Inlined requests: google-genai InlinedRequestDict = {model, contents, ...}.
    src = [{"model": model, "contents": p} for p in plan.prompts]
    job = client.batches.create(model=model, src=src)
    log(f"[gemini-batch] submitted {job.name}; polling every {poll_seconds}s")

    waited = 0
    while not str(getattr(job, "state", "")).endswith(("SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED")):
        time.sleep(poll_seconds)
        waited += poll_seconds
        job = client.batches.get(name=job.name)
        log(f"[gemini-batch] {job.name} state={getattr(job, 'state', '?')}")
        if max_wait_seconds is not None and waited >= max_wait_seconds:
            return {"job": job.name, "state": str(getattr(job, "state", "?")), "timed_out": True}

    if not str(getattr(job, "state", "")).endswith("SUCCEEDED"):
        return {"job": job.name, "state": str(getattr(job, "state", "?")), "written": 0}

    responses = [r.response for r in job.dest.inlined_responses]
    ok, err = writeback_responses(cache_dir, plan.keys, responses)
    log(f"[gemini-batch] wrote {ok} to cache ({err} errors)")
    return {"job": job.name, "state": "SUCCEEDED", "cached": plan.hit_count,
            "written": ok, "errors": err}
