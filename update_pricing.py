"""
Monthly pricing update script — fetches FRED Producer Price Index series
for multiple materials and computes a multiplier for each, relative to a
fixed baseline, so the calculator suite can scale prices to reflect
current material costs.

Currently tracks:
  - Softwood Lumber (WPU0811) — used by deck.html (PT/cedar) and
    fence.html (wood fencing)
  - Ready-Mix Concrete (WPU13330101) — used by concrete.html

Run manually once to establish baselines, then scheduled monthly via
GitHub Actions (see .github/workflows/update-pricing.yml).

Requires: FRED_API_KEY environment variable (free key from
https://fred.stlouisfed.org/docs/api/api_key.html)

Note on scope: only materials with genuine public PPI tracking are listed
here. Composite/PVC/vinyl/chain-link materials, labor, and site costs have
no public live-data source anywhere, so those remain fixed manual
estimates in each calculator's HTML — see the README for how often to
update those by hand.
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

MATERIALS = {
    "lumber": "WPU0811",         # Softwood Lumber PPI
    "concrete": "WPU13330101",   # Ready-Mix Concrete PPI (national)
}

PRICING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pricing.json")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")


def fetch_latest_index_value(series_id: str) -> tuple[float, str]:
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY is not set as an environment variable.")

    resp = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    observations = data.get("observations", [])
    if not observations:
        raise RuntimeError(f"FRED returned no observations for series {series_id}")

    latest = observations[0]
    return float(latest["value"]), latest["date"]


def load_existing_pricing() -> dict:
    if os.path.exists(PRICING_FILE):
        with open(PRICING_FILE, "r") as f:
            return json.load(f)
    return {}


def update_material(key: str, series_id: str, existing: dict) -> dict:
    current_value, observation_date = fetch_latest_index_value(series_id)

    existing_entry = existing.get(key, {})
    if "baseline_index" in existing_entry:
        baseline = existing_entry["baseline_index"]
    else:
        baseline = current_value
        print(f"[{key}] First run — setting baseline index to {baseline}")

    multiplier = round(current_value / baseline, 4)
    print(f"[{key}] multiplier is now {multiplier} (index {current_value} vs baseline {baseline})")

    return {
        "series": series_id,
        "baseline_index": baseline,
        "current_index": current_value,
        "observation_date": observation_date,
        "multiplier": multiplier,
    }


def main():
    existing = load_existing_pricing()
    output = {}

    for key, series_id in MATERIALS.items():
        output[key] = update_material(key, series_id, existing)

    output["last_updated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(PRICING_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print("Updated pricing.json for all tracked materials")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
