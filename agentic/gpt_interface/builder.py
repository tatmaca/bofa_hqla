# prompt/builder.py
import json
from typing import Any, Dict

from portfolio import Portfolio

from agentic.gpt_interface.portfolio_summary import summarize_portfolio
from hqla_risk_metrics.base import Scenario

RIGID_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "scenario_impact",
        "recommended_reallocation",
        "rationale",
        "metadata",
    ],
    "properties": {
        "scenario_impact": {"type": "string"},
        "recommended_reallocation": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["asset", "action", "notional"],
                "properties": {
                    "asset": {"type": "string"},
                    "action": {"type": "string", "enum": ["buy", "sell", "hold"]},
                    "notional": {"type": "number"},
                },
            },
        },
        "rationale": {"type": "string"},
        "metadata": {
            "type": "object",
            "required": [
                "lcr_before",
                "lcr_after_est",
                "nsfr_before",
                "nsfr_after_est",
                "rwa_before",
                "rwa_after_est",
            ],
        },
    },
}


def build_prompt(
    portfolio: Portfolio, scenario: Scenario, instructions: str = ""
) -> str:
    """
    Build deterministic prompt. Instructs LLM to respond ONLY with JSON matching schema.
    """
    summary_str = summarize_portfolio(portfolio, scenario_name=scenario.name)
    schema_snippet = json.dumps(RIGID_RESPONSE_SCHEMA, indent=2)

    prompt = f"""
You are a financial risk analyst AI that ALWAYS replies with a single JSON object and NOTHING ELSE.
Do not include explanation text. Do not wrap code fences. Respond using US decimal numbers.

Task:
1) Analyze the portfolio under the scenario: {scenario.name} (type: {scenario.scenario_type}, magnitude: {scenario.magnitude}, probability: {scenario.probability})
2) Provide a concise scenario impact summary string.
3) Provide a list named "recommended_reallocation" of trades to optimize LCR, NSFR, and RWA. Each item must be:
   - asset: exact asset name from the portfolio summary
   - action: one of "buy", "sell", "hold"
   - notional: positive number in same currency units as portfolio (do not include currency symbol)

4) Provide "rationale" string summarizing the logic.
5) Provide "metadata" with numeric estimates for LCR/NSFR/RWA before and after the proposed reallocations:
   - lcr_before, lcr_after_est, nsfr_before, nsfr_after_est, rwa_before, rwa_after_est

Portfolio summary (do not invent assets):
{summary_str}

Additional instructions:
{instructions}

RESPONSE SCHEMA (strict). Generate JSON exactly matching this schema:
{schema_snippet}

Respond now with only the JSON object.
"""
    # normalize whitespace
    return "\n".join(
        line.strip() for line in prompt.strip().splitlines() if line.strip()
    )
