"""M2-L08: validating untrusted input, especially LLM output.

Requires pydantic v2:
    source .venv/bin/activate
    python labs/m2/l08_pydantic.py
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

LINE = "-" * 74


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
# The model an LLM classifier must produce.
# ---------------------------------------------------------------------------
class Classification(BaseModel):
    """A ticket classification returned by a language model."""

    # Invented fields become errors instead of being silently dropped.
    model_config = ConfigDict(extra="forbid")

    category: Literal["billing", "technical", "account", "sales"]
    confidence: float = Field(ge=0.0, le=1.0, description="0-1 certainty")
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("category", mode="before")
    @classmethod
    def normalise_category(cls, v: object) -> object:
        """Runs BEFORE the Literal check, so 'Billing ' becomes 'billing'."""
        return v.strip().lower() if isinstance(v, str) else v


# Nine things a language model actually does.
LLM_OUTPUTS: list[tuple[str, str]] = [
    ("valid", '{"category": "billing", "confidence": 0.92, "reason": "Refund request"}'),
    ("messy case/space", '{"category": "  Billing ", "confidence": 0.8, "reason": "ok"}'),
    ("coercible number", '{"category": "sales", "confidence": "0.75", "reason": "ok"}'),
    ("invented category", '{"category": "refunds", "confidence": 0.9, "reason": "ok"}'),
    ("confidence out of range", '{"category": "billing", "confidence": 1.7, "reason": "ok"}'),
    ("confidence as word", '{"category": "billing", "confidence": "high", "reason": "ok"}'),
    ("missing field", '{"category": "billing", "confidence": 0.5}'),
    ("invented extra field", '{"category": "billing", "confidence": 0.5, "reason": "ok", "urgency": 9}'),
    ("wrapped in code fences", '```json\n{"category": "billing", "confidence": 0.5, "reason": "ok"}\n```'),
]


def format_errors_for_repair(exc: ValidationError) -> str:
    """Turn a ValidationError into text you can send back to a model."""
    parts = []
    for err in exc.errors():
        location = ".".join(str(p) for p in err["loc"]) or "(root)"
        parts.append(f"{location}: {err['msg']} (received {err.get('input')!r})")
    return "; ".join(parts)


def validate_llm_outputs() -> None:
    section("1. NINE REAL LLM FAILURE MODES, VALIDATED")
    for label, raw in LLM_OUTPUTS:
        print(f"  {label}")
        try:
            result = Classification.model_validate_json(raw)
            print(f"    OK -> category={result.category!r} "
                  f"confidence={result.confidence} ({type(result.confidence).__name__})")
        except ValidationError as exc:
            print(f"    REJECTED: {format_errors_for_repair(exc)}")
        except ValueError as exc:
            # Not valid JSON at all - caught before validation begins.
            print(f"    NOT JSON: {type(exc).__name__}")
        print()


def structured_errors() -> None:
    section("2. exc.errors() IS STRUCTURED DATA, NOT A STRING")
    bad = '{"category": "refunds", "confidence": 1.7, "reason": ""}'
    try:
        Classification.model_validate_json(bad)
    except ValidationError as exc:
        print(f"  {len(exc.errors())} errors found in one payload:")
        print()
        for err in exc.errors():
            print(f"    loc   : {err['loc']}")
            print(f"    type  : {err['type']}")
            print(f"    msg   : {err['msg']}")
            print(f"    input : {err.get('input')!r}")
            print()
        print("  Every one of those fields is programmatically accessible.")
        print("  That is what lets you build an API error body, or a repair")
        print("  prompt, without parsing English (M5-L07).")


def coercion_vs_strict() -> None:
    section("3. COERCION vs STRICT MODE")

    class Lenient(BaseModel):
        count: int
        flag: bool

    class Strict(BaseModel):
        model_config = ConfigDict(strict=True)
        count: int
        flag: bool

    cases = [
        {"count": "5", "flag": "true"},
        {"count": 5.0, "flag": True},
        {"count": 5.7, "flag": True},
    ]
    print(f"  {'input':<32}{'default (coercing)':<30}strict=True")
    for case in cases:
        try:
            lenient = repr(Lenient.model_validate(case).model_dump())
        except ValidationError:
            lenient = "REJECTED"
        try:
            strict = repr(Strict.model_validate(case).model_dump())
        except ValidationError:
            strict = "REJECTED"
        print(f"  {json.dumps(case):<32}{lenient:<30}{strict}")
    print()
    print("  Coercion is right for HTTP and forms, where everything arrives")
    print("  as a string. For LLM output, a string where you asked for a")
    print("  number may be a signal the model misread the schema - and")
    print("  strict mode makes that visible instead of hiding it.")
    print("  Note 5.7 -> int is rejected by BOTH: coercion never loses data.")


# ---------------------------------------------------------------------------
# Nested models
# ---------------------------------------------------------------------------
class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc_id: str = Field(min_length=1)
    quote: str = Field(min_length=1, max_length=300)


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    citations: list[Citation] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def quotes_must_differ(self):
        seen = {c.quote for c in self.citations}
        if len(seen) != len(self.citations):
            raise ValueError("citations must not repeat the same quote")
        return self


def nested_errors() -> None:
    section("4. NESTED MODELS - loc PINPOINTS THE FAILING ELEMENT")
    payloads = [
        ("citation missing doc_id",
         {"text": "Refunds take 5 days.",
          "citations": [{"doc_id": "d1", "quote": "five days"}, {"quote": "no id"}],
          "confidence": 0.9}),
        ("empty citations list",
         {"text": "Refunds take 5 days.", "citations": [], "confidence": 0.9}),
        ("duplicate quotes",
         {"text": "x",
          "citations": [{"doc_id": "d1", "quote": "same"}, {"doc_id": "d2", "quote": "same"}],
          "confidence": 0.5}),
    ]
    for label, payload in payloads:
        print(f"  {label}")
        try:
            Answer.model_validate(payload)
            print("    OK")
        except ValidationError as exc:
            for err in exc.errors():
                print(f"    loc={err['loc']}  {err['msg']}")
        print()

    print("  Note loc=('citations', 1, 'doc_id'): list INDEX included. In a")
    print("  20-citation answer that tells you exactly which one is broken.")


def schema_output() -> None:
    section("5. THE GENERATED JSON SCHEMA - your contract with the model")
    schema = Classification.model_json_schema()
    print(json.dumps(schema, indent=2))
    print()
    print("  This is what you hand a language model as its required output")
    print("  format (M5-L06) or as a tool definition (M5-L08, M9-L07).")
    print("  Notice the enum lists the four valid categories, and the")
    print("  description text becomes instruction the model actually reads.")
    print("  One model definition serves as validation, API documentation,")
    print("  and the model's own contract.")


def valid_but_wrong() -> None:
    section("6. THE LIMIT: VALID SHAPE IS NOT CORRECT CONTENT")
    fabricated = {
        "text": "Refunds are processed within 90 days under policy section 12.4.",
        "citations": [{"doc_id": "POLICY-2019-A", "quote": "refunds within 90 days"}],
        "confidence": 0.97,
    }
    answer = Answer.model_validate(fabricated)
    print(f"  Validated successfully: confidence={answer.confidence}")
    print(f"  Citation doc_id: {answer.citations[0].doc_id!r}")
    print()
    print("  Every constraint passed. The document POLICY-2019-A may not")
    print("  exist. The quote may appear nowhere. The 90 days may be wrong.")
    print("  The confidence of 0.97 is a number the model emitted, not a")
    print("  measurement (M1-L10).")
    print()
    print("  Pydantic guarantees SHAPE. It cannot guarantee TRUTH.")
    print("  Verifying that doc_id exists and that the quote really appears")
    print("  in it is a separate, non-optional step - Module 7 (M7-L12).")


def main() -> None:
    print("=" * 74)
    print("TYPE HINTS AND PYDANTIC VALIDATION")
    print("=" * 74)
    validate_llm_outputs()
    structured_errors()
    coercion_vs_strict()
    nested_errors()
    schema_output()
    valid_but_wrong()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
