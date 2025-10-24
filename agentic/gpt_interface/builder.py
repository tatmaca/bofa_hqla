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
    """
    Construct a prompt string for an LLM that includes the portfolio summary
    and multiple scenarios of different families.

    Args:
        portfolio: Portfolio object (any composition of L1/L2A/L2B assets)
        scenarios: List of Scenario objects (IRR, Liquidity, Credit, etc.)

    Returns:
        A single string prompt ready to submit to an LLM.
    """
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

    prompt = (
        "You are a financial analyst AI. "
        "Provide recommended portfolio reallocations to optimize LCR, NSFR, and RWA, "
        "while respecting regulatory guardrails. "
        "Output strictly in JSON with the following keys:\n"
        "  - scenario_impact: textual summary of portfolio changes\n"
        "  - recommended_reallocation: list of dicts {asset, action, notional}\n"
        "  - rationale: justification of reallocation\n"
        "  - metadata: dictionary of LCR, NSFR, RWA before and after scenario\n\n"
        + "\n".join(blocks)
    )

    return prompt
