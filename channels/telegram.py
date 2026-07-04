"""Telegram channel adapter for Agent 4 advisories.

The real bot sender is deliberately separate from message formatting so DEMO_MODE can
show exactly what the judge would receive without requiring a bot token.
"""
from __future__ import annotations


def format_telegram_message(advisory: dict) -> str:
    return (
        f"VayuNetra alert for {advisory['ward_id']}\n"
        f"Risk: {advisory['risk_tier'].replace('_', ' ')} (+{advisory['horizon_h']}h)\n"
        f"{advisory['message']}"
    )
