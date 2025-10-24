"""
main.py
--------
Driver script for building HQLA portfolios, applying scenarios, and generating GPT prompts.

Author: Togay Atmaca
Updated: 2025-10-24
"""

import os
import sys
from datetime import datetime

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


def wrap_irr_scenario(irr_obj) -> Scenario:
    """
    Convert a YCSteepening / YCFlattening object into a Scenario dataclass.
    """
    return Scenario(
        name=irr_obj.name,
        family=ScenarioFamily.IRR,
        description=f"{irr_obj.name} scenario with magnitude {irr_obj.magnitude}",
        rationale="Interest rate move applied to long-duration assets",
        probability=Probability(value=irr_obj.probability),
        impact=ImpactChannels(
            delta_LCR_bps=None,
            delta_NSFR_bps=None,
            delta_RWA_pct=None,
            delta_NII_bps=None,
        ),
        assumptions=f"Magnitude: {irr_obj.magnitude}",
        sources=["Internal IRR model"],
    )


def run_demo():
    # Build sample portfolio
    portfolio = Portfolio(
        total_expected_outflows_30d=120_000_000,
        required_stable_funding=150_000_000,
    )
    portfolio.add_asset(Level1Asset("Cash", 100_000_000))
    portfolio.add_asset(Level1Asset("UST_10Y", 50_000_000))
    portfolio.add_asset(Level2AAsset("Covered_Bond", 30_000_000))
    portfolio.add_asset(Level2BAsset("Corp_Bond", 20_000_000))

    # Create IRR scenarios
    irr_scenarios = [YCSteepening(), YCFlattening()]
    all_scenarios = [wrap_irr_scenario(s) for s in irr_scenarios]

    # Apply first scenario to portfolio (example)
    p_scenario = irr_scenarios[0].apply(portfolio)

    # Build prompt string
    prompt = build_prompt(portfolio, all_scenarios)

    print("\n=== GENERATED GPT PROMPT ===\n")
    print(prompt)


def main():
    run_demo()


if __name__ == "__main__":
    main()
