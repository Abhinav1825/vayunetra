"""E2 — train + validate the dense-coverage models (CPU here, GPU on Kaggle/Colab).

    python -m ml.coverage.train            # train both, print held-out metrics
    python -m ml.coverage.train --save     # also save artifacts to ml/coverage/artifacts/

Reports the honest numbers for Validation #7 (AOD→PM2.5 RMSE; downscaling skill vs
plain interpolation). The heavy GPU run is the companion Colab/Kaggle notebook;
this module keeps the code path identical so results are reproducible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import aod_pm25, downscale

ARTIFACTS = Path(__file__).parent / "artifacts"


def main() -> dict:
    ap = argparse.ArgumentParser(description="Train E2 dense-coverage models")
    ap.add_argument("--save", action="store_true", help="persist trained artifacts")
    args = ap.parse_args()

    aod_model, aod_metrics = aod_pm25.train_and_validate()
    ds_model, ds_metrics = downscale.train_and_validate()

    report = {"aod_pm25": aod_metrics.as_dict(), "downscale": ds_metrics}
    print(json.dumps(report, indent=2))

    if args.save:
        ARTIFACTS.mkdir(exist_ok=True)
        import joblib
        import torch

        joblib.dump(aod_model, ARTIFACTS / "aod_pm25_lgbm.joblib")
        torch.save(ds_model.state_dict(), ARTIFACTS / "downscale_cnn.pt")
        (ARTIFACTS / "metrics.json").write_text(json.dumps(report, indent=2))
        print(f"saved artifacts -> {ARTIFACTS}")

    return report


if __name__ == "__main__":
    main()
