"""IVR / public-display scripts for Agent 4 advisories.

Places a real Twilio voice call that reads an advisory in a clear Indian-English
neural voice, slowed slightly and repeated once for intelligibility over a phone
line. (The legacy 'alice' voice was robotic and the old "press 1/2" menu never
collected input — a working keypad needs a hosted TwiML webhook, so it's dropped
here in favour of a clear, self-contained message.)
"""
from __future__ import annotations

import argparse
import html
import os

import core.env  # noqa: F401  (loads .env)

# Amazon Polly neural voice via Twilio — clear Indian English, far better than 'alice'.
IVR_VOICE = "Polly.Raveena"
IVR_LANG = "en-IN"
BRAND = "Vayu Netra"


def render_ivr_script(advisory: dict) -> str:
    """Plain-text advisory (for public-display boards / logs)."""
    return (
        f"{BRAND} air quality advisory. {advisory.get('message', '')} "
        "Stay safe and limit outdoor exposure."
    )


def render_twiml(advisory: dict) -> str:
    """TwiML for a slowed, repeated, clearly-spoken advisory call."""
    msg = html.escape(str(advisory.get("message", "")).strip())
    body = (
        f"This is an air quality alert from {BRAND}. "
        f'<break time="600ms"/> {msg} '
        f'<break time="800ms"/> I will now repeat this alert. '
        f'<break time="400ms"/> {msg} '
        f'<break time="700ms"/> Stay safe, and limit outdoor exposure. Goodbye.'
    )
    return (
        "<Response>"
        '<Pause length="1"/>'
        f'<Say voice="{IVR_VOICE}" language="{IVR_LANG}">'
        f'<prosody rate="90%">{body}</prosody></Say>'
        "</Response>"
    )


def make_ivr_call(advisory: dict, to_number: str | None = None) -> dict:
    """Place a real Twilio voice call for one advisory.

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
    call = client.calls.create(to=to_number, from_=from_number, twiml=render_twiml(advisory))
    return {"sid": call.sid, "status": call.status}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", help="Recipient phone number; defaults to TWILIO_TO_NUMBER")
    ap.add_argument(
        "--message",
        default="Air quality is expected to be poor over the next 24 hours. Please limit outdoor activity.",
    )
    args = ap.parse_args()

    result = make_ivr_call({"message": args.message}, args.to)
    print(f"started IVR call sid={result['sid']} status={result['status']}")


if __name__ == "__main__":
    main()
