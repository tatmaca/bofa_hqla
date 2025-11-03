"""
builder.py
------------
Builds LLM prompts for HQLA portfolio scenarios (IRR, liquidity, credit, etc.)
in a structured and reproducible JSON format.

Author: Togay Atmaca (updated)
Created: 2025-10-24
"""

from typing import List

from agentic.gpt_interface.portfolio_summary import summarize_portfolio
from agentic.src.portfolio import Portfolio
from scenario_gen.common.scenario import Scenario


def build_prompt(portfolio: Portfolio, scenarios: List[Scenario]) -> str:
    summary_str = summarize_portfolio(portfolio)
    blocks = [f"Portfolio summary:\n```{summary_str}```\n"]

    for s in scenarios:
        row = s.to_matrix_row()
        blocks.append(
            f"Scenario Type: {s.family.value}\n"
            f"Scenario: {row['Scenario']}\n"
            f"Description: {row['Description']}\n"
            f"Probability: {row['Probability']}\n"
            f"Rationale: {row['Rationale']}\n"
            f"Impact Channels: {row['Impact Channels']}\n"
        )

    json_schema = """
JSON_SCHEMA = {
  "type": "object",
  "required": ["scenario_impact", "recommended_reallocation", "rationale", "metadata"],
  "properties": {
    "scenario_impact": {"type": "string"},
    "recommended_reallocation": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["asset", "action", "notional"],
        "properties": {
          "asset": {"type": "string"},
          "action": {"type": "string", "enum": ["buy", "sell"]},
          "notional": {"type": "number"}
        }
      }
    },
    "rationale": {"type": "string"},
    "metadata": {
      "type": "object",
      "required": ["before", "after"],
      "properties": {
        "before": {
          "type": "object",
          "required": ["LCR", "NSFR", "RWA"],
          "properties": {
            "LCR": {"type": "number"},
            "NSFR": {"type": "number"},
            "RWA": {"type": "number"}
          }
        },
        "after": {
          "type": "object",
          "required": ["LCR", "NSFR", "RWA"],
          "properties": {
            "LCR": {"type": "number"},
            "NSFR": {"type": "number"},
            "RWA": {"type": "number"}
          }
        }
      }
    }
  }
}
"""

    prompt = (
        "You are a financial analyst AI. "
        "Respond only with JSON. "
        "Follow the provided JSON_SCHEMA exactly. "
        "No commentary. No markdown. No underscores in numbers.\n\n"
        + json_schema
        + "\n\nScenario Data:\n"
        + "\n".join(blocks)
    )

    return prompt
