import os
import sys

from dotenv import load_dotenv

# Ensure access to src
sys.path.append(os.path.abspath("../src"))
sys.path.append(os.path.abspath("../../hqla_risk_metrics"))

from assets import Level1Asset
from portfolio import Portfolio
from scenario_shocks import YCSteepening

from chatgpt_selenium import chatgpt_reallocation
from portfolio_summary import summarize_portfolio

load_dotenv()  # still fine, even if we ignore login env vars

# Build portfolio
p = Portfolio(
    total_expected_outflows_30d=120_000_000, required_stable_funding=150_000_000
)
p.add_asset(Level1Asset("Cash", 100_000_000))
p.add_asset(Level1Asset("UST_10Y", 50_000_000))

# Apply scenario
scenario = YCSteepening(magnitude=0.05)
p_scenario = scenario.apply(p)

# Build string summary
summary_str = summarize_portfolio(p_scenario, scenario_name="YC Steepening")

# Construct the prompt for ChatGPT
prompt = f"""
You are a financial analyst AI. I will provide you with an HQLA portfolio and a matrix of risk scenarios with probabilities.

Please detail:
1. The impact of the given scenario on the portfolio,
2. Recommended reallocations to optimize LCR, NSFR, and RWA stability.

Portfolio summary:
```{summary_str}```
"""

print("Submitting prompt to ChatGPT...\n")
response = chatgpt_reallocation(prompt, headless=False)
print("GPT reallocation suggestions:\n", response)
