# pipeline/main.py
import os
import sys

# Ensure agentic/src is on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "agentic/src")))

from assets import Level1Asset, Level2AAsset, Level2BAsset
from portfolio import Portfolio

from agentic.gpt_interface.builder import build_prompt
from hqla_risk_metrics.scenario_shocks import YCSteepening


def run_demo():
    # build a flexible portfolio
    p = Portfolio(
        total_expected_outflows_30d=120_000_000,
        required_stable_funding=150_000_000,
    )
    p.add_asset(Level1Asset("Cash", 100_000_000))
    p.add_asset(Level1Asset("UST_10Y", 50_000_000))
    p.add_asset(Level2AAsset("Covered_Bond", 30_000_000))
    p.add_asset(Level2BAsset("Corp_Bond", 20_000_000))

    # define a test scenario (could be replaced with liquidity, credit, etc.)
    scenario = YCSteepening(magnitude=0.05)

    # apply scenario
    p_scenario = scenario.apply(p)

    # build deterministic prompt (no LLM call)
    prompt = build_prompt(p_scenario, scenario)

    print("\n=== GENERATED QUERY PROMPT ===\n")
    print(prompt)
    print("\n=== END OF PROMPT ===\n")


if __name__ == "__main__":
    run_demo()
