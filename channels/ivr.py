"""IVR/public-display scripts for Agent 4 advisories."""
from __future__ import annotations


def render_ivr_script(advisory: dict) -> str:
    return (
        f"VayuNetra air quality advisory. {advisory['message']} "
        "Press 1 to repeat. Press 2 for nearest clean-air shelter information."
    )
