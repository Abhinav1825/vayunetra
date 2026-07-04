"""Telegram channel adapter for Agent 4 advisories."""
from __future__ import annotations

import argparse
import asyncio
import os

import core.env  # noqa: F401  (loads .env)


def format_telegram_message(advisory: dict) -> str:
    return (
        f"VayuNetra alert for {advisory['ward_id']}\n"
        f"Risk: {advisory['risk_tier'].replace('_', ' ')} (+{advisory['horizon_h']}h)\n"
        f"{advisory['message']}"
    )


async def send_telegram_advisory(advisory: dict, chat_id: str | None = None) -> dict:
    """Send one advisory through a real Telegram bot.

    Requires TELEGRAM_BOT_TOKEN and either TELEGRAM_CHAT_ID or --chat-id. The token is
    never logged. This function is intentionally thin so tests and DEMO_MODE can keep
    using format_telegram_message without live network calls.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID is missing; message the bot once, then set the chat id")

    from telegram import Bot

    bot = Bot(token=token)
    msg = await bot.send_message(chat_id=chat_id, text=format_telegram_message(advisory))
    return {"chat_id": str(chat_id), "message_id": msg.message_id}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chat-id", help="Telegram chat id; defaults to TELEGRAM_CHAT_ID")
    ap.add_argument("--message", default="VayuNetra Telegram delivery smoke test")
    args = ap.parse_args()

    advisory = {
        "ward_id": "smoke-test",
        "risk_tier": "moderate",
        "horizon_h": 24,
        "message": args.message,
    }
    result = asyncio.run(send_telegram_advisory(advisory, args.chat_id))
    print(f"sent Telegram advisory message_id={result['message_id']}")


if __name__ == "__main__":
    main()
