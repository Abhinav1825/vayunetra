"""IVR/public-display scripts for Agent 4 advisories."""
from __future__ import annotations

import argparse
import os

import core.env  # noqa: F401  (loads .env)


def render_ivr_script(advisory: dict) -> str:
    return (
        f"VayuNetra air quality advisory. {advisory['message']} "
        "Press 1 to repeat. Press 2 for nearest clean-air shelter information."
    )


def make_ivr_call(advisory: dict, to_number: str | None = None) -> dict:
    """Place a real Twilio trial/prod voice call for one advisory.

    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, and either
    TWILIO_TO_NUMBER or --to. Trial accounts can call only verified recipient numbers.
    """
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    to_number = to_number or os.getenv("TWILIO_TO_NUMBER")
    missing = [
        name for name, value in {
            "TWILIO_ACCOUNT_SID": sid,
            "TWILIO_AUTH_TOKEN": token,
            "TWILIO_PHONE_NUMBER": from_number,
            "TWILIO_TO_NUMBER": to_number,
        }.items() if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Twilio settings: {', '.join(missing)}")

    from twilio.rest import Client

    client = Client(sid, token)
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        twiml=f"<Response><Say voice='alice'>{render_ivr_script(advisory)}</Say></Response>",
    )
    return {"sid": call.sid, "status": call.status}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", help="Recipient phone number; defaults to TWILIO_TO_NUMBER")
    ap.add_argument("--message", default="Air quality is expected to be poor in the next 24 hours.")
    args = ap.parse_args()

    advisory = {"message": args.message}
    result = make_ivr_call(advisory, args.to)
    print(f"started IVR call sid={result['sid']} status={result['status']}")


if __name__ == "__main__":
    main()
