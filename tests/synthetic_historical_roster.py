"""Synthetic historical-as-of roster for *existing* Next Move browser oracles.

The live registry is never edited. Test-only actors model active 16-Oct agents,
not a present-day revival of generations now recorded RETIRED.
"""
import copy
import re


def historical_active_roster(registry, *identifiers):
    result = copy.deepcopy(registry)
    identities = set(identifiers)
    for row in result.get("agents", []):
        if row.get("chat_id8") in identities:
            row["status"] = "active — SYNTHETIC historical as-of 2026-10-16"
            row.pop("retired", None)
            row.pop("retired_at", None)
    result["leases"] = [
        row for row in result.get("leases", [])
        if not (row.get("released") and any(re.search(
            r"(?<![0-9a-f])" + ident + r"(?![0-9a-f])",
            str(row.get("holder") or row.get("actor") or ""), re.I)
            for ident in identities))
    ]
    return result
