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
