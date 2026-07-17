# Stage 1 Demo Video Runbook

## Output

Target file: `docs/VayuNetra_Stage1_Demo.mp4`

Record this manually from the live deployment: https://vayunetra-aqi.vercel.app

Keep the final cut at or under 3 minutes. Use one browser window for the app and keep your Telegram device/window visible for the final broadcast proof.

## Pre-Record Checks

1. Open https://vayunetra-aqi.vercel.app and wait for the Delhi map, AQI hero, heat-smog badge, and latency widget to load.
2. Keep the right rail wide enough to show Cell Story, Enforcement, Dossier, What-if, ROI, Agent Pipeline, and Citizen tabs without zooming.
3. Have Telegram open on the subscribed/demo account so the incoming alert is visible after broadcast.
4. Do not use local fixtures for this recording. If the API fallback banner appears, refresh and wait for live data.

## <=3-Minute Shot Script

| Time | Shot | Action | Voiceover |
|---|---|---|---|
| 0:00-0:12 | AQI command view | Open on Delhi. Point at the AQI hero and the heat x smog badge. | "VayuNetra starts with the city officer's live command view: AQI now, forecast risk, and a compound heat x smog warning in the same console." |
| 0:12-0:35 | Cell story | Click a high-risk hexagon. Show blame share and SHAP drivers. Scrub/show +24h forecast. | "Click any hexagon and the system explains the cell: which source dominates, which signals drove the attribution, and what the next 24 to 72 hours look like." |
| 0:35-0:55 | Act from same cell | Keep the selected cell and show the nearest enforcement item. | "The cell story becomes an action queue. The worklist ranks inspections by contribution, exposed population, confidence, and CPCB/GRAP actionability." |
| 0:55-1:18 | Evidence dossier | Open Evidence dossier on the top worklist item. Show RAG citations, including CAQM. | "Before an officer moves, VayuNetra builds the evidence packet: the rationale, regulatory citations, and CAQM/GRAP basis are all traceable." |
| 1:18-1:30 | Notice PDF | Click Notice PDF and show the download beginning or opened PDF tab. | "The same packet becomes a draft notice PDF, ready for officer review rather than automatic enforcement." |
| 1:30-1:52 | What-if simulation | Open What-if. Run an intervention. Show cited magnitudes and people protected. | "Now we test policy before dispatch: the simulator returns AQI deltas, cited intervention magnitudes, real population protected, health cost, cases, and carbon co-benefits." |
| 1:52-2:08 | ROI panel | Show the ROI panel/cards. | "The ROI panel translates air quality into budget language: people protected, rupees saved, and tonnes avoided, with citations carried through." |
| 2:08-2:28 | Agent Pipeline | Open Agent Pipeline and click Run agents live. Let the trace populate. | "The five-agent pipeline can run live: attribution, forecast, enforcement, advisory, and multi-city intelligence, with timing visible end to end." |
| 2:28-2:48 | Citizen broadcast | Open Citizen tab and broadcast the latest alert. Show Telegram arriving. | "Finally the same advisory reaches citizens. A judge can subscribe on Telegram and receive the live city alert during the demo." |
| 2:48-2:58 | Honest metrics close | Return to the main view or metrics strip. | "Honest metrics: attribution validates at 0.92 cosine against SAFAR, forecasts use CQR intervals, and TFT was evaluated and rejected when it did not beat the lean stack." |

## Hard Stops

- If the live site stalls, pause the recording attempt and reload; do not record the fallback banner.
- If Telegram is rate-limited, show the most recent received message and say the broadcast is server-throttled for safety.
- Do not claim WorldPop; say GPW v4.11 population.
- Do not claim the system auto-fines. It generates officer-reviewed recommendations and notice drafts.
