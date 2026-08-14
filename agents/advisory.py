"""Agent 4 - Citizen Health Risk Advisory (Sejal).

Numbers come from forecasts and vulnerability layers; text is templated and localized.
The LLM can polish translations later, but Stage 1 has deterministic output that is safe
for DEMO_MODE, Telegram, IVR, and public-display surfaces.
"""
from __future__ import annotations

from datetime import datetime, timezone

RISK_ORDER = ["good", "satisfactory", "moderate", "poor", "very_poor", "severe"]
CHANNELS = ("pwa", "telegram", "ivr", "display")

BREAKPOINTS_PM25 = [
    (30, "good"),
    (60, "satisfactory"),
    (90, "moderate"),
    (120, "poor"),
    (250, "very_poor"),
    (10_000, "severe"),
]

<<<<<<< HEAD
# Native scripts (Devanagari / Kannada), deliberately short and formulaic so
# the templates stay unambiguous. Still worth a native speaker's read-through.
=======
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
LANG_LABEL = {
    "en": {
        "very_poor": "very poor",
        "poor": "poor",
        "moderate": "moderate",
        "severe": "severe",
        "action": "Keep outdoor activity short, use an N95 mask, and move heavy work outside the peak window.",
    },
    "hi": {
<<<<<<< HEAD
        "very_poor": "बहुत ख़राब",
        "poor": "ख़राब",
        "moderate": "मध्यम",
        "severe": "गंभीर",
        "action": "बाहर की गतिविधि कम रखें, N95 मास्क पहनें, और भारी काम पीक समय के बाद करें.",
    },
    "kn": {
        "very_poor": "ತುಂಬಾ ಕಳಪೆ",
        "poor": "ಕಳಪೆ",
        "moderate": "ಮಧ್ಯಮ",
        "severe": "ತೀವ್ರ",
        "action": "ಹೊರಗಿನ ಚಟುವಟಿಕೆ ಕಡಿಮೆ ಮಾಡಿ, N95 ಮಾಸ್ಕ್ ಬಳಸಿ, ಮತ್ತು ಭಾರೀ ಕೆಲಸವನ್ನು ಪೀಕ್ ಸಮಯದ ನಂತರ ಮಾಡಿ.",
    },
    "mr": {
        "very_poor": "खूप खराब",
        "poor": "खराब",
        "moderate": "मध्यम",
        "severe": "गंभीर",
        "action": "बाहेरील हालचाल कमी ठेवा, N95 मास्क वापरा, आणि जड काम पीक वेळेनंतर करा.",
=======
        "very_poor": "bahut kharab",
        "poor": "kharab",
        "moderate": "madhyam",
        "severe": "gambhir",
        "action": "Bahar ki gatividhi kam rakhein, N95 mask pehnein, aur bhari kaam peak samay ke baad karein.",
    },
    "kn": {
        "very_poor": "tumba kalape",
        "poor": "kalape",
        "moderate": "madhyama",
        "severe": "teevra",
        "action": "Horagina chatuvatike kadime madi, N95 mask balasi, mattu bhari kelasa peak samayada horage madi.",
    },
    "mr": {
        "very_poor": "khup kharab",
        "poor": "kharab",
        "moderate": "madhyam",
        "severe": "gambhir",
        "action": "Baherchi halchal kami theva, N95 mask vapra, ani jad kaam peak veles baher kara.",
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
    },
}


def risk_tier(pm25: float) -> str:
    for limit, tier in BREAKPOINTS_PM25:
        if pm25 <= limit:
            return tier
    return "severe"


def vulnerability_adjusted_tier(base_tier: str, vulnerability_index: float) -> str:
    idx = RISK_ORDER.index(base_tier)
    if vulnerability_index >= 0.75:
        idx += 1
    elif vulnerability_index >= 0.55 and base_tier in {"moderate", "poor"}:
        idx += 1
    return RISK_ORDER[min(idx, len(RISK_ORDER) - 1)]


def audience_segment(vulnerability: dict) -> str:
    if vulnerability.get("outdoor_worker_share", 0) >= 0.28:
        return "outdoor_worker"
    if vulnerability.get("schools", 0) >= 4:
        return "school"
    if vulnerability.get("hospitals", 0) >= 2:
        return "respiratory"
    return "general"


def render_message(city_name: str, ward_id: str, tier: str, horizon_h: int, lang: str) -> str:
    labels = LANG_LABEL.get(lang, LANG_LABEL["en"])
    tier_label = labels.get(tier, tier.replace("_", " "))
    action = labels["action"]
    if lang == "en":
        return f"{city_name} {ward_id}: air is forecast {tier_label} in +{horizon_h}h. {action}"
    if lang == "hi":
<<<<<<< HEAD
        return f"{city_name} {ward_id}: अगले {horizon_h} घंटों में हवा {tier_label} रहने का अनुमान है. {action}"
    if lang == "kn":
        return f"{city_name} {ward_id}: ಮುಂದಿನ {horizon_h} ಗಂಟೆಗಳಲ್ಲಿ ಗಾಳಿಯ ಗುಣಮಟ್ಟ {tier_label} ಇರಲಿದೆ ಎಂದು ಅಂದಾಜಿಸಲಾಗಿದೆ. {action}"
    if lang == "mr":
        return f"{city_name} {ward_id}: पुढील {horizon_h} तासांत हवा {tier_label} राहण्याचा अंदाज आहे. {action}"
=======
        return f"{city_name} {ward_id}: +{horizon_h}h me hawa {tier_label} rahegi. {action}"
    if lang == "kn":
        return f"{city_name} {ward_id}: +{horizon_h}h nalli gali {tier_label} agiruttade. {action}"
    if lang == "mr":
        return f"{city_name} {ward_id}: +{horizon_h}h madhe hava {tier_label} asel. {action}"
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
    return f"{city_name} {ward_id}: air is forecast {tier_label} in +{horizon_h}h. {action}"


def build_advisories(
    city_id: str,
    city_name: str,
    forecasts: list[dict],
    vulnerability_rows: list[dict],
    languages: list[str],
    horizon_h: int = 24,
    issued_at: str | None = None,
) -> list[dict]:
    issued_at = issued_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    values = [float(r["value"]) for r in forecasts if int(r.get("horizon_h", horizon_h)) == horizon_h]
    city_pm25 = sum(values) / len(values) if values else 95.0

    advisories: list[dict] = []
    for vuln in vulnerability_rows:
        base = risk_tier(city_pm25)
        tier = vulnerability_adjusted_tier(base, float(vuln.get("vulnerability_index", 0)))
        segment = audience_segment(vuln)
        for lang in languages:
            for channel in CHANNELS:
                advisories.append({
                    "city_id": city_id,
                    "ward_id": vuln["ward_id"],
                    "issued_at": issued_at,
                    "horizon_h": horizon_h,
                    "risk_tier": tier,
                    "audience_segment": segment,
                    "language": lang,
                    "channel": channel,
                    "message": render_message(city_name, vuln["ward_id"], tier, horizon_h, lang),
                })
    return advisories
