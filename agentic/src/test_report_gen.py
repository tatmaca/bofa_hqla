import asyncio
import pandas as pd
from io import BytesIO
from fastapi import UploadFile
from fastapi.requests import Request
import json
import QuantLib as ql

# Set the evaluation date to a future date beyond all coupon/fixing dates
ql.Settings.instance().evaluationDate = ql.Date(15, 12, 2025)  # Dec 15, 2025

# Import your API functions and globals
from api_server import (
    upload_portfolio,
    upload_yield_curve,
    optimize_scenarios,
    portfolio,
    base_curve_handle,
)

# ---------- Mock Request for JSON payload ----------
class MockRequest:
    def __init__(self, payload: dict):
        self._payload = payload

    async def json(self):
        return self._payload

# ---------- Helper to create UploadFile from CSV ----------
def uploadfile_from_csv_path(path: str, filename: str = None):
    filename = filename or path.split("/")[-1]
    with open(path, "rb") as f:
        return UploadFile(filename=filename, file=BytesIO(f.read()))

# ---------- Test script ----------
async def main():
    # 1. Upload portfolio
    portfolio_file = uploadfile_from_csv_path("demo_csvs/simulated_portfolio_2.csv")
    portfolio_resp = await upload_portfolio(portfolio_file)
    print("Portfolio upload response:", portfolio_resp)

    # 2. Upload yield curve
    yc_file = uploadfile_from_csv_path("demo_csvs/test_yc2.csv")
    yc_resp = await upload_yield_curve(yc_file)
    print("Yield curve upload response:", yc_resp)

    # 3. Build scenario payload
    scenario_payload = {
        "scenarioMatrix": [
            {
                "Scenario": "Upside Shock",
                "Description": "Rates drop by 25bps",
                "Probability": 0.3,
                "Rationale": "Economic slowdown",
                "ImpactChannels": "Rates, LCR",
                "TradeList": [],
                "Shocks": {"move": -25, "yield_curve": "parallel_shift"},
                "MetricsDelta": {"LCR": 5}
            },
            {
                "Scenario": "Downside Shock",
                "Description": "Rates rise by 25bps",
                "Probability": 0.7,
                "Rationale": "Inflation spike",
                "ImpactChannels": "Rates, LCR",
                "TradeList": [],
                "Shocks": {"move": 25, "yield_curve": "parallel_shift"},
                "MetricsDelta": {"LCR": -5}
            }
        ],
        "scenarioCurves": {
            "Upside Shock": [
                {"tenor": "1Y", "rate": 0.045},
                {"tenor": "2Y", "rate": 0.046},
                {"tenor": "3Y", "rate": 0.047},
                {"tenor": "5Y", "rate": 0.048},
                {"tenor": "7Y", "rate": 0.049},
                {"tenor": "10Y", "rate": 0.050}
            ],
            "Downside Shock": [
                {"tenor": "1Y", "rate": 0.055},
                {"tenor": "2Y", "rate": 0.056},
                {"tenor": "3Y", "rate": 0.057},
                {"tenor": "5Y", "rate": 0.058},
                {"tenor": "7Y", "rate": 0.059},
                {"tenor": "10Y", "rate": 0.060}
            ]
        },
        "combineMode": "probability_weighted",
        "optimizationMethod": "mean_lexicographic",
        "netCashOutflow": 1_000_000_000
    }

    # 4. Run optimization
    response = await optimize_scenarios(MockRequest(scenario_payload))
    print("\nOptimization response summary:")
    if isinstance(response, dict):
        print("Status:", response.get("status"))
        print("Total allocated:", response.get("summary_metrics", {}).get("total_allocated"))
        print("Combination mode:", response.get("combination_mode"))
    else:
        print(response)

    resp_dict = json.loads(response.body.decode())
    print(json.dumps(resp_dict, indent=2)) 

# ---------- Run ---------- 
if __name__ == "__main__":
    asyncio.run(main())
