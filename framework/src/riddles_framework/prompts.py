from __future__ import annotations

from pathlib import Path

import yaml

from .constants import ResponseFormat, RiddleLanguagePresented
from .exceptions import PromptBuildError, PromptTemplateNotFoundError
from .schemas import BenchmarkInstance, PromptConfig, PromptTemplate

# ---------------------------------------------------------------------------
# Prompt template loading
# ---------------------------------------------------------------------------
#
# Templates live in `prompt_templates/` alongside this file as YAML files with
# the schema:
#
#   template_id: riddle_basic
#   template_version: v1
#   instruction_text: |
#     ...
#   recommended_response_format: json   # optional
#
# Contributors add new templates by dropping a new YAML file; no code change.

TEMPLATES_DIR = Path(__file__).parent / "prompt_templates"


def _iter_template_files() -> list[Path]:
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(TEMPLATES_DIR.glob("*.yaml")) + sorted(TEMPLATES_DIR.glob("*.yml"))


def load_prompt_template(template_id: str, template_version: str) -> PromptTemplate:
    """Look up a PromptTemplate by (template_id, template_version).

    Raises PromptTemplateNotFoundError if no matching template file is found.
    """
    for path in _iter_template_files():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            raise PromptBuildError(f"Failed to parse template file {path}: {exc}") from exc

        if (
            data.get("template_id") == template_id
            and data.get("template_version") == template_version
        ):
            instruction = data.get("instruction_text")
            if not instruction or not str(instruction).strip():
                raise PromptBuildError(
                    f"Template {template_id} {template_version} is missing instruction_text"
                )
            rec_fmt_raw = data.get("recommended_response_format")
            rec_fmt = ResponseFormat(rec_fmt_raw) if rec_fmt_raw else None
            return PromptTemplate(
                template_id=template_id,
                template_version=template_version,
                instruction_text=str(instruction).strip(),
                recommended_response_format=rec_fmt,
            )

    available = []
    for path in _iter_template_files():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            available.append(f"{data.get('template_id')}@{data.get('template_version')}")
        except Exception:
            continue
    raise PromptTemplateNotFoundError(
        f"No template found for {template_id}@{template_version}. "
        f"Available: {available}"
    )


def list_available_templates() -> list[tuple[str, str]]:
    """Return a list of (template_id, template_version) tuples available on disk."""
    out: list[tuple[str, str]] = []
    for path in _iter_template_files():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            tid = data.get("template_id")
            tver = data.get("template_version")
            if tid and tver:
                out.append((tid, tver))
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_condition_id(
    riddle_language_presented: RiddleLanguagePresented,
    is_hint_provided: bool,
) -> str:
    return f"{riddle_language_presented.value}_{'with_hint' if is_hint_provided else 'no_hint'}"


def get_presented_riddle_text(
    instance: BenchmarkInstance,
    riddle_language_presented: RiddleLanguagePresented,
) -> str:
    if riddle_language_presented == RiddleLanguagePresented.SOURCE:
        return instance.riddle_original

    if riddle_language_presented == RiddleLanguagePresented.ENGLISH:
        if not instance.riddle_english or not instance.riddle_english.strip():
            raise PromptBuildError(
                f"{instance.riddle_id}: missing riddle_english for english condition"
            )
        return instance.riddle_english

    raise PromptBuildError(
        f"{instance.riddle_id}: unsupported riddle_language_presented={riddle_language_presented}"
    )


def get_presented_hint_text(
    instance: BenchmarkInstance,
    riddle_language_presented: RiddleLanguagePresented,
    is_hint_provided: bool,
) -> str | None:
    if not is_hint_provided:
        return None

    if riddle_language_presented == RiddleLanguagePresented.ENGLISH:
        raise PromptBuildError(f"{instance.riddle_id}: english + hints is unsupported")

    return instance.riddle_hint


def maybe_wrap_instruction_for_response_format(
    instruction_text: str,
    response_format: ResponseFormat,
) -> str:
    if response_format == ResponseFormat.FREE_FORM:
        return instruction_text

    if response_format == ResponseFormat.JSON:
        return (
            instruction_text
            + '\nReturn only valid JSON in this format: {"riddle_answer": "your answer"}'
        )

    if response_format == ResponseFormat.JSON_SCHEMA:
        return (
            instruction_text
            + '\nReturn strict JSON with exactly this schema: {"riddle_answer": "string"}'
        )

    return instruction_text


def build_prompt(
    instance: BenchmarkInstance,
    template: PromptTemplate,
    prompt_config: PromptConfig,
) -> str:
    riddle_text = get_presented_riddle_text(
        instance,
        prompt_config.riddle_language_presented,
    )
    hint_text = get_presented_hint_text(
        instance,
        prompt_config.riddle_language_presented,
        prompt_config.is_hint_provided,
    )
    instruction = maybe_wrap_instruction_for_response_format(
        template.instruction_text,
        prompt_config.response_format,
    )
    temp_template = PromptTemplate(
        template_id=template.template_id,
        template_version=template.template_version,
        instruction_text=instruction,
    )
    return temp_template.render(riddle_text=riddle_text, hint_text=hint_text)
