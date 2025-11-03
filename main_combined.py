"""
main.py
--------
Demo driver for HQLA scenario analysis.
Prints GPT prompt based on portfolio and multiple scenario types (IRR, Liquidity).

Author: Togay Atmaca
"""

import json
import os
import sys
from datetime import datetime

from openai import OpenAI

from agentic.gpt_interface.builder import build_prompt

# Ensure access to local src
sys.path.append(os.path.abspath("./agentic/src"))
sys.path.append(os.path.abspath("./hqla_risk_metrics"))
from assets import Level1Asset, Level2AAsset, Level2BAsset
from scenario_shocks import YCFlattening, YCSteepening

from agentic.src.portfolio import Portfolio
from scenario_gen.common.scenario import (
    ImpactChannels,
    Probability,
    Scenario,
    ScenarioFamily,
)
from scenario_gen.liquidity_risk.run import _format_prompt
from scenario_gen.liquidity_risk.run import main as liq_run


def demo_portfolio() -> Portfolio:
    p = Portfolio(
        total_expected_outflows_30d=120_000_000, required_stable_funding=150_000_000
    )
    p.add_asset(Level1Asset("Cash", 100_000_000))
    p.add_asset(Level1Asset("UST_10Y", 50_000_000))
    p.add_asset(Level2AAsset("Covered_Bond", 30_000_000))
    p.add_asset(Level2BAsset("Corp_Bond", 20_000_000))
    return p


def build_liquidity_scenario() -> Scenario:
    """Build a liquidity scenario using latest indicators."""
    import pandas as pd

    from scenario_gen.liquidity_risk.features import make_features
    from scenario_gen.liquidity_risk.load_data import load_indicators
    from scenario_gen.liquidity_risk.probs import composite_probs

    df = load_indicators()
    X = make_features(df)
    P = composite_probs(X)
    latest_X, latest_P = X.iloc[-1], P.iloc[-1]

    return Scenario(
        name="Liquidity Stress",
        family=ScenarioFamily.LIQUIDITY,
        description="Funding-market stress over 30-90 days",
        rationale="MOVE and 2s10s slope indicate near-term liquidity pressure",
        probability=Probability(value=latest_P["P90_liq_stress"]),
        impact=ImpactChannels(
            delta_LCR_bps=-200,
            delta_NSFR_bps=-150,
            hqla_mix_notes="Shift +10% to Level 1; haircuts on L2A/B +25%",
        ),
    )


CATEGORY_MAP = {
    "L1": Level1Asset,
    "L2A": Level2AAsset,
    "L2B": Level2BAsset,
}


def apply_recommended_reallocation(portfolio: Portfolio, model_response: str):
    data = json.loads(model_response)
    reallocs = data.get("recommended_reallocation", [])

    for r in reallocs:
        asset_name = r["asset"]
        action = r["action"]
        amount = r["notional"]

        asset = portfolio.get_asset(asset_name)

        if asset is None:
            raise ValueError(f"Unknown asset {asset_name}")

        if action == "sell":
            if asset.market_value < amount:
                raise ValueError(
                    f"Cannot sell {amount}. Only {asset.market_value} exists."
                )
            asset.market_value -= amount

        elif action == "buy":
            asset.market_value += amount

        else:
            raise ValueError(f"Unsupported action {action}")

    return portfolio


def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    portfolio = demo_portfolio()

    # Build IRR scenarios
    yc_steep = YCSteepening()
    yc_flat = YCFlattening()

    # Wrap IRR scenarios in Scenario dataclass for uniform handling
    irr_scenarios = []
    for yc in [yc_steep, yc_flat]:
        irr_scenarios.append(
            Scenario(
                name=yc.name,
                family=ScenarioFamily.IRR,
                description=f"{yc.name} scenario with magnitude {yc.magnitude}",
                rationale="Interest rate move applied to long-duration assets",
                probability=Probability(value=yc.probability),
                impact=ImpactChannels(),  # placeholder; could be computed via apply
            )
        )

    # Build liquidity scenario
    liq_scenario = build_liquidity_scenario()

    # Combine all scenarios
    all_scenarios = irr_scenarios + [liq_scenario]

    # Generate GPT prompt
    prompt = build_prompt(portfolio, all_scenarios)
    print("\n=== GENERATED GPT PROMPT ===\n")
    print(prompt)

    # ---- NEW: Send to API ----
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=1,
    )

    print("\n=== MODEL RESPONSE ===\n")
    print(response.choices[0].message.content)

    approve = input("Apply reallocation? (y/n): ").lower()
    if approve == "y":
        apply_recommended_reallocation(portfolio, response.choices[0].message.content)
        print("\nUpdated summary:", portfolio.summary())
    else:
        print("No changes made.")


if __name__ == "__main__":
    main()
