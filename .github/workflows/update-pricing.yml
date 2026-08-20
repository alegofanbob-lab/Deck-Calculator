"""
Monthly pricing update script — fetches the FRED softwood lumber Producer
Price Index (series WPU0811) and computes a multiplier relative to a fixed
baseline, so the deck calculator can scale its pressure-treated and cedar
price ranges to reflect current lumber costs.

Run manually once to establish, then scheduled monthly via GitHub Actions
(see .github/workflows/update-pricing.yml).

Requires: FRED_API_KEY environment variable (free key from
https://fred.stlouisfed.org/docs/api/api_key.html)

Note on scope: this only tracks softwood lumber (used for pressure-treated
and cedar decking). Composite, PVC, labor, and footing costs have no
public live-data source anywhere, so those remain fixed manual estimates —
see the README for how often to update those by hand.
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

SERIES_ID = "WPU0811"  # Softwood Lumber PPI
PRICING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pricing.json")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")


def fetch_latest_index_value() -> tuple[float, str]:
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY is not set as an environment variable.")

    resp = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": SERIES_ID,
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
        raise RuntimeError("FRED returned no observations for series " + SERIES_ID)

    latest = observations[0]
    return float(latest["value"]), latest["date"]


def load_existing_pricing() -> dict:
    if os.path.exists(PRICING_FILE):
        with open(PRICING_FILE, "r") as f:
            return json.load(f)
    return {}


def main():
    current_value, observation_date = fetch_latest_index_value()
    existing = load_existing_pricing()

    if "baseline_index" in existing:
        baseline = existing["baseline_index"]
    else:
        # First run ever: this becomes the fixed reference point.
        # All future multipliers are relative to this value.
        baseline = current_value
        print(f"First run — setting baseline index to {baseline}")

    multiplier = round(current_value / baseline, 4)

    output = {
        "series": SERIES_ID,
        "baseline_index": baseline,
        "current_index": current_value,
        "observation_date": observation_date,
        "multiplier": multiplier,
        "last_updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open(PRICING_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Updated pricing.json — multiplier is now {multiplier} (index {current_value} vs baseline {baseline})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
