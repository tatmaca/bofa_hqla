
"""
credit_risk/prompt_template.py

LLM prompt template for a 5-column Scenario Matrix for Credit Risk.
ASCII-only; strict Markdown table output.
"""

SCENARIO_PROMPT = """
You are preparing a 6-month Credit Spread Risk Scenario Matrix for a large bank.

Indicators snapshot (today):
- IG OAS={IG_OAS:.1f} bp (z={IG_OAS_z:.2f}, 1mΔ={IG_OAS_chg:.1f})
- HY OAS={HY_OAS:.1f} bp (z={HY_OAS_z:.2f}, 1mΔ={HY_OAS_chg:.1f})
{OPT_VIX}
{OPT_MOVE}
{OPT_SLOPE}

Use these probabilities (do not invent new ones):
- Mild Credit Tightening: 30d={P30_mild:.1%}, 90d={P90_mild:.1%}
- Severe Credit Shock:    30d={P30_severe:.1%}, 90d={P90_severe:.1%}
- Spread Compression:     30d={P30_compress:.1%}, 90d={P90_compress:.1%}
- Probabilities must sum to 100%. If you subtract X from one scenario, add X back to the others so the total stays exactly 100% (1.0). Renormalize after rounding.

Now generate exactly one GitHub-flavored Markdown table with five columns and 4–6 rows:

Scenario | Description | Probability | Rationale | Impact Channels

Formatting rules (strict):
- Output only the Markdown table — no lists, headings, prose, or code fences.
- Columns must appear in this order: Scenario | Description | Probability | Rationale | Impact Channels.
- Each cell <= 2 lines. Keep wording concise and factual.
- Probability must be a single percent value (e.g., 30.0 %).
- Probabilities across all rows must total exactly 100.0%. Double-check the sum equals 1.0 before output.
- Use plain ASCII only.
- Impact Channels must reference at least one of: Delta LCR, Delta NSFR, Level 1 vs 2A/2B, haircuts, NII.

Example structure only (do not reuse content):
| Scenario | Description | Probability | Rationale | Impact Channels |
| -------- | ----------- | ----------- | --------- | --------------- |
| Mild Credit Tightening | IG/HY spreads widen modestly | 35.0 % | IG z>1, HY momentum | Delta LCR -2 pts; Level 2 haircuts +10%; NII down |

Generate the final table below.
"""
