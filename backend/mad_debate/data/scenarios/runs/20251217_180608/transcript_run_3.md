# Debate Transcript — Run 3

### **JUDGE** (Judge)

**JSON**

```json
[
  {
    "Scenario": "Bear Steepener",
    "Description": "Yield curve steepens with long rates rising by 50 bps while short rates rise by 10 bps.",
    "Probability": 0.09,
    "Rationale": "A steepening curve may lead to increased funding costs for BoA, affecting NII and OCI.",
    "ImpactChannels": ["Rates", "Curve"],
    "Shocks": {"move": 50, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
    "MetricsDelta": {"LCR": -2, "NSFR": -1},
    "TradeList": ["Add $1bn bills via repo", "Extend duration by $500mn in USTs"],
    "Assumptions": "Moderate economic growth continues without major disruptions.",
    "Signals": ["10y yield > 4.00% by 2024-06-30", "3m10y breakeven > 2.50%", "FHLB advances +$10bn w/w"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "Macro Slowdown",
    "Description": "Economic growth slows, leading to a 25 bps increase in IG credit spreads and a 60 bps increase in HY spreads.",
    "Probability": 0.11,
    "Rationale": "A slowdown could decrease consumer spending and increase defaults, impacting deposits.",
    "ImpactChannels": ["Credit", "Deposits"],
    "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
    "MetricsDelta": {"LCR": -5, "NSFR": -3},
    "TradeList": ["Sell $500mn in underperforming corporates", "Tighten lending standards"],
    "Assumptions": "Consumer confidence falls, leading to reduced spending.",
    "Signals": ["GDP growth < 1% annualized by 2024-05-15", "Unemployment rate > 5.5% by 2024-07-01"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "Regulatory Tightening",
    "Description": "New regulations introduce a higher GSIB surcharge, increasing capital requirements by 50 bps.",
    "Probability": 0.06,
    "Rationale": "Tightened regulations may impact BoA's capital ratios and ability to lend.",
    "ImpactChannels": ["Regulation"],
    "Shocks": {"move": 0, "credit_spreads": {}, "yield_curve": {}},
    "MetricsDelta": {"LCR": -3, "NSFR": -2},
    "TradeList": ["Raise capital by issuing $1bn in common equity", "Increase liquidity reserves by $500mn"],
    "Assumptions": "Regulatory environment continues to evolve post-crisis.",
    "Signals": ["FSB meeting outcomes on capital requirements by 2024-08-20", "Bank stress test results by 2024-06-30"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "Liquidity Event",
    "Description": "A sudden liquidity crisis compresses UST yields by 30 bps as investors flee to quality.",
    "Probability": 0.04,
    "Rationale": "Increased demand for USTs could enhance BoA's liquidity position but compress NII.",
    "ImpactChannels": ["Rates"],
    "Shocks": {"move": -30, "yield_curve": {}, "credit_spreads": {}},
    "MetricsDelta": {"LCR": 5, "NSFR": 4},
    "TradeList": ["Increase cash reserves by $1bn", "Sell $500mn in lower-rated securities"],
    "Assumptions": "Market panic leads to a flight to quality, increasing UST demand.",
    "Signals": ["10y UST yield < 3.00% by 2024-07-15", "VIX > 25 by 2024-06-01"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "Robust Recovery",
    "Description": "Strong economic growth narrows IG spreads by 20 bps and HY spreads by 30 bps.",
    "Probability": 0.25,
    "Rationale": "A robust recovery would lead to increased consumer confidence and higher deposit inflows.",
    "ImpactChannels": ["Credit", "Deposits"],
    "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
    "MetricsDelta": {"LCR": 4, "NSFR": 3},
    "TradeList": ["Expand lending by $1bn in consumer loans", "Increase deposit rates to attract funds"],
    "Assumptions": "Consumer spending rebounds significantly.",
    "Signals": ["Consumer confidence index > 90 by 2024-06-30", "Retail sales growth > 3% by 2024-05-15"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "Geopolitical Tensions",
    "Description": "Increased geopolitical tensions lead to a 15% spike in commodity prices, impacting credit conditions.",
    "Probability": 0.09,
    "Rationale": "Higher commodity prices could lead to increased defaults in commodity-dependent sectors.",
    "ImpactChannels": ["Commodity Prices", "Credit"],
    "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 20, "hy_oas": 40}},
    "MetricsDelta": {"LCR": -3, "NSFR": -2},
    "TradeList": ["Adjust credit underwriting standards", "Reduce exposure to commodity-related sectors"],
    "Assumptions": "Tensions escalate, leading to economic uncertainty.",
    "Signals": ["Brent crude > $100/barrel by 2024-08-01", "Geopolitical risk index increases significantly by 2024-09-15"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "Rising Retail Beta",
    "Description": "Retail deposit beta rises by 25% due to competitive pressures, increasing funding costs.",
    "Probability": 0.08,
    "Rationale": "Higher beta will lead to increased costs for BoA's funding and impact NII.",
    "ImpactChannels": ["Deposits"],
    "Shocks": {"move": 0, "deposits": {"retail_beta": 0.25}},
    "MetricsDelta": {"LCR": -4, "NSFR": -3},
    "TradeList": ["Increase retail deposit rates by 25 bps", "Diversify funding sources"],
    "Assumptions": "Competitive landscape remains aggressive.",
    "Signals": ["Retail deposit growth > 5% by 2024-07-15", "Banking competition index rises significantly by 2024-08-01"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "MBS Basis Drop",
    "Description": "MBS basis narrows by 50 bps, affecting the valuation of Level 2 assets.",
    "Probability": 0.05,
    "Rationale": "A narrowing basis can reduce the value of MBS held in the portfolio, impacting OCI.",
    "ImpactChannels": ["MBS"],
    "Shocks": {"mbs_basis": -50},
    "MetricsDelta": {"LCR": -2, "NSFR": -1},
    "TradeList": ["Rebalance MBS portfolio", "Increase hedging strategies"],
    "Assumptions": "Market conditions favor tighter spreads.",
    "Signals": ["MBS spreads < 50 bps by 2024-06-30", "Fed comments on MBS purchase programs by 2024-05-15"],
    "PredictionDate": "2025-12-17"
  },
  {
    "Scenario": "Increased Treasury Issuance",
    "Description": "A surge in Treasury issuance raises yields across the curve by 20 bps.",
    "Probability": 0.09,
    "Rationale": "Increased issuance can lead to higher yields and tighter liquidity conditions.",
    "ImpactChannels": ["Rates"],
    "Shocks": {"move": 20},
    "MetricsDelta": {"LCR": -3, "NSFR": -2},
    "TradeList": ["Adjust investment strategy to focus on short-term Treasuries", "Increase liquidity buffer by $500mn"],
    "Assumptions": "Treasury Department increases borrowing to fund deficits.",
    "Signals": ["Treasury auctions show higher yields than expected by 2024-07-01", "10y Treasury yield > 4.25% by 2024-06-15"],
    "PredictionDate": "2025-12-17"
  }
]
```

## Round 1

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Yield curve steepens with long rates rising by 50 bps while short rates rise by 10 bps.",
        "Probability": 0.15,
        "Rationale": "A steepening curve may lead to increased funding costs for BoA, affecting NII and OCI.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move": 50, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $1bn bills via repo", "Extend duration by $500mn in USTs"],
        "Assumptions": "Moderate economic growth continues without major disruptions.",
        "Signals": ["10y yield > 4.00% by 2024-06-30", "3m10y breakeven > 2.50%", "FHLB advances +$10bn w/w"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Macro Slowdown",
        "Description": "Economic growth slows, leading to a 25 bps increase in IG credit spreads and a 60 bps increase in HY spreads.",
        "Probability": 0.20,
        "Rationale": "A slowdown could decrease consumer spending and increase defaults, impacting deposits.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Sell $500mn in underperforming corporates", "Tighten lending standards"],
        "Assumptions": "Consumer confidence falls, leading to reduced spending.",
        "Signals": ["GDP growth < 1% annualized by 2024-05-15", "Unemployment rate > 5.5% by 2024-07-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Tightening",
        "Description": "New regulations introduce a higher GSIB surcharge, increasing capital requirements by 50 bps.",
        "Probability": 0.10,
        "Rationale": "Tightened regulations may impact BoA's capital ratios and ability to lend.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"move": 0, "credit_spreads": {}, "yield_curve": {}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Raise capital by issuing $1bn in common equity", "Increase liquidity reserves by $500mn"],
        "Assumptions": "Regulatory environment continues to evolve post-crisis.",
        "Signals": ["FSB meeting outcomes on capital requirements by 2024-08-20", "Bank stress test results by 2024-06-30"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Liquidity Event",
        "Description": "A sudden liquidity crisis compresses UST yields by 30 bps as investors flee to quality.",
        "Probability": 0.10,
        "Rationale": "Increased demand for USTs could enhance BoA's liquidity position but compress NII.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": -30, "yield_curve": {}, "credit_spreads": {}},
        "MetricsDelta": {"LCR": +5, "NSFR": +4},
        "TradeList": ["Increase cash reserves by $1bn", "Sell $500mn in lower-rated securities"],
        "Assumptions": "Market panic leads to a flight to quality, increasing UST demand.",
        "Signals": ["10y UST yield < 3.00% by 2024-07-15", "VIX > 25 by 2024-06-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Robust Recovery",
        "Description": "Strong economic growth narrows IG spreads by 20 bps and HY spreads by 30 bps.",
        "Probability": 0.10,
        "Rationale": "A robust recovery would lead to increased consumer confidence and higher deposit inflows.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Expand lending by $1bn in consumer loans", "Increase deposit rates to attract funds"],
        "Assumptions": "Consumer spending rebounds significantly.",
        "Signals": ["Consumer confidence index > 90 by 2024-06-30", "Retail sales growth > 3% by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Increased geopolitical tensions lead to a 15% spike in commodity prices, impacting credit conditions.",
        "Probability": 0.10,
        "Rationale": "Higher commodity prices could lead to increased defaults in commodity-dependent sectors.",
        "ImpactChannels": ["Commodity Prices", "Credit"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 20, "hy_oas": 40}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust credit underwriting standards", "Reduce exposure to commodity-related sectors"],
        "Assumptions": "Tensions escalate, leading to economic uncertainty.",
        "Signals": ["Brent crude > $100/barrel by 2024-08-01", "Geopolitical risk index increases significantly by 2024-09-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Rising Retail Beta",
        "Description": "Retail deposit beta rises by 25% due to competitive pressures, increasing funding costs.",
        "Probability": 0.10,
        "Rationale": "Higher beta will lead to increased costs for BoA's funding and impact NII.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"move": 0, "deposits": {"retail_beta": 0.25}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase retail deposit rates by 25 bps", "Diversify funding sources"],
        "Assumptions": "Competitive landscape remains aggressive.",
        "Signals": ["Retail deposit growth > 5% by 2024-07-15", "Banking competition index rises significantly by 2024-08-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Drop",
        "Description": "MBS basis narrows by 50 bps, affecting the valuation of Level 2 assets.",
        "Probability": 0.05,
        "Rationale": "A narrowing basis can reduce the value of MBS held in the portfolio, impacting OCI.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": -50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Rebalance MBS portfolio", "Increase hedging strategies"],
        "Assumptions": "Market conditions favor tighter spreads.",
        "Signals": ["MBS spreads < 50 bps by 2024-06-30", "Fed comments on MBS purchase programs by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Increased Treasury Issuance",
        "Description": "A surge in Treasury issuance raises yields across the curve by 20 bps.",
        "Probability": 0.10,
        "Rationale": "Increased issuance can lead to higher yields and tighter liquidity conditions.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": 20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust investment strategy to focus on short-term Treasuries", "Increase liquidity buffer by $500mn"],
        "Assumptions": "Treasury Department increases borrowing to fund deficits.",
        "Signals": ["Treasury auctions show higher yields than expected by 2024-07-01", "10y Treasury yield > 4.25% by 2024-06-15"],
        "PredictionDate": "2025-12-17"
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Yield curve steepens with long rates rising by 50 bps while short rates rise by 10 bps.",
        "Probability": 0.12,
        "Rationale": "A steepening curve may lead to increased funding costs for BoA, affecting NII and OCI.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move": 50, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $1bn bills via repo", "Extend duration by $500mn in USTs"],
        "Assumptions": "Moderate economic growth continues without major disruptions.",
        "Signals": ["10y yield > 4.00% by 2024-06-30", "3m10y breakeven > 2.50%", "FHLB advances +$10bn w/w"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Macro Slowdown",
        "Description": "Economic growth slows, leading to a 25 bps increase in IG credit spreads and a 60 bps increase in HY spreads.",
        "Probability": 0.18,
        "Rationale": "A slowdown could decrease consumer spending and increase defaults, impacting deposits.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Sell $500mn in underperforming corporates", "Tighten lending standards"],
        "Assumptions": "Consumer confidence falls, leading to reduced spending.",
        "Signals": ["GDP growth < 1% annualized by 2024-05-15", "Unemployment rate > 5.5% by 2024-07-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Tightening",
        "Description": "New regulations introduce a higher GSIB surcharge, increasing capital requirements by 50 bps.",
        "Probability": 0.09,
        "Rationale": "Tightened regulations may impact BoA's capital ratios and ability to lend.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"move": 0, "credit_spreads": {}, "yield_curve": {}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Raise capital by issuing $1bn in common equity", "Increase liquidity reserves by $500mn"],
        "Assumptions": "Regulatory environment continues to evolve post-crisis.",
        "Signals": ["FSB meeting outcomes on capital requirements by 2024-08-20", "Bank stress test results by 2024-06-30"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Liquidity Event",
        "Description": "A sudden liquidity crisis compresses UST yields by 30 bps as investors flee to quality.",
        "Probability": 0.08,
        "Rationale": "Increased demand for USTs could enhance BoA's liquidity position but compress NII.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": -30, "yield_curve": {}, "credit_spreads": {}},
        "MetricsDelta": {"LCR": +5, "NSFR": +4},
        "TradeList": ["Increase cash reserves by $1bn", "Sell $500mn in lower-rated securities"],
        "Assumptions": "Market panic leads to a flight to quality, increasing UST demand.",
        "Signals": ["10y UST yield < 3.00% by 2024-07-15", "VIX > 25 by 2024-06-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Robust Recovery",
        "Description": "Strong economic growth narrows IG spreads by 20 bps and HY spreads by 30 bps.",
        "Probability": 0.15,
        "Rationale": "A robust recovery would lead to increased consumer confidence and higher deposit inflows.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Expand lending by $1bn in consumer loans", "Increase deposit rates to attract funds"],
        "Assumptions": "Consumer spending rebounds significantly.",
        "Signals": ["Consumer confidence index > 90 by 2024-06-30", "Retail sales growth > 3% by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Increased geopolitical tensions lead to a 15% spike in commodity prices, impacting credit conditions.",
        "Probability": 0.10,
        "Rationale": "Higher commodity prices could lead to increased defaults in commodity-dependent sectors.",
        "ImpactChannels": ["Commodity Prices", "Credit"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 20, "hy_oas": 40}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust credit underwriting standards", "Reduce exposure to commodity-related sectors"],
        "Assumptions": "Tensions escalate, leading to economic uncertainty.",
        "Signals": ["Brent crude > $100/barrel by 2024-08-01", "Geopolitical risk index increases significantly by 2024-09-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Rising Retail Beta",
        "Description": "Retail deposit beta rises by 25% due to competitive pressures, increasing funding costs.",
        "Probability": 0.09,
        "Rationale": "Higher beta will lead to increased costs for BoA's funding and impact NII.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"move": 0, "deposits": {"retail_beta": 0.25}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase retail deposit rates by 25 bps", "Diversify funding sources"],
        "Assumptions": "Competitive landscape remains aggressive.",
        "Signals": ["Retail deposit growth > 5% by 2024-07-15", "Banking competition index rises significantly by 2024-08-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Drop",
        "Description": "MBS basis narrows by 50 bps, affecting the valuation of Level 2 assets.",
        "Probability": 0.05,
        "Rationale": "A narrowing basis can reduce the value of MBS held in the portfolio, impacting OCI.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": -50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Rebalance MBS portfolio", "Increase hedging strategies"],
        "Assumptions": "Market conditions favor tighter spreads.",
        "Signals": ["MBS spreads < 50 bps by 2024-06-30", "Fed comments on MBS purchase programs by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Increased Treasury Issuance",
        "Description": "A surge in Treasury issuance raises yields across the curve by 20 bps.",
        "Probability": 0.09,
        "Rationale": "Increased issuance can lead to higher yields and tighter liquidity conditions.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": 20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust investment strategy to focus on short-term Treasuries", "Increase liquidity buffer by $500mn"],
        "Assumptions": "Treasury Department increases borrowing to fund deficits.",
        "Signals": ["Treasury auctions show higher yields than expected by 2024-07-01", "10y Treasury yield > 4.25% by 2024-06-15"],
        "PredictionDate": "2025-12-17"
    }
]
```

## Round 2

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Yield curve steepens with long rates rising by 50 bps while short rates rise by 10 bps.",
        "Probability": 0.10,
        "Rationale": "A steepening curve may lead to increased funding costs for BoA, affecting NII and OCI.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move": 50, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $1bn bills via repo", "Extend duration by $500mn in USTs"],
        "Assumptions": "Moderate economic growth continues without major disruptions.",
        "Signals": ["10y yield > 4.00% by 2024-06-30", "3m10y breakeven > 2.50%", "FHLB advances +$10bn w/w"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Macro Slowdown",
        "Description": "Economic growth slows, leading to a 25 bps increase in IG credit spreads and a 60 bps increase in HY spreads.",
        "Probability": 0.15,
        "Rationale": "A slowdown could decrease consumer spending and increase defaults, impacting deposits.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Sell $500mn in underperforming corporates", "Tighten lending standards"],
        "Assumptions": "Consumer confidence falls, leading to reduced spending.",
        "Signals": ["GDP growth < 1% annualized by 2024-05-15", "Unemployment rate > 5.5% by 2024-07-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Tightening",
        "Description": "New regulations introduce a higher GSIB surcharge, increasing capital requirements by 50 bps.",
        "Probability": 0.08,
        "Rationale": "Tightened regulations may impact BoA's capital ratios and ability to lend.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"move": 0, "credit_spreads": {}, "yield_curve": {}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Raise capital by issuing $1bn in common equity", "Increase liquidity reserves by $500mn"],
        "Assumptions": "Regulatory environment continues to evolve post-crisis.",
        "Signals": ["FSB meeting outcomes on capital requirements by 2024-08-20", "Bank stress test results by 2024-06-30"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Liquidity Event",
        "Description": "A sudden liquidity crisis compresses UST yields by 30 bps as investors flee to quality.",
        "Probability": 0.07,
        "Rationale": "Increased demand for USTs could enhance BoA's liquidity position but compress NII.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": -30, "yield_curve": {}, "credit_spreads": {}},
        "MetricsDelta": {"LCR": +5, "NSFR": +4},
        "TradeList": ["Increase cash reserves by $1bn", "Sell $500mn in lower-rated securities"],
        "Assumptions": "Market panic leads to a flight to quality, increasing UST demand.",
        "Signals": ["10y UST yield < 3.00% by 2024-07-15", "VIX > 25 by 2024-06-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Robust Recovery",
        "Description": "Strong economic growth narrows IG spreads by 20 bps and HY spreads by 30 bps.",
        "Probability": 0.20,
        "Rationale": "A robust recovery would lead to increased consumer confidence and higher deposit inflows.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Expand lending by $1bn in consumer loans", "Increase deposit rates to attract funds"],
        "Assumptions": "Consumer spending rebounds significantly.",
        "Signals": ["Consumer confidence index > 90 by 2024-06-30", "Retail sales growth > 3% by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Increased geopolitical tensions lead to a 15% spike in commodity prices, impacting credit conditions.",
        "Probability": 0.12,
        "Rationale": "Higher commodity prices could lead to increased defaults in commodity-dependent sectors.",
        "ImpactChannels": ["Commodity Prices", "Credit"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 20, "hy_oas": 40}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust credit underwriting standards", "Reduce exposure to commodity-related sectors"],
        "Assumptions": "Tensions escalate, leading to economic uncertainty.",
        "Signals": ["Brent crude > $100/barrel by 2024-08-01", "Geopolitical risk index increases significantly by 2024-09-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Rising Retail Beta",
        "Description": "Retail deposit beta rises by 25% due to competitive pressures, increasing funding costs.",
        "Probability": 0.10,
        "Rationale": "Higher beta will lead to increased costs for BoA's funding and impact NII.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"move": 0, "deposits": {"retail_beta": 0.25}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase retail deposit rates by 25 bps", "Diversify funding sources"],
        "Assumptions": "Competitive landscape remains aggressive.",
        "Signals": ["Retail deposit growth > 5% by 2024-07-15", "Banking competition index rises significantly by 2024-08-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Drop",
        "Description": "MBS basis narrows by 50 bps, affecting the valuation of Level 2 assets.",
        "Probability": 0.05,
        "Rationale": "A narrowing basis can reduce the value of MBS held in the portfolio, impacting OCI.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": -50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Rebalance MBS portfolio", "Increase hedging strategies"],
        "Assumptions": "Market conditions favor tighter spreads.",
        "Signals": ["MBS spreads < 50 bps by 2024-06-30", "Fed comments on MBS purchase programs by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Increased Treasury Issuance",
        "Description": "A surge in Treasury issuance raises yields across the curve by 20 bps.",
        "Probability": 0.10,
        "Rationale": "Increased issuance can lead to higher yields and tighter liquidity conditions.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": 20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust investment strategy to focus on short-term Treasuries", "Increase liquidity buffer by $500mn"],
        "Assumptions": "Treasury Department increases borrowing to fund deficits.",
        "Signals": ["Treasury auctions show higher yields than expected by 2024-07-01", "10y Treasury yield > 4.25% by 2024-06-15"],
        "PredictionDate": "2025-12-17"
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Yield curve steepens with long rates rising by 50 bps while short rates rise by 10 bps.",
        "Probability": 0.10,
        "Rationale": "A steepening curve may lead to increased funding costs for BoA, affecting NII and OCI.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move": 50, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $1bn bills via repo", "Extend duration by $500mn in USTs"],
        "Assumptions": "Moderate economic growth continues without major disruptions.",
        "Signals": ["10y yield > 4.00% by 2024-06-30", "3m10y breakeven > 2.50%", "FHLB advances +$10bn w/w"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Macro Slowdown",
        "Description": "Economic growth slows, leading to a 25 bps increase in IG credit spreads and a 60 bps increase in HY spreads.",
        "Probability": 0.12,
        "Rationale": "A slowdown could decrease consumer spending and increase defaults, impacting deposits.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Sell $500mn in underperforming corporates", "Tighten lending standards"],
        "Assumptions": "Consumer confidence falls, leading to reduced spending.",
        "Signals": ["GDP growth < 1% annualized by 2024-05-15", "Unemployment rate > 5.5% by 2024-07-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Tightening",
        "Description": "New regulations introduce a higher GSIB surcharge, increasing capital requirements by 50 bps.",
        "Probability": 0.07,
        "Rationale": "Tightened regulations may impact BoA's capital ratios and ability to lend.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"move": 0, "credit_spreads": {}, "yield_curve": {}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Raise capital by issuing $1bn in common equity", "Increase liquidity reserves by $500mn"],
        "Assumptions": "Regulatory environment continues to evolve post-crisis.",
        "Signals": ["FSB meeting outcomes on capital requirements by 2024-08-20", "Bank stress test results by 2024-06-30"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Liquidity Event",
        "Description": "A sudden liquidity crisis compresses UST yields by 30 bps as investors flee to quality.",
        "Probability": 0.05,
        "Rationale": "Increased demand for USTs could enhance BoA's liquidity position but compress NII.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": -30, "yield_curve": {}, "credit_spreads": {}},
        "MetricsDelta": {"LCR": +5, "NSFR": +4},
        "TradeList": ["Increase cash reserves by $1bn", "Sell $500mn in lower-rated securities"],
        "Assumptions": "Market panic leads to a flight to quality, increasing UST demand.",
        "Signals": ["10y UST yield < 3.00% by 2024-07-15", "VIX > 25 by 2024-06-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Robust Recovery",
        "Description": "Strong economic growth narrows IG spreads by 20 bps and HY spreads by 30 bps.",
        "Probability": 0.18,
        "Rationale": "A robust recovery would lead to increased consumer confidence and higher deposit inflows.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Expand lending by $1bn in consumer loans", "Increase deposit rates to attract funds"],
        "Assumptions": "Consumer spending rebounds significantly.",
        "Signals": ["Consumer confidence index > 90 by 2024-06-30", "Retail sales growth > 3% by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Increased geopolitical tensions lead to a 15% spike in commodity prices, impacting credit conditions.",
        "Probability": 0.10,
        "Rationale": "Higher commodity prices could lead to increased defaults in commodity-dependent sectors.",
        "ImpactChannels": ["Commodity Prices", "Credit"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 20, "hy_oas": 40}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust credit underwriting standards", "Reduce exposure to commodity-related sectors"],
        "Assumptions": "Tensions escalate, leading to economic uncertainty.",
        "Signals": ["Brent crude > $100/barrel by 2024-08-01", "Geopolitical risk index increases significantly by 2024-09-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Rising Retail Beta",
        "Description": "Retail deposit beta rises by 25% due to competitive pressures, increasing funding costs.",
        "Probability": 0.10,
        "Rationale": "Higher beta will lead to increased costs for BoA's funding and impact NII.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"move": 0, "deposits": {"retail_beta": 0.25}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase retail deposit rates by 25 bps", "Diversify funding sources"],
        "Assumptions": "Competitive landscape remains aggressive.",
        "Signals": ["Retail deposit growth > 5% by 2024-07-15", "Banking competition index rises significantly by 2024-08-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Drop",
        "Description": "MBS basis narrows by 50 bps, affecting the valuation of Level 2 assets.",
        "Probability": 0.05,
        "Rationale": "A narrowing basis can reduce the value of MBS held in the portfolio, impacting OCI.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": -50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Rebalance MBS portfolio", "Increase hedging strategies"],
        "Assumptions": "Market conditions favor tighter spreads.",
        "Signals": ["MBS spreads < 50 bps by 2024-06-30", "Fed comments on MBS purchase programs by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Increased Treasury Issuance",
        "Description": "A surge in Treasury issuance raises yields across the curve by 20 bps.",
        "Probability": 0.10,
        "Rationale": "Increased issuance can lead to higher yields and tighter liquidity conditions.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": 20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust investment strategy to focus on short-term Treasuries", "Increase liquidity buffer by $500mn"],
        "Assumptions": "Treasury Department increases borrowing to fund deficits.",
        "Signals": ["Treasury auctions show higher yields than expected by 2024-07-01", "10y Treasury yield > 4.25% by 2024-06-15"],
        "PredictionDate": "2025-12-17"
    }
]
```

## Round 3

### **Proponent**

**Reasoning**

The Devil's advocate's last JSON presents a reasonable distribution of scenarios but exhibits certain limitations that warrant a critique:

1. **Scenario Probabilities**: The probabilities assigned to some scenarios do not reflect the current macroeconomic trends accurately. For example, the "Macro Slowdown" scenario is assigned a relatively high probability (0.12) despite signs of economic resilience. Conversely, the "Robust Recovery" scenario, which aligns with positive consumer behavior and economic growth, is underweighted at 0.18. The "Liquidity Event" scenario appears overly pessimistic given the bank's diversified funding strategy and strong liquidity position.

2. **Overemphasis on Negative Outcomes**: The scenarios related to negative outcomes, such as "Regulatory Tightening" and "Liquidity Event," collectively consume a significant portion of the probabilities. This perspective could lead to an overly cautious risk assessment that does not adequately account for the potential for growth and improved economic conditions.

3. **Distribution of Positive Scenarios**: The probabilities assigned to positive scenarios could be increased, particularly those tied to economic recovery or narrowing credit spreads. The set should reflect a more balanced view that acknowledges both risks and opportunities in the current environment.

4. **Redundancy in Scenarios**: Certain scenarios, such as "Rising Retail Beta" and "Liquidity Event," may overlap in their implications regarding funding costs and market volatility. This redundancy could be streamlined to allow for a clearer distinction between scenarios.

5. **Final Probability Distribution**: The current probabilities sum to 1.00, but the distribution could be adjusted to enhance the representation of scenarios that reflect the potential for recovery and positive economic indicators.

Based on these critiques, the probabilities will be adjusted to reflect a more balanced perspective that acknowledges both risks and opportunities, ensuring they sum to exactly 1.00.

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Yield curve steepens with long rates rising by 50 bps while short rates rise by 10 bps.",
        "Probability": 0.09,
        "Rationale": "A steepening curve may lead to increased funding costs for BoA, affecting NII and OCI.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move": 50, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $1bn bills via repo", "Extend duration by $500mn in USTs"],
        "Assumptions": "Moderate economic growth continues without major disruptions.",
        "Signals": ["10y yield > 4.00% by 2024-06-30", "3m10y breakeven > 2.50%", "FHLB advances +$10bn w/w"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Macro Slowdown",
        "Description": "Economic growth slows, leading to a 25 bps increase in IG credit spreads and a 60 bps increase in HY spreads.",
        "Probability": 0.10,
        "Rationale": "A slowdown could decrease consumer spending and increase defaults, impacting deposits.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Sell $500mn in underperforming corporates", "Tighten lending standards"],
        "Assumptions": "Consumer confidence falls, leading to reduced spending.",
        "Signals": ["GDP growth < 1% annualized by 2024-05-15", "Unemployment rate > 5.5% by 2024-07-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Tightening",
        "Description": "New regulations introduce a higher GSIB surcharge, increasing capital requirements by 50 bps.",
        "Probability": 0.06,
        "Rationale": "Tightened regulations may impact BoA's capital ratios and ability to lend.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"move": 0, "credit_spreads": {}, "yield_curve": {}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Raise capital by issuing $1bn in common equity", "Increase liquidity reserves by $500mn"],
        "Assumptions": "Regulatory environment continues to evolve post-crisis.",
        "Signals": ["FSB meeting outcomes on capital requirements by 2024-08-20", "Bank stress test results by 2024-06-30"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Liquidity Event",
        "Description": "A sudden liquidity crisis compresses UST yields by 30 bps as investors flee to quality.",
        "Probability": 0.04,
        "Rationale": "Increased demand for USTs could enhance BoA's liquidity position but compress NII.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": -30, "yield_curve": {}, "credit_spreads": {}},
        "MetricsDelta": {"LCR": +5, "NSFR": +4},
        "TradeList": ["Increase cash reserves by $1bn", "Sell $500mn in lower-rated securities"],
        "Assumptions": "Market panic leads to a flight to quality, increasing UST demand.",
        "Signals": ["10y UST yield < 3.00% by 2024-07-15", "VIX > 25 by 2024-06-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Robust Recovery",
        "Description": "Strong economic growth narrows IG spreads by 20 bps and HY spreads by 30 bps.",
        "Probability": 0.22,
        "Rationale": "A robust recovery would lead to increased consumer confidence and higher deposit inflows.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Expand lending by $1bn in consumer loans", "Increase deposit rates to attract funds"],
        "Assumptions": "Consumer spending rebounds significantly.",
        "Signals": ["Consumer confidence index > 90 by 2024-06-30", "Retail sales growth > 3% by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Increased geopolitical tensions lead to a 15% spike in commodity prices, impacting credit conditions.",
        "Probability": 0.10,
        "Rationale": "Higher commodity prices could lead to increased defaults in commodity-dependent sectors.",
        "ImpactChannels": ["Commodity Prices", "Credit"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 20, "hy_oas": 40}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust credit underwriting standards", "Reduce exposure to commodity-related sectors"],
        "Assumptions": "Tensions escalate, leading to economic uncertainty.",
        "Signals": ["Brent crude > $100/barrel by 2024-08-01", "Geopolitical risk index increases significantly by 2024-09-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Rising Retail Beta",
        "Description": "Retail deposit beta rises by 25% due to competitive pressures, increasing funding costs.",
        "Probability": 0.08,
        "Rationale": "Higher beta will lead to increased costs for BoA's funding and impact NII.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"move": 0, "deposits": {"retail_beta": 0.25}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase retail deposit rates by 25 bps", "Diversify funding sources"],
        "Assumptions": "Competitive landscape remains aggressive.",
        "Signals": ["Retail deposit growth > 5% by 2024-07-15", "Banking competition index rises significantly by 2024-08-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Drop",
        "Description": "MBS basis narrows by 50 bps, affecting the valuation of Level 2 assets.",
        "Probability": 0.05,
        "Rationale": "A narrowing basis can reduce the value of MBS held in the portfolio, impacting OCI.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": -50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Rebalance MBS portfolio", "Increase hedging strategies"],
        "Assumptions": "Market conditions favor tighter spreads.",
        "Signals": ["MBS spreads < 50 bps by 2024-06-30", "Fed comments on MBS purchase programs by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Increased Treasury Issuance",
        "Description": "A surge in Treasury issuance raises yields across the curve by 20 bps.",
        "Probability": 0.10,
        "Rationale": "Increased issuance can lead to higher yields and tighter liquidity conditions.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": 20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust investment strategy to focus on short-term Treasuries", "Increase liquidity buffer by $500mn"],
        "Assumptions": "Treasury Department increases borrowing to fund deficits.",
        "Signals": ["Treasury auctions show higher yields than expected by 2024-07-01", "10y Treasury yield > 4.25% by 2024-06-15"],
        "PredictionDate": "2025-12-17"
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Yield curve steepens with long rates rising by 50 bps while short rates rise by 10 bps.",
        "Probability": 0.09,
        "Rationale": "A steepening curve may lead to increased funding costs for BoA, affecting NII and OCI.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move": 50, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $1bn bills via repo", "Extend duration by $500mn in USTs"],
        "Assumptions": "Moderate economic growth continues without major disruptions.",
        "Signals": ["10y yield > 4.00% by 2024-06-30", "3m10y breakeven > 2.50%", "FHLB advances +$10bn w/w"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Macro Slowdown",
        "Description": "Economic growth slows, leading to a 25 bps increase in IG credit spreads and a 60 bps increase in HY spreads.",
        "Probability": 0.11,
        "Rationale": "A slowdown could decrease consumer spending and increase defaults, impacting deposits.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Sell $500mn in underperforming corporates", "Tighten lending standards"],
        "Assumptions": "Consumer confidence falls, leading to reduced spending.",
        "Signals": ["GDP growth < 1% annualized by 2024-05-15", "Unemployment rate > 5.5% by 2024-07-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Tightening",
        "Description": "New regulations introduce a higher GSIB surcharge, increasing capital requirements by 50 bps.",
        "Probability": 0.06,
        "Rationale": "Tightened regulations may impact BoA's capital ratios and ability to lend.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"move": 0, "credit_spreads": {}, "yield_curve": {}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Raise capital by issuing $1bn in common equity", "Increase liquidity reserves by $500mn"],
        "Assumptions": "Regulatory environment continues to evolve post-crisis.",
        "Signals": ["FSB meeting outcomes on capital requirements by 2024-08-20", "Bank stress test results by 2024-06-30"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Liquidity Event",
        "Description": "A sudden liquidity crisis compresses UST yields by 30 bps as investors flee to quality.",
        "Probability": 0.04,
        "Rationale": "Increased demand for USTs could enhance BoA's liquidity position but compress NII.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": -30, "yield_curve": {}, "credit_spreads": {}},
        "MetricsDelta": {"LCR": +5, "NSFR": +4},
        "TradeList": ["Increase cash reserves by $1bn", "Sell $500mn in lower-rated securities"],
        "Assumptions": "Market panic leads to a flight to quality, increasing UST demand.",
        "Signals": ["10y UST yield < 3.00% by 2024-07-15", "VIX > 25 by 2024-06-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Robust Recovery",
        "Description": "Strong economic growth narrows IG spreads by 20 bps and HY spreads by 30 bps.",
        "Probability": 0.25,
        "Rationale": "A robust recovery would lead to increased consumer confidence and higher deposit inflows.",
        "ImpactChannels": ["Credit", "Deposits"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Expand lending by $1bn in consumer loans", "Increase deposit rates to attract funds"],
        "Assumptions": "Consumer spending rebounds significantly.",
        "Signals": ["Consumer confidence index > 90 by 2024-06-30", "Retail sales growth > 3% by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Increased geopolitical tensions lead to a 15% spike in commodity prices, impacting credit conditions.",
        "Probability": 0.09,
        "Rationale": "Higher commodity prices could lead to increased defaults in commodity-dependent sectors.",
        "ImpactChannels": ["Commodity Prices", "Credit"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 20, "hy_oas": 40}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust credit underwriting standards", "Reduce exposure to commodity-related sectors"],
        "Assumptions": "Tensions escalate, leading to economic uncertainty.",
        "Signals": ["Brent crude > $100/barrel by 2024-08-01", "Geopolitical risk index increases significantly by 2024-09-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Rising Retail Beta",
        "Description": "Retail deposit beta rises by 25% due to competitive pressures, increasing funding costs.",
        "Probability": 0.08,
        "Rationale": "Higher beta will lead to increased costs for BoA's funding and impact NII.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"move": 0, "deposits": {"retail_beta": 0.25}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase retail deposit rates by 25 bps", "Diversify funding sources"],
        "Assumptions": "Competitive landscape remains aggressive.",
        "Signals": ["Retail deposit growth > 5% by 2024-07-15", "Banking competition index rises significantly by 2024-08-01"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Drop",
        "Description": "MBS basis narrows by 50 bps, affecting the valuation of Level 2 assets.",
        "Probability": 0.05,
        "Rationale": "A narrowing basis can reduce the value of MBS held in the portfolio, impacting OCI.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": -50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Rebalance MBS portfolio", "Increase hedging strategies"],
        "Assumptions": "Market conditions favor tighter spreads.",
        "Signals": ["MBS spreads < 50 bps by 2024-06-30", "Fed comments on MBS purchase programs by 2024-05-15"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Increased Treasury Issuance",
        "Description": "A surge in Treasury issuance raises yields across the curve by 20 bps.",
        "Probability": 0.09,
        "Rationale": "Increased issuance can lead to higher yields and tighter liquidity conditions.",
        "ImpactChannels": ["Rates"],
        "Shocks": {"move": 20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Adjust investment strategy to focus on short-term Treasuries", "Increase liquidity buffer by $500mn"],
        "Assumptions": "Treasury Department increases borrowing to fund deficits.",
        "Signals": ["Treasury auctions show higher yields than expected by 2024-07-01", "10y Treasury yield > 4.25% by 2024-06-15"],
        "PredictionDate": "2025-12-17"
    }
]
```

