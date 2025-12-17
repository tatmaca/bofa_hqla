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
    portfolio_file = uploadfile_from_csv_path("demo_csvs/representative_portfolio.csv")
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
            "Scenario": "Lingering Inflation + Fed on Hold",
            "Description": "Core PCE stalls at 2.8% and services inflation re-accelerates, forcing the Fed to keep rates at 5.50% into late 2025.",
            "Probability": 0.32,
            "Rationale": "Sticky shelter and wage prints keep financial conditions tight; curve bear-flattens as short rates stay anchored.",
            "ImpactChannels": [
            "Rates",
            "Curve",
            "Deposits"
            ],
            "Shocks": {
            "rates_parallel_bps": 35,
            "curve_2s10s_bps": -15,
            "ig_oas_bps": 10,
            "hy_oas_bps": 40,
            "mbs_basis_bps": 12,
            "deposit_outflow_pct": 3.0,
            "reg_change_note": "Fed pauses balance sheet normalization"
            },
            "MetricsDelta": {
            "dLCR_pct": -2.5,
            "dNSFR_pct": -1.4,
            "dNII_bps": 18,
            "dur_change_years": -0.2
            },
            "TradeList": [
            "Add $1.2bn front-end USTs via repo to rebuild HQLA buffer",
            "Trim $800mm 10y MBS to reduce convexity drag"
            ],
            "Assumptions": [
            "Money-market inflows plateau",
            "FDIC special assessment sunsets mid-year"
            ]
        },
        {
            "Scenario": "Bull Steepener on Growth Scare",
            "Description": "Payrolls roll over and small-business surveys collapse, forcing an early Fed cut sequence.",
            "Probability": 0.28,
            "Rationale": "Recession odds rise; front-end rallies ~80 bps while long-end lags on issuance risk.",
            "ImpactChannels": [
            "Rates",
            "Curve",
            "Credit"
            ],
            "Shocks": {
            "rates_parallel_bps": -45,
            "curve_2s10s_bps": 35,
            "ig_oas_bps": 25,
            "hy_oas_bps": 75,
            "mbs_basis_bps": 5,
            "deposit_outflow_pct": -1.0,
            "reg_change_note": "Counter-cyclical buffer paused"
            },
            "MetricsDelta": {
            "dLCR_pct": 3.0,
            "dNSFR_pct": 1.2,
            "dNII_bps": -22,
            "dur_change_years": 0.4
            },
            "TradeList": [
            "Rotate $600mm from bills into 5y UST to capture steepening",
            "Add $400mm TIPS as disinflation hedge"
            ],
            "Assumptions": [
            "Fiscal impulse fades",
            "Commercial real estate stress broadens"
            ]
        },
        {
            "Scenario": "Geopolitical Shock + Commodity Spike",
            "Description": "Energy supply disruption lifts Brent above $110, rekindling breakevens and widening MBS basis.",
            "Probability": 0.22,
            "Rationale": "Flight-to-quality meets higher inflation risk; curve bear-steepens and liquidity premiums widen.",
            "ImpactChannels": [
            "Commodity Prices",
            "Rates",
            "Credit",
            "Deposits"
            ],
            "Shocks": {
            "rates_parallel_bps": 20,
            "curve_2s10s_bps": 25,
            "ig_oas_bps": 30,
            "hy_oas_bps": 90,
            "mbs_basis_bps": 18,
            "deposit_outflow_pct": 4.5,
            "reg_change_note": "Treasury boosts bill issuance to fund SPR release"
            },
            "MetricsDelta": {
            "dLCR_pct": -3.7,
            "dNSFR_pct": -2.1,
            "dNII_bps": 24,
            "dur_change_years": -0.3
            },
            "TradeList": [
            "Increase HQLA cash buffer by $500mm via FHLB advances",
            "Short belly futures to hedge rate beta"
            ],
            "Assumptions": [
            "USD funding spreads widen 15 bps",
            "Retail deposits beta jumps 0.15"
            ]
        },
        {
            "Scenario": "Reg Relief / Capital Recalibration",
            "Description": "Agencies finalize Endgame tweaks that soften G-SIB surcharge and Level 2 caps for HQLA.",
            "Probability": 0.18,
            "Rationale": "Political compromise post-elections reduces capital drag; banks redeploy excess cash into spread assets.",
            "ImpactChannels": [
            "Regulatory",
            "Market Sentiment"
            ],
            "Shocks": {
            "rates_parallel_bps": 5,
            "curve_2s10s_bps": 5,
            "ig_oas_bps": -8,
            "hy_oas_bps": -20,
            "mbs_basis_bps": -7,
            "deposit_outflow_pct": -0.5,
            "reg_change_note": "TLAC calibration delayed; LIQ add-ons eased"
            },
            "MetricsDelta": {
            "dLCR_pct": 4.1,
            "dNSFR_pct": 3.3,
            "dNII_bps": 8,
            "dur_change_years": 0.1
            },
            "TradeList": [
            "Add $900mm Agency MBS down-in-credit",
            "Deploy $400mm to Level 2A corporates within cap"
            ],
            "Assumptions": [
            "Deposit runoff stabilizes",
            "Repo markets remain liquid"
            ]
        }
    ],
        "scenarioCurves": {
    "Lingering Inflation + Fed on Hold": [
        {"tenor": "1Y", "rate": 0.055},
        {"tenor": "2Y", "rate": 0.057},
        {"tenor": "3Y", "rate": 0.058},
        {"tenor": "5Y", "rate": 0.060},
        {"tenor": "7Y", "rate": 0.062},
        {"tenor": "10Y", "rate": 0.064}
    ],
    "Bull Steepener on Growth Scare": [
        {"tenor": "1Y", "rate": 0.050},
        {"tenor": "2Y", "rate": 0.052},
        {"tenor": "3Y", "rate": 0.054},
        {"tenor": "5Y", "rate": 0.056},
        {"tenor": "7Y", "rate": 0.058},
        {"tenor": "10Y", "rate": 0.060}
    ],
    "Geopolitical Shock + Commodity Spike": [
        {"tenor": "1Y", "rate": 0.060},
        {"tenor": "2Y", "rate": 0.062},
        {"tenor": "3Y", "rate": 0.064},
        {"tenor": "5Y", "rate": 0.067},
        {"tenor": "7Y", "rate": 0.070},
        {"tenor": "10Y", "rate": 0.073}
    ],
    "Reg Relief / Capital Recalibration": [
        {"tenor": "1Y", "rate": 0.045},
        {"tenor": "2Y", "rate": 0.046},
        {"tenor": "3Y", "rate": 0.047},
        {"tenor": "5Y", "rate": 0.049},
        {"tenor": "7Y", "rate": 0.051},
        {"tenor": "10Y", "rate": 0.053}
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

    if isinstance(response, dict):
        resp_dict = response
    else:
        resp_dict = json.loads(response.body.decode())

    print(json.dumps(resp_dict, indent=2))

    # ---------- Save final portfolio to CSV ----------
    final_portfolio = resp_dict.get("final_portfolio")

    if final_portfolio:
        final_df = pd.DataFrame(final_portfolio)
        final_df.to_csv("final_portfolio.csv", index=False)
        print("Saved final portfolio to output/final_portfolio.csv")
    else:
        print("No final portfolio returned")

    # ---------- Save AI report ----------
    ai_report = resp_dict.get("ai_report")

    if ai_report:
        with open("ai_report.txt", "w") as f:
            f.write(ai_report)
        print("Saved AI report to output/ai_report.txt")
    else:
        print("No AI report returned")

# ---------- Run ---------- 
if __name__ == "__main__":
    asyncio.run(main())
