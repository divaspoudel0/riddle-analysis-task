from __future__ import annotations

import json
from pathlib import Path

import pytest

from riddles_framework.constants import ResponseFormat, RiddleLanguagePresented
from riddles_framework.dataset_loader import load_benchmark_instances
from riddles_framework.exceptions import (
    PromptTemplateNotFoundError,
    UnsupportedConfigurationError,
)
from riddles_framework.factory import create_model
from riddles_framework.prompts import (
    build_condition_id,
    build_prompt,
    list_available_templates,
    load_prompt_template,
)
from riddles_framework.registry import register_model_adapter
from riddles_framework.runner import BenchmarkRunner
from riddles_framework.schemas import (
    BenchmarkInstance,
    ModelCapabilities,
    ModelSpec,
    PromptConfig,
    PromptTemplate,
    RunConfig,
)
from riddles_framework.models.dummy import DummyModel
from riddles_framework.utils import looks_like_refusal
from riddles_framework.yaml_config import load_run_config_from_yaml


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sample_dataset_row() -> dict:
    return {
        "riddle_id": "tamil_india_history_001",
        "source_row_number": 1,
        "language": "tam",
        "community": "tamil_india",
        "topic": "History",
        "is_wildcard": False,
        "riddle_original": "\u0b92\u0bb0\u0bc1 \u0bb5\u0bb0\u0bb2\u0bbe\u0bb1\u0bcd\u0bb1\u0bc1 \u0baa\u0bc1\u0ba4\u0bbf\u0bb0\u0bcd",
        "riddle_english": "A historical riddle",
        "reference_answer_original": "\u0bb0\u0bbe\u0b9c\u0bb0\u0bbe\u0b9c \u0b9a\u0bc7\u0bbe\u0bb4\u0ba9\u0bcd",
        "reference_answer_english": "Rajaraja Chola",
        "riddle_hint": "\u0bae\u0ba9\u0bcd\u0ba9\u0ba9\u0bcd",
        "riddle_note": None,
        "author_credit": "Tester",
        "human_validator_name": None,
        "human_answer_original": None,
        "human_answer_score": None,
        "human_answer_comment": None,
        "row_status": "valid",
        "raw_template_fields": {},
    }


def test_dataset_loader_reads_valid_jsonl(tmp_path: Path):
    dataset_path = tmp_path / "dataset.jsonl"
    write_jsonl(dataset_path, [sample_dataset_row()])

    instances = load_benchmark_instances(dataset_path)
    assert len(instances) == 1
    assert instances[0].riddle_id == "tamil_india_history_001"
    assert instances[0].language == "tam"


def test_benchmark_instance_validation():
    row = sample_dataset_row()
    inst = BenchmarkInstance.from_dict(row)
    inst.validate()
    assert inst.community == "tamil_india"


def test_prompt_build_source_no_hint():
    inst = BenchmarkInstance.from_dict(sample_dataset_row())
    template = PromptTemplate(
        template_id="riddle_basic",
        template_version="v1",
        instruction_text="Solve this riddle.",
    )
    cfg = PromptConfig(
        prompt_language="eng",
        riddle_language_presented=RiddleLanguagePresented.SOURCE,
        is_hint_provided=False,
        response_format=ResponseFormat.FREE_FORM,
    )
    prompt = build_prompt(inst, template, cfg)
    assert "RIDDLE:" in prompt
    assert "HINT:" not in prompt
    assert "\u0b92\u0bb0\u0bc1 \u0bb5\u0bb0\u0bb2\u0bbe\u0bb1\u0bcd\u0bb1\u0bc1 \u0baa\u0bc1\u0ba4\u0bbf\u0bb0\u0bcd" in prompt


def test_prompt_build_source_with_hint():
    inst = BenchmarkInstance.from_dict(sample_dataset_row())
    template = PromptTemplate(
        template_id="riddle_basic",
        template_version="v1",
        instruction_text="Solve this riddle.",
    )
    cfg = PromptConfig(
        prompt_language="eng",
        riddle_language_presented=RiddleLanguagePresented.SOURCE,
        is_hint_provided=True,
        response_format=ResponseFormat.FREE_FORM,
    )
    prompt = build_prompt(inst, template, cfg)
    assert "HINT:" in prompt
    assert "\u0bae\u0ba9\u0bcd\u0ba9\u0ba9\u0bcd" in prompt


def test_condition_id():
    cid = build_condition_id(RiddleLanguagePresented.SOURCE, False)
    assert cid == "source_no_hint"


def test_load_prompt_template_v1():
    tpl = load_prompt_template("riddle_basic", "v1")
    assert tpl.template_id == "riddle_basic"
    assert tpl.template_version == "v1"
    assert "Solve" in tpl.instruction_text
    assert tpl.recommended_response_format == ResponseFormat.FREE_FORM


def test_load_prompt_template_v2_structured():
    tpl = load_prompt_template("riddle_basic", "v2")
    assert tpl.recommended_response_format == ResponseFormat.JSON


def test_load_prompt_template_missing_raises():
    with pytest.raises(PromptTemplateNotFoundError):
        load_prompt_template("nonexistent", "v999")


def test_list_available_templates_includes_shipped_ones():
    available = list_available_templates()
    assert ("riddle_basic", "v1") in available
    assert ("riddle_basic", "v2") in available


def _dummy_spec() -> ModelSpec:
    return ModelSpec(
        model_name="Dummy Echo",
        model_id="dummy/echo-v1",
        provider="dummy",
        access_pattern="local",
        provider_model_name="dummy-echo-v1",
        capabilities=ModelCapabilities(
            supports_reasoning=False,
            supports_search=False,
            supports_structured_output=True,
            supports_batch=False,
            supports_seed=False,
        ),
        closed_source=False,
    )


def test_dummy_runner_creates_outputs(tmp_path: Path):
    dataset_path = tmp_path / "dataset.jsonl"
    write_jsonl(dataset_path, [sample_dataset_row()])

    spec = _dummy_spec()

    run_config = RunConfig(
        model_spec=spec,
        runner_name="tester",
        dataset_path=str(dataset_path),
        dataset_version="test_v1",
        prompt_template_id="riddle_basic",
        prompt_template_version="v1",
        prompt_language="eng",
        riddle_language_presented=RiddleLanguagePresented.SOURCE,
        is_hint_provided=False,
        response_format=ResponseFormat.JSON,
        temperature=None,
        max_output_tokens=32,
    )

    model = DummyModel(spec)
    template = PromptTemplate(
        template_id="riddle_basic",
        template_version="v1",
        instruction_text="Solve this riddle.",
    )

    runner = BenchmarkRunner(
        run_config=run_config,
        prompt_template=template,
        model=model,
        output_root=tmp_path / "runs",
    )
    run_id = runner.run()

    run_dir = tmp_path / "runs" / run_id
    assert run_dir.exists()
    assert (run_dir / "run_config.json").exists()
    assert (run_dir / "run_metadata.json").exists()
    assert (run_dir / "results.jsonl").exists()
    assert (run_dir / "manifest.json").exists()

    results = (run_dir / "results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(results) == 1
    row = json.loads(results[0])
    assert row["generation_status"] == "success"
    assert row["raw_response"] is not None
    # Temperature should be recorded as None when not set.
    assert row["temperature"] is None
    # model_params field should be present (even if empty) for analysis joins.
    assert "model_params" in row


def test_runner_rejects_english_with_hint(tmp_path: Path):
    dataset_path = tmp_path / "dataset.jsonl"
    write_jsonl(dataset_path, [sample_dataset_row()])

    spec = _dummy_spec()
    run_config = RunConfig(
        model_spec=spec,
        runner_name="tester",
        dataset_path=str(dataset_path),
        dataset_version="test_v1",
        prompt_template_id="riddle_basic",
        prompt_template_version="v1",
        prompt_language="eng",
        riddle_language_presented=RiddleLanguagePresented.ENGLISH,
        is_hint_provided=True,
    )

    model = DummyModel(spec)
    template = PromptTemplate(
        template_id="riddle_basic",
        template_version="v1",
        instruction_text="Solve this riddle.",
    )

    runner = BenchmarkRunner(
        run_config=run_config,
        prompt_template=template,
        model=model,
        output_root=tmp_path / "runs",
    )

    with pytest.raises(UnsupportedConfigurationError):
        runner.run()


def test_model_params_are_threaded_through(tmp_path: Path):
    """The runner should forward model_params verbatim to the adapter."""
    dataset_path = tmp_path / "dataset.jsonl"
    write_jsonl(dataset_path, [sample_dataset_row()])

    spec = _dummy_spec()
    run_config = RunConfig(
        model_spec=spec,
        runner_name="tester",
        dataset_path=str(dataset_path),
        dataset_version="test_v1",
        prompt_template_id="riddle_basic",
        prompt_template_version="v1",
        prompt_language="eng",
        riddle_language_presented=RiddleLanguagePresented.SOURCE,
        is_hint_provided=False,
        model_params={"top_p": 0.95, "frequency_penalty": 0.1},
    )

    model = DummyModel(spec)
    template = PromptTemplate(
        template_id="riddle_basic",
        template_version="v1",
        instruction_text="Solve this riddle.",
    )

    runner = BenchmarkRunner(
        run_config=run_config,
        prompt_template=template,
        model=model,
        output_root=tmp_path / "runs",
    )
    run_id = runner.run()

    row = json.loads(
        (tmp_path / "runs" / run_id / "results.jsonl").read_text().strip()
    )
    assert row["model_params"] == {"top_p": 0.95, "frequency_penalty": 0.1}
    # The Dummy adapter echoes model_params into provider_details for verification.
    assert row["provider_details"]["model_params"] == {
        "top_p": 0.95,
        "frequency_penalty": 0.1,
    }


def test_registry_and_factory_dummy():
    key = "dummytest:local"

    try:
        register_model_adapter(key, lambda spec, cfg: DummyModel(spec))
    except Exception:
        pass

    spec = ModelSpec(
        model_name="Dummy Test",
        model_id="dummytest/echo-v1",
        provider="dummytest",
        access_pattern="local",
        provider_model_name="dummy-echo-v1",
    )
    model = create_model(spec, {})
    assert model.model_id == "dummytest/echo-v1"


def test_yaml_config_loading(tmp_path: Path):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
runner_name: tester
dataset_path: data_loading/pilot_dataset/pilot_dataset_v1.jsonl
dataset_version: pilot_dataset_v1
prompt_template_id: riddle_basic
prompt_template_version: v1
prompt_language: eng
riddle_language_presented: source
is_hint_provided: false
reasoning_mode: null
search_enabled: false
response_format: json
batch_mode: false
temperature: null
max_output_tokens: 64
seed: null
model_params:
  top_p: 0.9
cache_enabled: false
cache_backend: null
cache_namespace: null
cache_dir: null
api_key_env_var: null
base_url: null
runner_version: v1.0.0
notes: test config
strict_capability_check: true

model_spec:
  model_name: Dummy Echo
  model_id: dummy/echo-v1
  provider: dummy
  access_pattern: local
  provider_model_name: dummy-echo-v1
  closed_source: false
  notes: Dummy model
  capabilities:
    supports_reasoning: false
    supports_search: false
    supports_structured_output: true
    supports_batch: false
    supports_seed: false
""",
        encoding="utf-8",
    )

    cfg = load_run_config_from_yaml(str(yaml_path))
    assert cfg.runner_name == "tester"
    assert cfg.model_spec.model_id == "dummy/echo-v1"
    assert cfg.riddle_language_presented.value == "source"
    # Optional temperature defaults to None when YAML says null.
    assert cfg.temperature is None
    # model_params loads through.
    assert cfg.model_params == {"top_p": 0.9}
    # response_format defaults to json now.
    assert cfg.response_format == ResponseFormat.JSON


def test_refusal_heuristic():
    # Policy refusals: should be tagged.
    assert looks_like_refusal("I'm sorry, but I can't help with that.")
    assert looks_like_refusal("I cannot assist with that.")

    # Honest uncertainty: must NOT be tagged as refusal.
    assert not looks_like_refusal("I cannot determine the answer from the given information.")
    assert not looks_like_refusal("I do not have enough information.")
    assert not looks_like_refusal("I don't know.")

    # Normal answers: not refusals.
    assert not looks_like_refusal("Paris")
    assert not looks_like_refusal("")
    assert not looks_like_refusal(None)
