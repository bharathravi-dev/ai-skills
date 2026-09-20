"""M9-L07 lab -- every MCP tool carries an inputSchema, and may carry an
outputSchema. Both are JSON Schema (2020-12 by default). This lab implements a
small, honest subset of a JSON Schema validator -- with local $ref resolution, a
refusal to fetch network $refs, and a work budget for composition keywords --
and uses it to measure:

  1. what an inputSchema catches in a corpus of realistic bad tool arguments,
  2. the difference between {"type":"object"} and additionalProperties:false
     for a tool that takes no parameters,
  3. output drift: a server release that renames a field, with and without
     client-side validation of structuredContent,
  4. why a server should validate its OWN output before sending it,
  5. $ref: local definitions resolve, network URIs are refused,
  6. composition keywords as a denial-of-service vector, and a work budget.

A subset only: type, enum, const, properties, required, additionalProperties,
items, minimum, maximum, minLength, maxLength, pattern, anyOf, oneOf, allOf, $ref.
Production code should use a complete validator (e.g. the `jsonschema` package).
Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m9/l07_input_output_schemas.py
"""

from __future__ import annotations

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


class SchemaError(Exception):
    """The schema itself cannot be used (unresolvable $ref, budget exceeded)."""


class Validator:
    TYPES = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
        "integer": lambda v: (isinstance(v, int) and not isinstance(v, bool)) or (isinstance(v, float) and v.is_integer()),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    }

    def __init__(self, root: dict, budget: int = 10_000):
        self.root, self.budget, self.evaluations = root, budget, 0

    def resolve(self, ref: str) -> dict:
        if not ref.startswith("#/"):
            raise SchemaError(f"refusing to dereference non-local $ref {ref!r}")
        node = self.root
        for part in ref[2:].split("/"):
            node = node[part]
        return node

    def errors(self, value, schema: dict | None = None, path: str = "$") -> list[str]:
        schema = self.root if schema is None else schema
        self.evaluations += 1
        if self.evaluations > self.budget:
            raise SchemaError(f"validation budget of {self.budget} subschema evaluations exceeded")
        out: list[str] = []
        if "$ref" in schema:
            out += self.errors(value, self.resolve(schema["$ref"]), path)
        t = schema.get("type")
        if t is not None:
            allowed = t if isinstance(t, list) else [t]
            if not any(self.TYPES[a](value) for a in allowed):
                return out + [f"{path}: expected {t}, got {type(value).__name__} {value!r}"]
        if "enum" in schema and value not in schema["enum"]:
            out.append(f"{path}: {value!r} not in {schema['enum']}")
        if "const" in schema and value != schema["const"]:
            out.append(f"{path}: must equal {schema['const']!r}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                out.append(f"{path}: {value} < minimum {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                out.append(f"{path}: {value} > maximum {schema['maximum']}")
        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                out.append(f"{path}: shorter than {schema['minLength']}")
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                out.append(f"{path}: longer than {schema['maxLength']}")
            if "pattern" in schema and not re.search(schema["pattern"], value):
                out.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if isinstance(value, dict):
            props = schema.get("properties", {})
            for name in schema.get("required", []):
                if name not in value:
                    out.append(f"{path}: missing required {name!r}")
            for name, sub in value.items():
                if name in props:
                    out += self.errors(sub, props[name], f"{path}.{name}")
                elif schema.get("additionalProperties") is False:
                    out.append(f"{path}: unexpected property {name!r}")
        if isinstance(value, list) and "items" in schema:
            for i, item in enumerate(value):
                out += self.errors(item, schema["items"], f"{path}[{i}]")
        if "allOf" in schema:
            for sub in schema["allOf"]:
                out += self.errors(value, sub, path)
        if "anyOf" in schema:
            if not any(not self.errors(value, sub, path) for sub in schema["anyOf"]):
                out.append(f"{path}: matches none of anyOf")
        if "oneOf" in schema:
            n = sum(1 for sub in schema["oneOf"] if not self.errors(value, sub, path))
            if n != 1:
                out.append(f"{path}: matches {n} of oneOf (need exactly 1)")
        return out


# ============================================================ 1
rule("1. WHAT AN inputSchema CATCHES IN REALISTIC BAD ARGUMENTS")

REFUND_INPUT = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string", "pattern": "^O-[0-9]{4}$"},
        "amount": {"type": "number", "minimum": 0.01, "maximum": 500},
        "reason": {"type": "string", "enum": ["damaged", "late", "wrong_item", "other"]},
        "notify_customer": {"type": "boolean"},
    },
    "required": ["order_id", "amount", "reason"],
    "additionalProperties": False,
}

CORPUS = [
    ("well-formed", {"order_id": "O-1001", "amount": 40.0, "reason": "late"}),
    ("well-formed + optional", {"order_id": "O-1001", "amount": 12, "reason": "damaged", "notify_customer": True}),
    ("amount as string", {"order_id": "O-1001", "amount": "40.00", "reason": "late"}),
    ("currency symbol", {"order_id": "O-1001", "amount": "$40", "reason": "late"}),
    ("negative amount", {"order_id": "O-1001", "amount": -40, "reason": "late"}),
    ("huge amount", {"order_id": "O-1001", "amount": 40000, "reason": "late"}),
    ("enum wrong case", {"order_id": "O-1001", "amount": 40, "reason": "Late"}),
    ("invented enum value", {"order_id": "O-1001", "amount": 40, "reason": "goodwill"}),
    ("missing reason", {"order_id": "O-1001", "amount": 40}),
    ("order id format", {"order_id": "1001", "amount": 40, "reason": "late"}),
    ("hallucinated field", {"order_id": "O-1001", "amount": 40, "reason": "late", "override_limit": True}),
    ("boolean as string", {"order_id": "O-1001", "amount": 40, "reason": "late", "notify_customer": "yes"}),
    ("snake vs camel", {"orderId": "O-1001", "amount": 40, "reason": "late"}),
    ("null amount", {"order_id": "O-1001", "amount": None, "reason": "late"}),
]
caught_required_only = caught_types = caught_full = 0
for label, args in CORPUS:
    required_only = any(k not in args for k in REFUND_INPUT["required"])
    types_only = required_only or any(
        k in args and not Validator.TYPES[REFUND_INPUT["properties"][k]["type"]](args[k])
        for k in REFUND_INPUT["properties"])
    errs = Validator(REFUND_INPUT).errors(args)
    caught_required_only += required_only
    caught_types += types_only
    caught_full += bool(errs)
    print(f"  {label:<24} -> {'OK' if not errs else errs[0]}")
bad = len(CORPUS) - 2
print(f"\n  {bad} bad payloads. Caught by: required-keys check {caught_required_only}/{bad}, "
      f"+type check {caught_types}/{bad}, full schema {caught_full}/{bad}")


# ============================================================ 2
rule("2. A TOOL WITH NO PARAMETERS: TWO 'VALID' SCHEMAS, DIFFERENT GUARANTEES")

LOOSE = {"type": "object"}
STRICT = {"type": "object", "additionalProperties": False}
calls = [{}, {"force": True}, {"all_regions": True}, {"confirm": "yes"}, {"dry_run": False}]
loose_ok = sum(not Validator(LOOSE).errors(c) for c in calls)
strict_ok = sum(not Validator(STRICT).errors(c) for c in calls)
print(f"  get_current_time called with {calls}")
print(f"    {{'type':'object'}}                        accepted {loose_ok}/5")
print(f"    {{'type':'object','additionalProperties':false}} accepted {strict_ok}/5")
print("\n  The loose schema passes {'force': True} to the handler. If the handler")
print("  ever reads kwargs, a model can switch on behaviour nobody declared.")


# ============================================================ 3
rule("3. OUTPUT DRIFT: A SERVER RELEASE RENAMES A FIELD")

ORDER_OUTPUT = {
    "type": "object",
    "properties": {"order_id": {"type": "string"}, "status": {"type": "string",
                   "enum": ["processing", "shipped", "delivered"]}, "amount": {"type": "number"}},
    "required": ["order_id", "status", "amount"],
}


def server_v1(order_id):
    return {"order_id": order_id, "status": "delivered", "amount": 40.0}


def server_v2(order_id):  # the release renamed status -> state
    return {"order_id": order_id, "state": "delivered", "amount": 40.0}


def refund_decision(structured: dict) -> str:
    return "eligible" if structured.get("status") == "delivered" else "not eligible"


for name, server in (("v1", server_v1), ("v2", server_v2)):
    denied = sum(refund_decision(server(f"O-{i:04d}")) == "not eligible" for i in range(50))
    detected = sum(bool(Validator(ORDER_OUTPUT).errors(server(f"O-{i:04d}"))) for i in range(50))
    print(f"  server {name}: 50 delivered orders -> unvalidated client denied {denied:>2}; "
          f"validating client flagged {detected:>2} results as off-schema")
print("\n  With v2, every refund was wrongly denied and nothing raised an error:")
print("  .get('status') simply returned None. Validating against outputSchema")
print("  turned 50 silent wrong decisions into 50 loud, attributable failures.")


# ============================================================ 4
rule("4. A SERVER MUST CONFORM TO ITS OWN outputSchema: CHECK BEFORE SENDING")


def make_result(structured, output_schema, self_check: bool):
    if self_check:
        errs = Validator(output_schema).errors(structured)
        if errs:
            return {"resultType": "complete", "isError": True,
                    "content": [{"type": "text", "text": "Internal error: result failed output schema"}]}
    return {"resultType": "complete", "isError": False, "structuredContent": structured,
            "content": [{"type": "text", "text": json.dumps(structured)}]}


for flag in (False, True):
    r = make_result(server_v2("O-1001"), ORDER_OUTPUT, self_check=flag)
    print(f"  self_check={flag!s:<5} -> isError={r['isError']}, "
          f"structuredContent={'present' if 'structuredContent' in r else 'absent'}")
print("\n  Without the self-check the drifted object ships as if valid. With it, the")
print("  caller gets an explicit error instead. When structuredContent IS sent, the")
print("  result also carries a TextContent copy of the JSON -- the spec's backward-")
print("  compatibility SHOULD for clients that only read text.")


# ============================================================ 5
rule("5. $ref: LOCAL DEFINITIONS RESOLVE, NETWORK URIs ARE REFUSED")

LOCAL = {"$defs": {"money": {"type": "number", "minimum": 0}},
         "type": "object", "properties": {"amount": {"$ref": "#/$defs/money"}}, "required": ["amount"]}
REMOTE = {"type": "object", "properties": {"amount": {"$ref": "http://169.254.169.254/latest/meta-data/"}}}
v = Validator(LOCAL)
print(f"  local  $ref, amount=-5  -> {v.errors({'amount': -5})}")
try:
    Validator(REMOTE).errors({"amount": 5})
except SchemaError as exc:
    print(f"  remote $ref             -> schema rejected: {exc}")
print("\n  Implementations MUST NOT dereference network $refs by default. This")
print("  one points at a cloud metadata endpoint: a server-supplied schema would")
print("  otherwise make the CLIENT issue an internal network request (SSRF).")


# ============================================================ 6
rule("6. COMPOSITION KEYWORDS AS A DENIAL-OF-SERVICE VECTOR")


def nested_anyof(depth: int) -> dict:
    """Each level references the level below TWICE via $ref, so the schema grows
    linearly with depth while the validation work grows exponentially."""
    defs: dict = {"n0": {"type": "string"}}
    for i in range(1, depth + 1):
        below = {"$ref": f"#/$defs/n{i - 1}"}
        defs[f"n{i}"] = {"anyOf": [{"allOf": [below, {"minLength": 999}]},
                                   {"allOf": [below, {"maxLength": 0}]}]}
    return {"$defs": defs, "$ref": f"#/$defs/n{depth}"}


print("  depth   schema bytes   evaluations (unbounded)   with budget 5,000")
for depth in (4, 8, 12, 14):
    schema = nested_anyof(depth)
    unbounded = Validator(schema, budget=10**9)
    unbounded.errors("hello")
    bounded = Validator(schema, budget=5_000)
    try:
        bounded.errors("hello")
        verdict = f"validated in {bounded.evaluations:,}"
    except SchemaError:
        verdict = "rejected: budget exceeded"
    print(f"  {depth:>5}   {len(json.dumps(schema)):>12,}   {unbounded.evaluations:>22,}   {verdict}")
print("\n  A schema of about a kilobyte forces exponential work because each anyOf")
print("  branch re-validates the whole level below it through $ref. The spec says")
print("  implementations SHOULD bound depth, subschema count or time.")


# ============================================================ 7
rule("7. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every validation verdict, catch count, drift count and evaluation")
print("  count above is produced by running this validator on these inputs.")
print("\n  ILLUSTRATIVE: the validator is a teaching subset -- no format, no")
print("  unevaluatedProperties, no dynamic refs, no dialect switching -- and")
print("  section 1's corpus is hand-written to resemble common model mistakes.")
print("\n  NOT SHOWN: tool-name validation, x-mcp-header rules (M9-L08), and")
print("  schema design for the model's benefit -- descriptions, examples and")
print("  enum wording that improve argument accuracy (M9-L15).")
print("\nDone.")
