# channels/ — citizen delivery

Owner: **Sejal**. Spec: ARCHITECTURE.md §13, PRD §14.2.

- **Primary (free):** Telegram bot + PWA push.
- **IVR demo:** Twilio trial number (Kannada/Marathi TTS) — pre-verify the judge's number.
- **Public display mode:** big-screen ward board.
- **Localization:** short templated messages + LLM (Gemini) translation, native-speaker reviewed
  for **hi / en / kn / mr**.

Reads `advisories` (Agent 4 output). WhatsApp = production upgrade (has cost) — Telegram is the default.
