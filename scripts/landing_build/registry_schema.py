"""WP-L3 optional registry schema: read-only error-visible projections.

Unknown keys remain unchanged. Malformed input stays visible with the original
raw value; validation never implies Owner approval or authentic custody.
"""
import re

ORIGINAL_CLASSES = frozenset(("ORIGINAL", "SYNTHETIC", "PARTIAL", "MISSING"))
IMPROVEMENT_DISPOSITIONS = frozenset(
    ("KEEP", "PROPOSED", "ADOPTED", "REJECTED", "PARKED"))
_SHA = re.compile(r"^[a-fA-F0-9]{7,64}$")
_SHA256 = re.compile(r"^[a-fA-F0-9]{64}$")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _optional_text(value):
    return value is None or _text(value)


def _error(path, raw, problems):
    return {"status": "ERROR", "reason": "INVALID_REGISTRY_VALUE",
            "path": path, "errors": problems, "raw": raw}


def _fields(value, path, required=(), text_fields=(), optional=(), enums=None):
    """Return field-specific problems; preserve the user's original object."""
    errors = []
    for name in required:
        if name not in value or not _text(value[name]):
            errors.append(f"{path}.{name}")
    for name in text_fields:
        if name in value and name not in required and not _text(value[name]):
            errors.append(f"{path}.{name}")
    for name in optional:
        if name in value and not _optional_text(value[name]):
            errors.append(f"{path}.{name}")
    for name, allowed in (enums or {}).items():
        if name in value and (not isinstance(value[name], str) or
                              value[name] not in allowed):
            errors.append(f"{path}.{name}")
    return errors


def _original(value, path):
    if not isinstance(value, dict):
        return _error(path, value, [path + ".type"])
    issues = _fields(value, path, required=("name", "path"),
                     enums={"class": ORIGINAL_CLASSES})
    if "class" not in value:
        issues.append(path + ".class")
    if "sha" in value and value["sha"] is not None and (
            not isinstance(value["sha"], str) or
            not _SHA.fullmatch(value["sha"])):
        issues.append(path + ".sha")
    if "sha256" in value and value["sha256"] is not None and (
            not isinstance(value["sha256"], str) or
            not _SHA256.fullmatch(value["sha256"])):
        issues.append(path + ".sha256")
    if "custody" in value and not (
            _text(value["custody"]) or isinstance(value["custody"], dict)):
        issues.append(path + ".custody")
    return _error(path, value, sorted(set(issues))) if issues else value


def _improvement(value, path):
    if not isinstance(value, dict):
        return _error(path, value, [path + ".type"])
    issues = _fields(value, path, required=("id", "title", "author"),
                     optional=("reason", "revisit_if", "implemented_in",
                               "observed_result"),
                     enums={"disposition": IMPROVEMENT_DISPOSITIONS})
    if "disposition" not in value:
        issues.append(path + ".disposition")
    if "retain" in value and not isinstance(value["retain"], bool):
        issues.append(path + ".retain")
    return _error(path, value, sorted(set(issues))) if issues else value


def _succession(value, path):
    if not isinstance(value, dict):
        return _error(path, value, [path + ".type"])
    issues = _fields(value, path,
                     text_fields=("outgoing", "incoming", "method", "phase"))
    if "links" in value:
        links = value["links"]
        if not isinstance(links, dict):
            issues.append(path + ".links")
        else:
            for label in ("1a", "1b", "2"):
                if label in links and not _optional_text(links[label]):
                    issues.append(path + ".links." + label)
    if "pending_sends" in value and not isinstance(value["pending_sends"], list):
        issues.append(path + ".pending_sends")
    if "custody" in value and not (
            _text(value["custody"]) or isinstance(value["custody"], dict)):
        issues.append(path + ".custody")
    if "unrecorded_interval" in value:
        interval = value["unrecorded_interval"]
        if not isinstance(interval, dict):
            issues.append(path + ".unrecorded_interval")
        else:
            for label in ("from_checkpoint", "to_departure"):
                if label in interval and not _optional_text(interval[label]):
                    issues.append(path + ".unrecorded_interval." + label)
    return _error(path, value, sorted(set(issues))) if issues else value


def _array(source, key, validator):
    raw = source[key]
    if not isinstance(raw, list):
        return _error(key, raw, [key + ".type"])
    return [validator(row, f"{key}[{i}]") for i, row in enumerate(raw)]


def project_additions(registry):
    """Project only present keys, leaving old registries byte-identical."""
    if not isinstance(registry, dict):
        return {}
    result = {}
    if "originals" in registry:
        result["originals"] = _array(registry, "originals", _original)
    if "improvements" in registry:
        result["improvements"] = _array(registry, "improvements", _improvement)
    if "succession" in registry:
        result["succession"] = _succession(registry["succession"], "succession")
    # history_refs stays on WP-L2(c)'s existing allow-listed lineage fetch.
    return result
