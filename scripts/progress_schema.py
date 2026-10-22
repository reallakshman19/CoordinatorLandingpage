"""Small fail-closed JSON Schema 2020-12 evaluator for Progress data.

Implements only the keywords used by the checked-in contracts. Never silently
ignores unknown schema keywords; no third-party packages or network access.
"""
import re


class UnsupportedKeyword(ValueError):
    """A schema requests a keyword this evaluator cannot enforce."""


KEYWORDS = {
    "$schema", "type", "properties", "required", "additionalProperties",
    "items", "enum", "const", "pattern", "minimum", "minLength",
    "minItems", "oneOf",
}
TYPES = {"object", "array", "string", "integer", "boolean", "null", "number"}


def check_schema(schema, at="$"):
    """Preflight every branch, including branches the present data cannot reach."""
    if not isinstance(schema, dict):
        raise UnsupportedKeyword(f"{at}: schema must be an object")
    for keyword, value in schema.items():
        if keyword not in KEYWORDS:
            raise UnsupportedKeyword(f"{at}: unsupported schema keyword {keyword!r}")
        if keyword == "$schema" and value != "https://json-schema.org/draft/2020-12/schema":
            raise UnsupportedKeyword(f"{at}: unsupported JSON Schema dialect {value!r}")
        if keyword == "type" and (not isinstance(value, str) or value not in TYPES):
            raise UnsupportedKeyword(f"{at}: unsupported schema type {value!r}")
        if keyword in ("properties",) and not isinstance(value, dict):
            raise UnsupportedKeyword(f"{at}: properties must be an object")
        if keyword == "required" and (not isinstance(value, list) or
                                       not all(isinstance(k, str) for k in value)):
            raise UnsupportedKeyword(f"{at}: required must be a string list")
        if keyword == "oneOf" and (not isinstance(value, list) or not value):
            raise UnsupportedKeyword(f"{at}: oneOf must be a nonempty array")
        if keyword == "additionalProperties" and not isinstance(value, (bool, dict)):
            raise UnsupportedKeyword(f"{at}: additionalProperties must be bool or schema")
        if keyword in ("items",) and not isinstance(value, dict):
            raise UnsupportedKeyword(f"{at}: items must be a schema")
        if keyword in ("minimum", "minLength", "minItems") and (
                isinstance(value, bool) or not isinstance(value, int) or
                (keyword != "minimum" and value < 0)):
            raise UnsupportedKeyword(f"{at}: {keyword} needs an integer bound")
        if keyword == "pattern" and not isinstance(value, str):
            raise UnsupportedKeyword(f"{at}: pattern must be a string")
        if keyword == "enum" and (not isinstance(value, list) or not value):
            raise UnsupportedKeyword(f"{at}: enum must be a nonempty array")
    for name, child in schema.get("properties", {}).items():
        check_schema(child, f"{at}.properties.{name}")
    if isinstance(schema.get("additionalProperties"), dict):
        check_schema(schema["additionalProperties"], f"{at}.additionalProperties")
    if "items" in schema:
        check_schema(schema["items"], f"{at}.items")
    for i, child in enumerate(schema.get("oneOf", [])):
        check_schema(child, f"{at}.oneOf[{i}]")


def _is_type(value, t):
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "boolean": lambda: isinstance(value, bool),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: isinstance(value, (int, float)) and not isinstance(value, bool),
        "null": lambda: value is None,
    }[t]()


def validate(value, schema, at="$"):
    """Return data errors, never silently skip a supported constraint."""
    errors = []
    if "type" in schema and not _is_type(value, schema["type"]):
        return [f"{at}: expected {schema['type']}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{at}: value {value!r} not in enum {schema['enum']!r}")
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        errors.append(f"{at}: expected const {schema['const']!r}")
    if "oneOf" in schema:
        matches = sum(not validate(value, case, at) for case in schema["oneOf"])
        if matches != 1:
            errors.append(f"{at}: oneOf matched {matches} alternatives (expected 1)")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{at}: does not match pattern {schema['pattern']!r}")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{at}: length below {schema['minLength']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{at}: below minimum {schema['minimum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{at}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(validate(item, schema["items"], f"{at}[{i}]"))
    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{at}: missing required {name!r}")
        props = schema.get("properties", {})
        rest = schema.get("additionalProperties", True)
        for k, v in value.items():
            if k in props:
                errors.extend(validate(v, props[k], f"{at}.{k}"))
            elif rest is False:
                errors.append(f"{at}: extra property {k!r}")
            elif isinstance(rest, dict):
                errors.extend(validate(v, rest, f"{at}.{k}"))
    return errors

def scan_forbidden(raw, private):
    """Return forbidden-content findings; private relaxes only ChatGPT links."""
    bad = []
    if re.search(r"drive\.google\.com|docs\.google\.com", raw):
        bad.append("contains a Google Drive link")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw):
        bad.append("contains an email address")
    if not private and re.search(r"chatgpt\.com/c/|chat\.openai\.com", raw):
        bad.append("contains a ChatGPT chat link (public repo: id8 only)")
    return bad


def check_links(value):
    """Walk content, including nested options and fixture entries."""
    problems = []
    if isinstance(value, dict):
        for name, item in value.items():
            if name in ("u", "url", "ref") and isinstance(item, str) and item and not item.startswith("https://"):
                problems.append(f"link must start with https:// ({item[:50]})")
            problems.extend(check_links(item))
    elif isinstance(value, list):
        for item in value:
            problems.extend(check_links(item))
    return problems


def check_topic(data, chats):
    """Cross-file constraints are separate from per-file schema checks."""
    problems = []
    for sid, stage in data["stages"].items():
        if not isinstance(stage, dict):
            continue
        if stage.get("milestone") not in data["meta"].get("milestones", {}):
            problems.append(("stages", f"{sid}: unknown milestone {stage.get('milestone')!r}"))
        if stage.get("lane") not in data["meta"].get("lanes", {}):
            problems.append(("stages", f"{sid}: unknown lane {stage.get('lane')!r}"))
        for chat in stage.get("chats", []):
            if chat not in chats:
                problems.append(("stages", f"{sid}: chat key {chat!r} not in index.json"))
    for cid, card in data["actions"].items():
        if not isinstance(card, dict):
            continue
        for stage in card.get("stages", []):
            if stage not in data["stages"]:
                problems.append(("actions", f"{cid}: unknown stage {stage!r}"))
        if card.get("status") == "open" and sum(
                bool(option.get("suggested")) for option in card.get("options", [])
                if isinstance(option, dict)) != 1:
            problems.append(("actions", f"{cid}: open card needs exactly one suggested option"))
        if card.get("status") == "done":
            answer = card.get("answer")
            for field in ("text", "at", "ref"):
                if not isinstance(answer, dict) or not isinstance(answer.get(field), str) or not answer[field]:
                    problems.append(("actions", f"{cid}: done card needs answer.{field}"))
    sections = ("repository", "issues", "pullRequests", "roadmap", "highRoi",
                "future", "intent", "inputs", "knownIssues", "pending")
    for name, entries in data["fixtures"].items():
        if name not in sections:
            problems.append(("fixtures", f"unknown fixture section {name!r}"))
        elif isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and not entry.get("t"):
                    problems.append(("fixtures", f"{name}: entry has no text"))
    return problems
