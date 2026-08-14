# Stage 1 Demo Video Runbook

## Output

Target file: `docs/VayuNetra_Stage1_Demo.mp4`

This environment does not have a video encoder or screen recorder available, so the final MP4 must be recorded from the running app. Use this runbook to produce the actual video in one take.

## Setup

1. Start API:
   `python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8010`
2. Start web:
   `cd web`
   `$env:VITE_API_BASE_URL="http://127.0.0.1:8010"`
   `npm run dev`
3. Open `http://localhost:5173`.

## Shot List

1. Delhi map opens on source attribution.
2. Toggle satellite NO2, then return to Sources.
3. Scrub forecast +24h, +48h, +72h.
4. Show Enforcement Worklist and read the top construction-dust recommendation.
5. Open Citizen tab, switch language to Hindi, show Telegram and IVR advisory text.
6. Open Compare tab and switch Delhi -> Bengaluru -> Mumbai.
7. End on the Signal-to-Action latency widget.

## Voiceover

"VayuNetra turns air-quality data into action. The blame map shows the dominant source per H3 cell, not just AQI. The forecast tells officers where the next spike is coming. The enforcement panel ranks field actions by contribution and exposed population. The citizen panel localizes advisories into English, Hindi, Kannada, and Marathi across app, Telegram, IVR, and display channels. Finally, the same engine switches across Delhi, Bengaluru, and Mumbai from config-driven city onboarding. The result is signal to action in minutes."
