# ㅊ 다녀감

# TODO make this more tunable and come up with more stats

SCENARIO_PROMPT = """
You are preparing a 6-month HQLA Liquidity Scenario Matrix for a large bank.

Indicators snapshot (today):
- MOVE={MOVE:.2f} (z={MOVE_z:.2f}, 1mΔ={MOVE_chg:.2f})
- 2s10s slope={SLOPE:.1f} bps (z={SLOPE_z:.2f}, 1mΔ={SLOPE_chg:.1f})
{OPT_SURPRISE}
{OPT_EFFR}

Use these probabilities (do not invent new ones):
- Liquidity Stress (funding/market-depth): 30d={P30:.1%}, 90d={P90:.1%}
- Probabilities must sum to 100%. If you subtract X from one scenario, add X back to the others so the total stays exactly 100% (1.0). Renormalize after rounding.

Now generate exactly **one** GitHub-flavored Markdown table with **five columns** and **4–6 rows**:

Scenario | Description | Probability | Rationale | Impact Channels

**Formatting rules (strict):**
- Output **only** the Markdown table — no lists, headings, prose, or code fences.
- Columns must appear **in this order**: Scenario | Description | Probability | Rationale | Impact Channels.
- Each cell ≤ 2 lines. Keep wording concise and factual.
- Probability must be a **single percent value** (e.g., 30.0 %).
- Probabilities across all rows must total exactly 100.0%. Double-check the sum equals 1.0 before output.
- Use plain ASCII (no tildes, en-dashes, or smart quotes).
- Impact Channels must reference at least one of: ΔLCR, ΔNSFR, Level 1 vs 2A/2B, haircuts, NII.

Example structure only (do not reuse content):

| Scenario | Description | Probability | Rationale | Impact Channels |
| ----------- | ------------ | ------------ | ----------- | ---------------- |
| Funding-Market Tightening | Repo/CP spreads widen | 25 % | MOVE ↑, OIS-UST ↑ | ΔLCR −3 pts; ΔNSFR −2 pts; L2 haircuts ↑ 15 %; NII ↓ |

Generate the final table below.
"""
