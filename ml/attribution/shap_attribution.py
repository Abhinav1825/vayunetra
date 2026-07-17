"""GBM + SHAP source apportionment (Attribution v2).  PLAN §2A/§3A; ARCH §9.1.

Method (standard explainable-ML apportionment):
1. Train LightGBM to predict PM2.5 from *source-marker* + condition features
   (never PM2.5 itself or its lags — that would leak the target).
2. SHAP TreeExplainer gives each feature's signed contribution per sample.
3. Positive SHAP mass is grouped by marker→source mapping (NO2/CO/sat-NO2 →
   traffic, SO2 → industrial, PM10/PM2.5 ratio → construction dust, FIRMS fire
   → biomass, advected PM2.5 → transported) and normalised into shares.
   Met/calendar features explain *conditions*, not sources, so they are
   excluded from the apportionment mass (they still help the model fit).
4. Shares are blended with the chemical-signature priors (signatures.py) and
   confidence is calibrated from method agreement + model fit + sample depth.

Falls back to the signature priors automatically when a city's data is too
thin to train on (the runner handles that).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .signatures import CATEGORIES

# marker feature -> source category (the apportionment mass)
# Known limitation: pm10_pm25_ratio has PM2.5 in its denominator, so it softly
# encodes the target (PM10 itself is NOT a feature, so the target is not
# recoverable). Coarse-fraction markers are standard receptor-model practice;
# the signature-prior blend further dampens any circularity.
SOURCE_MARKERS: dict[str, str] = {
    "no2": "traffic",
    "co": "traffic",
    "no2_sat": "traffic",
    "so2": "industrial",
    "pm10_pm25_ratio": "construction_dust",
    "fire": "biomass_burning",
    "advected_pm25": "transported",
}

# condition features: help the fit, excluded from source mass
CONDITION_FEATURES = [
    "o3", "temp", "rh", "precip", "wind_u", "wind_v", "blh",
    "wind_speed", "ventilation", "hour", "dow",
]

MIN_SAMPLES = 400          # below this, hybrid isn't trustworthy -> signature fallback
MIN_HOLDOUT_R2 = 0.15      # a model with no out-of-sample skill must not assign ML blame
OTHER_FLOOR = 0.05         # small unexplained-mass floor so shares never claim 100% certainty
BLEND_WEIGHT = 0.6         # hybrid share = 0.6 * shap + 0.4 * signature prior
RECENT_HOURS = 72          # apportion over the trailing window per cell
METHOD_VERSION = "hybrid-gbm-shap-v2"


@dataclass(frozen=True)
class CellApportionment:
    shares: dict[str, float]
    confidence: float
    shap_drivers: list[dict]   # top drivers: {feature, source, contribution}
    n_samples: int


def build_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    """Measurements -> per (cell, ts) wide table with markers + conditions.

    Reuses the forecast feature pipeline (met broadcast, calendar, advection)
    and joins the attribution-only markers (fire, satellite NO2) onto it.
    """
    from ml.forecast.features import build_feature_table

    wide = build_feature_table(long_df)

    extra = long_df[long_df["variable"].isin(["fire", "no2_sat"])].copy()
    if not extra.empty:
        extra["ts"] = pd.to_datetime(extra["ts"], utc=True).dt.floor("h")
        piv = extra.pivot_table(index=["city_id", "h3_cell", "ts"], columns="variable", values="value").reset_index()
        wide = wide.merge(piv, on=["city_id", "h3_cell", "ts"], how="left")
    for col in ("fire", "no2_sat"):
        if col not in wide.columns:
            wide[col] = 0.0
    wide[["fire", "no2_sat"]] = wide[["fire", "no2_sat"]].fillna(0.0)

    wide["pm10_pm25_ratio"] = np.where(wide.get("pm25", 0) > 0, wide.get("pm10", np.nan) / wide["pm25"], np.nan)
    return wide


def _feature_frame(wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """(X, y, feature_cols) for the apportionment model — no target leakage."""
    markers = [f for f in SOURCE_MARKERS if f in wide.columns]
    conditions = [f for f in CONDITION_FEATURES if f in wide.columns]
    calendar = [c for c in wide.columns if c.startswith(("is_", "season_", "stubble", "diwali", "winter"))]
    cols = markers + conditions + calendar
    usable = wide.dropna(subset=["pm25"])
    return usable[cols], usable["pm25"], cols


def _fit_gbm(X: pd.DataFrame, y: pd.Series):
    """LightGBM fit + honest holdout R² (time-ordered 80/20 split)."""
    import lightgbm as lgb
    from sklearn.metrics import r2_score

    split = int(len(X) * 0.8)
    model = lgb.LGBMRegressor(
        n_estimators=300, learning_rate=0.05, num_leaves=31,
        min_child_samples=20, verbosity=-1,
    )
    model.fit(X.iloc[:split], y.iloc[:split])
    r2 = float(r2_score(y.iloc[split:], model.predict(X.iloc[split:]))) if len(X) - split > 20 else 0.0
    model.fit(X, y)  # refit on all data for the final explanations
    return model, max(0.0, r2)


class _LinearModel:
    def __init__(self, cols: list[str], means: pd.Series, coef: np.ndarray):
        self.cols = cols
        self.means = means
        self.coef = coef

    def design(self, X: pd.DataFrame) -> np.ndarray:
        clean = X[self.cols].fillna(self.means).fillna(0.0)
        return np.column_stack([np.ones(len(clean)), clean.to_numpy(dtype=float)])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.design(X) @ self.coef


def _r2_np(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2)) or 1.0
    return 1.0 - ss_res / ss_tot


def _fit_linear(X: pd.DataFrame, y: pd.Series) -> tuple[_LinearModel, float]:
    """Numpy-only fallback for CI/lean envs when LightGBM/SHAP/sklearn break."""
    split = int(len(X) * 0.8)
    means = X.iloc[:split].median(numeric_only=True)
    train_model = _LinearModel(list(X.columns), means, np.zeros(len(X.columns) + 1))
    design = train_model.design(X.iloc[:split])
    coef, *_ = np.linalg.lstsq(design, y.iloc[:split].to_numpy(dtype=float), rcond=None)
    train_model.coef = coef
    holdout = X.iloc[split:]
    r2 = _r2_np(y.iloc[split:].to_numpy(dtype=float), train_model.predict(holdout)) if len(holdout) > 20 else 0.0

    means_all = X.median(numeric_only=True)
    model = _LinearModel(list(X.columns), means_all, np.zeros(len(X.columns) + 1))
    coef_all, *_ = np.linalg.lstsq(model.design(X), y.to_numpy(dtype=float), rcond=None)
    model.coef = coef_all
    return model, max(0.0, float(r2))


def _linear_shares(
    model: _LinearModel, grp: pd.DataFrame, cols: list[str], observed_frac: dict[str, float]
) -> tuple[dict[str, float], list[dict]]:
    mass = {c: 0.0 for c in CATEGORIES}
    per_feature: dict[str, float] = {}
    for idx, col in enumerate(cols, start=1):
        source = SOURCE_MARKERS.get(col)
        if source is None or observed_frac.get(col, 1.0) < MIN_MARKER_COVERAGE:
            continue
        spread = float(grp[col].fillna(model.means.get(col, 0.0)).std()) or 0.0
        contrib = abs(float(model.coef[idx])) * spread
        per_feature[col] = contrib
        mass[source] += contrib

    total = sum(mass.values())
    if total <= 0:
        return {}, []
    shares = {c: (1 - OTHER_FLOOR) * mass[c] / total for c in CATEGORIES if c != "other"}
    shares["other"] = OTHER_FLOOR
    drivers = [
        {"feature": f, "source": SOURCE_MARKERS[f], "contribution": round(v, 3)}
        for f, v in sorted(per_feature.items(), key=lambda kv: -kv[1])[:3]
        if v > 0
    ]
    return {k: round(v, 4) for k, v in shares.items()}, drivers


MIN_MARKER_COVERAGE = 0.3  # a marker must be observed in ≥30% of the window's rows


def _shap_shares(
    shap_vals: np.ndarray, cols: list[str], observed_frac: dict[str, float] | None = None
) -> tuple[dict[str, float], list[dict]]:
    """Positive SHAP mass of *observed* marker groups -> shares + top drivers.

    Unobserved markers are excluded: LightGBM's missing-value branch still
    produces SHAP mass, which would assign identical phantom blame (e.g.
    "industrial") to every cell that simply lacks an SO2 sensor.
    """
    observed_frac = observed_frac or {}
    mass = {c: 0.0 for c in CATEGORIES}
    per_feature: dict[str, float] = {}
    for j, col in enumerate(cols):
        source = SOURCE_MARKERS.get(col)
        if source is None:
            continue
        if observed_frac.get(col, 1.0) < MIN_MARKER_COVERAGE:
            continue  # marker not actually measured here -> no blame from it
        contrib = float(np.clip(shap_vals[:, j], 0, None).mean())
        per_feature[col] = contrib
        mass[source] += contrib

    total = sum(mass.values())
    if total <= 0:
        return {}, []
    shares = {c: (1 - OTHER_FLOOR) * mass[c] / total for c in CATEGORIES if c != "other"}
    shares["other"] = OTHER_FLOOR

    drivers = [
        {"feature": f, "source": SOURCE_MARKERS[f], "contribution": round(v, 3)}
        for f, v in sorted(per_feature.items(), key=lambda kv: -kv[1])[:3]
        if v > 0
    ]
    return {k: round(v, 4) for k, v in shares.items()}, drivers


def _blend(shap_s: dict[str, float], sig_s: dict[str, float], w: float = BLEND_WEIGHT) -> dict[str, float]:
    blended = {c: w * shap_s.get(c, 0.0) + (1 - w) * sig_s.get(c, 0.0) for c in CATEGORIES}
    total = sum(blended.values()) or 1.0
    return {c: round(v / total, 4) for c, v in blended.items()}


def _calibrated_confidence(
    shap_s: dict[str, float], sig_s: dict[str, float], r2: float, n_cell: int
) -> float:
    """Agreement between independent methods + model fit + sample depth -> [0.30, 0.95]."""
    l1 = sum(abs(shap_s.get(c, 0.0) - sig_s.get(c, 0.0)) for c in CATEGORIES)
    agreement = max(0.0, 1.0 - 0.5 * l1)           # 1 = identical share vectors
    depth = min(1.0, n_cell / RECENT_HOURS)         # full trailing window available?
    conf = 0.30 + 0.35 * agreement + 0.20 * r2 + 0.10 * depth
    return round(float(np.clip(conf, 0.30, 0.95)), 3)


def apportion_cells(
    wide: pd.DataFrame, sig_by_cell: dict[str, dict[str, float]]
) -> tuple[dict[str, CellApportionment], float]:
    """Per-cell hybrid apportionment over the trailing window.

    Returns ({h3_cell: CellApportionment}, holdout_r2). Raises ValueError when
    the city's data is too thin — callers fall back to signature priors.
    """
    X, y, cols = _feature_frame(wide)
    if len(X) < MIN_SAMPLES:
        raise ValueError(f"too few samples for GBM apportionment ({len(X)} < {MIN_SAMPLES})")

    use_linear = False
    try:
        import shap

        model, r2 = _fit_gbm(X, y)
        explainer = shap.TreeExplainer(model)
    except Exception:
        model, r2 = _fit_linear(X, y)
        explainer = None
        use_linear = True
    if r2 < MIN_HOLDOUT_R2:
        # SHAP from a model that can't predict out-of-sample is noise dressed
        # as ML — keep the transparent chemistry priors instead.
        raise ValueError(f"holdout R2 too low for trustworthy apportionment ({r2:.2f} < {MIN_HOLDOUT_R2})")

    cutoff = wide["ts"].max() - pd.Timedelta(hours=RECENT_HOURS)
    recent = wide.dropna(subset=["pm25"])
    recent = recent[recent["ts"] >= cutoff]

    out: dict[str, CellApportionment] = {}
    for cell, grp in recent.groupby("h3_cell"):
        observed = {c: float(grp[c].notna().mean()) for c in cols if c in SOURCE_MARKERS}
        if use_linear:
            shap_s, drivers = _linear_shares(model, grp, cols, observed)
        else:
            shap_vals = explainer.shap_values(grp[cols])
            shap_s, drivers = _shap_shares(np.asarray(shap_vals), cols, observed)
        if not shap_s:
            continue  # no observed markers -> keep the transparent signature row
        sig_s = sig_by_cell.get(cell, {})
        out[str(cell)] = CellApportionment(
            shares=_blend(shap_s, sig_s),
            confidence=_calibrated_confidence(shap_s, sig_s, r2, len(grp)),
            shap_drivers=drivers,
            n_samples=len(grp),
        )
    if not out:
        raise ValueError("no cells had recent data to apportion")
    return out, r2
