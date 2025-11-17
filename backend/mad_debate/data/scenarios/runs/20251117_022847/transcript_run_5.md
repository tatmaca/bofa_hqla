# Debate Transcript — Run 5

### **JUDGE** (Judge)

**JSON**

```json
[
  {
    "Scenario": "Persistent Inflation Shock",
    "Description": "Inflation remains elevated, forcing the Fed into additional aggressive rate hikes. Credit spreads widen and MBS underperform as risk sentiment deteriorates.",
    "Probability": 0.25,
    "Rationale": "Recent inflation prints and sticky wage growth prompt the Fed to tighten further, driving up rates and risk premia.",
    "ImpactChannels": ["Rates", "Credit", "MBS", "Deposits"],
    "Shocks": {"Rates": 50, "Curve": "bear_steepener", "IG_OAS": 20, "HY_OAS": 40, "MBS_Basis": 15},
    "TradeList": ["SELL 30y MBS", "BUY 2y UST"],
    "MetricsDelta": {"ΔLCR": -4.0, "ΔNSFR": -1.5, "ΔNII": 2.1},
    "Assumptions": "Inflation persists above target; Fed guidance turns more hawkish; deposit betas rise modestly."
  },
  {
    "Scenario": "Stable Inflation with Gradual Rate Cuts",
    "Description": "Inflation stabilizes, allowing the Fed to begin a slow, measured rate-cutting cycle. Credit spreads tighten and HQLA valuations improve.",
    "Probability": 0.20,
    "Rationale": "Anchored inflation expectations and softening labor market data allow for a dovish policy pivot.",
    "ImpactChannels": ["Rates", "Credit", "MBS"],
    "Shocks": {"Rates": -25, "Curve": "bull_flattener", "IG_OAS": -10, "HY_OAS": -5, "MBS_Basis": -5},
    "TradeList": ["BUY 10y UST", "ADD Agency MBS"],
    "MetricsDelta": {"ΔLCR": 3.0, "ΔNSFR": 1.0, "ΔNII": -1.2},
    "Assumptions": "Inflation remains near target; Fed signals gradual cuts; deposit outflows slow."
  },
  {
    "Scenario": "Geopolitical Risk-Off Stress",
    "Description": "Escalating geopolitical tensions trigger a flight to quality, deposit outflows, and sharp volatility in rates and credit.",
    "Probability": 0.15,
    "Rationale": "External shocks (e.g., conflict escalation, trade disruptions) drive risk aversion and funding stress.",
    "ImpactChannels": ["Rates", "Credit", "Deposits", "MBS"],
    "Shocks": {"Rates": 25, "Curve": "bear_steepener", "IG_OAS": 30, "HY_OAS": 60, "MBS_Basis": 20},
    "TradeList": ["INCREASE cash reserves", "REDUCE HY credit"],
    "MetricsDelta": {"ΔLCR": -7.0, "ΔNSFR": -2.5, "ΔNII": 1.8},
    "Assumptions": "Sudden risk-off; deposit outflows from corporate and retail; market liquidity deteriorates."
  },
  {
    "Scenario": "Resilient Corporate Balance Sheets",
    "Description": "Strong corporate earnings and cash flows support credit markets, keeping spreads tight and deposit inflows steady.",
    "Probability": 0.15,
    "Rationale": "Corporate sector strength underpins credit and deposit stability, supporting HQLA performance.",
    "ImpactChannels": ["Credit", "Deposits", "Rates"],
    "Shocks": {"Rates": -15, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -10, "MBS_Basis": -3},
    "TradeList": ["ADD IG Credit", "HOLD MBS"],
    "MetricsDelta": {"ΔLCR": 2.0, "ΔNSFR": 0.5, "ΔNII": -0.7},
    "Assumptions": "Corporate profitability remains robust; no major defaults; deposit base grows modestly."
  },
  {
    "Scenario": "Regulatory Tightening",
    "Description": "Supervisory scrutiny increases, with new or anticipated liquidity requirements prompting portfolio rebalancing.",
    "Probability": 0.10,
    "Rationale": "Regulators respond to recent market events by tightening liquidity standards, impacting HQLA composition.",
    "ImpactChannels": ["Regulation", "Deposits", "Rates"],
    "Shocks": {"Rates": 10, "Curve": "flat", "IG_OAS": 5, "HY_OAS": 10, "MBS_Basis": 0},
    "TradeList": ["INCREASE Level 1 HQLA", "REDUCE Level 2 MBS"],
    "MetricsDelta": {"ΔLCR": -2.0, "ΔNSFR": -0.8, "ΔNII": 0.3},
    "Assumptions": "Regulatory guidance tightens; banks front-load HQLA upgrades; deposit mix shifts toward insured balances."
  },
  {
    "Scenario": "Moderate Economic Growth with Limited Volatility",
    "Description": "Steady economic growth and muted volatility support stable liquidity and capital metrics.",
    "Probability": 0.15,
    "Rationale": "No major shocks; economic indicators remain positive; funding and credit conditions benign.",
    "ImpactChannels": ["Deposits", "Rates", "Credit"],
    "Shocks": {"Rates": -10, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -5, "MBS_Basis": -2},
    "TradeList": ["MAINTAIN current HQLA mix"],
    "MetricsDelta": {"ΔLCR": 1.0, "ΔNSFR": 0.2, "ΔNII": -0.3},
    "Assumptions": "No significant policy or market changes; deposit base stable; credit losses low."
  }
]
```

## Round 1

### **A**

**JSON**

```json
[
  {
    "Scenario": "Persistent Inflation Scenario",
    "Description": "High inflation persists, forcing aggressive Fed rate hikes.",
    "Probability": 0.35,
    "Rationale": "Inflation pressures lead to continued monetary tightening, impacting asset valuations.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": +50, "Curve": "bear_steepener", "IG_OAS": +30, "HY_OAS": +60, "MBS_Basis": +15},
    "MetricsDelta": {"LCR": -5, "NSFR": -5, "Capital_Ratio": -0.5},
    "TradeList": ["Reduce MBS exposure", "Increase UST holdings"],
    "Assumptions": "Inflation remains above target; Fed responds aggressively."
  },
  {
    "Scenario": "Geopolitical Tensions Scenario",
    "Description": "Escalating geopolitical risks lead to market instability.",
    "Probability": 0.25,
    "Rationale": "Market volatility and a flight to quality could pressure liquidity metrics.",
    "ImpactChannels": ["Rates", "Deposits"],
    "Shocks": {"Rates": +25, "Curve": "bear_steepener", "IG_OAS": +20, "HY_OAS": +40, "MBS_Basis": +10},
    "MetricsDelta": {"LCR": -10, "NSFR": -7, "Capital_Ratio": -0.3},
    "TradeList": ["Increase cash reserves", "Diversify funding sources"],
    "Assumptions": "Investors seek safety, leading to deposit outflows."
  },
  {
    "Scenario": "Regulatory Tightening Scenario",
    "Description": "New liquidity regulations impact capital and liquidity requirements.",
    "Probability": 0.20,
    "Rationale": "Regulators may increase scrutiny on liquidity metrics due to market conditions.",
    "ImpactChannels": ["Regulation", "Deposits"],
    "Shocks": {"Rates": +30, "Curve": "flat", "IG_OAS": +15, "HY_OAS": +25, "MBS_Basis": 0},
    "MetricsDelta": {"LCR": -8, "NSFR": -5, "Capital_Ratio": -0.4},
    "TradeList": ["Reallocate towards Level 1 assets", "Enhance liquidity management"],
    "Assumptions": "Regulatory changes are expected based on recent market volatility."
  },
  {
    "Scenario": "Market Sentiment Shift Scenario",
    "Description": "Negative economic data leads to a sell-off in risk assets.",
    "Probability": 0.15,
    "Rationale": "Poor market sentiment could trigger liquidity challenges and asset valuation drops.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": +15, "Curve": "bear_steepener", "IG_OAS": +25, "HY_OAS": +50, "MBS_Basis": +5},
    "MetricsDelta": {"LCR": -6, "NSFR": -4, "Capital_Ratio": -0.2},
    "TradeList": ["Increase cash holdings", "Reduce exposure to riskier assets"],
    "Assumptions": "Market reacts negatively to economic indicators."
  },
  {
    "Scenario": "Recession Scenario",
    "Description": "Economic indicators signal a recession, causing a risk-off environment.",
    "Probability": 0.05,
    "Rationale": "A recession would severely impact liquidity and capital ratios due to asset devaluation.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": +10, "Curve": "flat", "IG_OAS": +40, "HY_OAS": +80, "MBS_Basis": +20},
    "MetricsDelta": {"LCR": -12, "NSFR": -10, "Capital_Ratio": -1.0},
    "TradeList": ["Maximize liquidity buffers", "Consider hedging strategies"],
    "Assumptions": "Economic downturn leads to widespread asset devaluation."
  }
]
```

### **B**

**JSON**

```json
[
  {
    "Scenario": "Stable Inflation with Gradual Rate Cuts",
    "Description": "Inflation trends stabilize, leading to a gradual easing of monetary policy.",
    "Probability": 0.30,
    "Rationale": "Inflation expectations remain anchored, allowing the Fed to cut rates slowly.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -25, "Curve": "bull_flattener", "IG_OAS": -10, "HY_OAS": -5, "MBS_Basis": -5},
    "Assumptions": "Economic growth remains stable; inflation expectations are well-anchored."
  },
  {
    "Scenario": "Resilient Corporate Balance Sheets",
    "Description": "Strong corporate earnings support credit markets and stabilize spreads.",
    "Probability": 0.25,
    "Rationale": "Corporate balance sheets remain robust, leading to stable credit spreads.",
    "ImpactChannels": ["Credit", "Deposits"],
    "Shocks": {"Rates": -15, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -10, "MBS_Basis": -3},
    "Assumptions": "Corporate profitability supports liquidity and investor confidence."
  },
  {
    "Scenario": "Positive Carry in Short-Duration Treasuries",
    "Description": "Increased inflows into short-duration Treasuries enhance carry.",
    "Probability": 0.20,
    "Rationale": "Investors seek safety, leading to tighter spreads and improved carry in HQLA.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -20, "Curve": "bull_flattener", "IG_OAS": -8, "HY_OAS": -3, "MBS_Basis": -4},
    "Assumptions": "Market volatility leads investors to favor liquidity and safety."
  },
  {
    "Scenario": "Stable Economic Growth",
    "Description": "Moderate economic growth supports stable liquidity conditions.",
    "Probability": 0.15,
    "Rationale": "Economic growth leads to positive inflows and stable funding environments.",
    "ImpactChannels": ["Deposits", "Regulation"],
    "Shocks": {"Rates": -10, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -5, "MBS_Basis": -2},
    "Assumptions": "The economy grows steadily without major disruptions."
  },
  {
    "Scenario": "Controlled Inflation with Low Volatility",
    "Description": "Inflation remains controlled with low market volatility, supporting HQLA performance.",
    "Probability": 0.10,
    "Rationale": "A well-managed inflation environment leads to stable rates and spreads.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -5, "Curve": "bull_flattener", "IG_OAS": -3, "HY_OAS": -2, "MBS_Basis": -1},
    "Assumptions": "Inflation remains below target; central banks maintain a cautious approach."
  }
]
```

## Round 2

### **A**

**Reasoning**

B's scenarios present a more optimistic view of the macroeconomic landscape, focusing on stable growth and resilient corporate balance sheets. While these outcomes are plausible, there are notable weaknesses:

1. **Overly Optimistic Probability Distribution**: The sum of probabilities does not account for potential downside risks sufficiently. While scenarios for stable growth and inflation control are included, they may not reflect the current economic uncertainties that could lead to adverse outcomes. The distribution should balance both optimistic and pessimistic scenarios more evenly.

2. **Lack of Tail Risks**: The scenarios do not adequately address tail risks associated with potential economic downturns or external shocks, such as geopolitical tensions or sudden shifts in monetary policy. In the current environment, it is essential to incorporate scenarios that account for more extreme outcomes.

3. **Insufficient Focus on Funding Stress**: The scenarios neglect potential funding stress and liquidity pressures that could arise from a sudden market correction. While there are references to stable deposits, the bank's reliance on them might not hold in a rapidly changing environment.

4. **Limited Attention to Regulatory Changes**: The scenarios do not sufficiently consider potential regulatory changes that could affect liquidity and capital requirements. This could be particularly relevant given the evolving financial landscape and heightened scrutiny on banks.

5. **Inconsistent Transmission Channels**: Some scenarios do not clearly articulate the transmission channels through which the outcomes would affect HQLA. For instance, the impact of corporate balance sheets on credit spreads should be more explicitly defined.

**JSON**

```json
[
  {
    "Scenario": "Stable Inflation with Gradual Rate Cuts",
    "Description": "Inflation trends stabilize, leading to a gradual easing of monetary policy.",
    "Probability": 0.20,
    "Rationale": "Inflation expectations remain anchored, allowing the Fed to cut rates slowly, which supports HQLA valuations.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -25, "Curve": "bull_flattener", "IG_OAS": -10, "HY_OAS": -5, "MBS_Basis": -5},
    "Assumptions": "Economic growth remains stable; inflation expectations are well-anchored."
  },
  {
    "Scenario": "Resilient Corporate Balance Sheets",
    "Description": "Strong corporate earnings support credit markets and stabilize spreads.",
    "Probability": 0.20,
    "Rationale": "Corporate balance sheets remain robust, leading to stable credit spreads and positive sentiment.",
    "ImpactChannels": ["Credit", "Deposits"],
    "Shocks": {"Rates": -15, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -10, "MBS_Basis": -3},
    "Assumptions": "Corporate profitability supports liquidity and investor confidence."
  },
  {
    "Scenario": "Positive Carry in Short-Duration Treasuries",
    "Description": "Increased inflows into short-duration Treasuries enhance carry.",
    "Probability": 0.20,
    "Rationale": "Investors seek safety, leading to tighter spreads and improved carry in HQLA.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -20, "Curve": "bull_flattener", "IG_OAS": -8, "HY_OAS": -3, "MBS_Basis": -4},
    "Assumptions": "Market volatility leads investors to favor liquidity and safety."
  },
  {
    "Scenario": "Moderate Economic Growth with Limited Volatility",
    "Description": "Economic growth leads to stable liquidity conditions without significant volatility.",
    "Probability": 0.20,
    "Rationale": "Stable economic conditions support liquidity, allowing banks to maintain strong capital ratios.",
    "ImpactChannels": ["Deposits", "Regulation"],
    "Shocks": {"Rates": -10, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -5, "MBS_Basis": -2},
    "Assumptions": "The economy grows steadily without major disruptions."
  },
  {
    "Scenario": "Regulatory Stability with Enhanced Liquidity Standards",
    "Description": "Regulatory environment remains stable, enhancing liquidity requirements.",
    "Probability": 0.20,
    "Rationale": "Stability in regulations supports bank liquidity and confidence in HQLA.",
    "ImpactChannels": ["Regulation", "Deposits"],
    "Shocks": {"Rates": -5, "Curve": "flat", "IG_OAS": -3, "HY_OAS": -2, "MBS_Basis": -1},
    "Assumptions": "Regulatory environment does not introduce new risks; banks maintain strong liquidity."
  }
]
```

### **B**

**JSON**

```json
[
  {
    "Scenario": "Stable Inflation with Gradual Rate Cuts",
    "Description": "Inflation trends stabilize, leading to a gradual easing of monetary policy.",
    "Probability": 0.30,
    "Rationale": "Inflation expectations remain anchored, allowing the Fed to cut rates slowly.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -25, "Curve": "bull_flattener", "IG_OAS": -10, "HY_OAS": -5, "MBS_Basis": -5},
    "Assumptions": "Economic growth remains stable; inflation expectations are well-anchored."
  },
  {
    "Scenario": "Resilient Corporate Balance Sheets",
    "Description": "Strong corporate earnings support credit markets and stabilize spreads.",
    "Probability": 0.25,
    "Rationale": "Corporate balance sheets remain robust, leading to stable credit spreads.",
    "ImpactChannels": ["Credit", "Deposits"],
    "Shocks": {"Rates": -15, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -10, "MBS_Basis": -3},
    "Assumptions": "Corporate profitability supports liquidity and investor confidence."
  },
  {
    "Scenario": "Positive Carry in Short-Duration Treasuries",
    "Description": "Increased inflows into short-duration Treasuries enhance carry.",
    "Probability": 0.20,
    "Rationale": "Investors seek safety, leading to tighter spreads and improved carry in HQLA.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -20, "Curve": "bull_flattener", "IG_OAS": -8, "HY_OAS": -3, "MBS_Basis": -4},
    "Assumptions": "Market volatility leads investors to favor liquidity and safety."
  },
  {
    "Scenario": "Moderate Economic Growth with Limited Volatility",
    "Description": "Economic growth leads to stable liquidity conditions without significant volatility.",
    "Probability": 0.15,
    "Rationale": "Stable economic conditions support liquidity, allowing banks to maintain strong capital ratios.",
    "ImpactChannels": ["Deposits", "Regulation"],
    "Shocks": {"Rates": -10, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -5, "MBS_Basis": -2},
    "Assumptions": "The economy grows steadily without major disruptions."
  },
  {
    "Scenario": "Regulatory Stability with Enhanced Liquidity Standards",
    "Description": "Regulatory environment remains stable, enhancing liquidity requirements.",
    "Probability": 0.10,
    "Rationale": "Stability in regulations supports bank liquidity and confidence in HQLA.",
    "ImpactChannels": ["Regulation", "Deposits"],
    "Shocks": {"Rates": -5, "Curve": "flat", "IG_OAS": -3, "HY_OAS": -2, "MBS_Basis": -1},
    "Assumptions": "Regulatory environment does not introduce new risks; banks maintain strong liquidity."
  }
]
```

## Round 3

### **A**

**Reasoning**

B's last JSON presents several scenarios that reflect a generally optimistic outlook on the macroeconomic landscape. However, there are notable critiques:

1. **Probability Distribution**: The sum of probabilities in B's scenarios is skewed towards positive outcomes without adequately accounting for potential downside risks. The distribution does not provide a balanced view of likely macroeconomic developments, as it fails to include scenarios that might reflect more challenging economic conditions.

2. **Lack of Tail Risks**: The scenarios do not sufficiently address potential tail risks or extreme events that could adversely affect HQLA, such as sudden geopolitical tensions, financial crises, or unexpected monetary policy shifts. The absence of these scenarios indicates a lack of comprehensive risk assessment.

3. **Funding and Liquidity Assumptions**: The reliance on stable deposits and resilient corporate balance sheets overlooks potential funding stress that could arise from market corrections or shifts in investor sentiment. The scenarios should incorporate the possibility of liquidity pressures that may impact the bank's capital ratios.

4. **Regulatory Environment**: While there is a mention of regulatory stability, the scenarios do not consider the impact of potential regulatory changes that could tighten liquidity requirements. Given the evolving financial landscape, this oversight may lead to an incomplete understanding of the potential risks.

5. **Transmission Channels**: Some scenarios lack clear articulation of how the proposed shocks would specifically impact HQLA valuations and liquidity metrics. For example, while the impact of stable corporate balance sheets on credit spreads is mentioned, the transmission mechanism could be more explicitly detailed.

**JSON**

```json
[
  {
    "Scenario": "Stable Inflation with Gradual Rate Cuts",
    "Description": "Inflation trends stabilize, leading to a gradual easing of monetary policy.",
    "Probability": 0.20,
    "Rationale": "Inflation expectations remain anchored, allowing the Fed to cut rates slowly, which supports HQLA valuations.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -25, "Curve": "bull_flattener", "IG_OAS": -10, "HY_OAS": -5, "MBS_Basis": -5},
    "Assumptions": "Economic growth remains stable; inflation expectations are well-anchored."
  },
  {
    "Scenario": "Resilient Corporate Balance Sheets",
    "Description": "Strong corporate earnings support credit markets and stabilize spreads.",
    "Probability": 0.20,
    "Rationale": "Corporate balance sheets remain robust, leading to stable credit spreads and positive sentiment.",
    "ImpactChannels": ["Credit", "Deposits"],
    "Shocks": {"Rates": -15, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -10, "MBS_Basis": -3},
    "Assumptions": "Corporate profitability supports liquidity and investor confidence."
  },
  {
    "Scenario": "Positive Carry in Short-Duration Treasuries",
    "Description": "Increased inflows into short-duration Treasuries enhance carry.",
    "Probability": 0.15,
    "Rationale": "Investors seek safety, leading to tighter spreads and improved carry in HQLA.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -20, "Curve": "bull_flattener", "IG_OAS": -8, "HY_OAS": -3, "MBS_Basis": -4},
    "Assumptions": "Market volatility leads investors to favor liquidity and safety."
  },
  {
    "Scenario": "Moderate Economic Growth with Limited Volatility",
    "Description": "Economic growth leads to stable liquidity conditions without significant volatility.",
    "Probability": 0.15,
    "Rationale": "Stable economic conditions support liquidity, allowing banks to maintain strong capital ratios.",
    "ImpactChannels": ["Deposits", "Regulation"],
    "Shocks": {"Rates": -10, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -5, "MBS_Basis": -2},
    "Assumptions": "The economy grows steadily without major disruptions."
  },
  {
    "Scenario": "Regulatory Stability with Enhanced Liquidity Standards",
    "Description": "Regulatory environment remains stable, enhancing liquidity requirements.",
    "Probability": 0.10,
    "Rationale": "Stability in regulations supports bank liquidity and confidence in HQLA.",
    "ImpactChannels": ["Regulation", "Deposits"],
    "Shocks": {"Rates": -5, "Curve": "flat", "IG_OAS": -3, "HY_OAS": -2, "MBS_Basis": -1},
    "Assumptions": "Regulatory environment does not introduce new risks; banks maintain strong liquidity."
  }
]
```

### **B**

**JSON**

```json
[
  {
    "Scenario": "Stable Inflation with Gradual Rate Cuts",
    "Description": "Inflation trends stabilize, leading to a gradual easing of monetary policy.",
    "Probability": 0.30,
    "Rationale": "Inflation expectations remain anchored, allowing the Fed to cut rates slowly.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -25, "Curve": "bull_flattener", "IG_OAS": -10, "HY_OAS": -5, "MBS_Basis": -5},
    "Assumptions": "Economic growth remains stable; inflation expectations are well-anchored."
  },
  {
    "Scenario": "Resilient Corporate Balance Sheets",
    "Description": "Strong corporate earnings support credit markets and stabilize spreads.",
    "Probability": 0.25,
    "Rationale": "Corporate balance sheets remain robust, leading to stable credit spreads.",
    "ImpactChannels": ["Credit", "Deposits"],
    "Shocks": {"Rates": -15, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -10, "MBS_Basis": -3},
    "Assumptions": "Corporate profitability supports liquidity and investor confidence."
  },
  {
    "Scenario": "Positive Carry in Short-Duration Treasuries",
    "Description": "Increased inflows into short-duration Treasuries enhance carry.",
    "Probability": 0.20,
    "Rationale": "Investors seek safety, leading to tighter spreads and improved carry in HQLA.",
    "ImpactChannels": ["Rates", "Credit"],
    "Shocks": {"Rates": -20, "Curve": "bull_flattener", "IG_OAS": -8, "HY_OAS": -3, "MBS_Basis": -4},
    "Assumptions": "Market volatility leads investors to favor liquidity and safety."
  },
  {
    "Scenario": "Moderate Economic Growth with Limited Volatility",
    "Description": "Economic growth leads to stable liquidity conditions without significant volatility.",
    "Probability": 0.15,
    "Rationale": "Stable economic conditions support liquidity, allowing banks to maintain strong capital ratios.",
    "ImpactChannels": ["Deposits", "Regulation"],
    "Shocks": {"Rates": -10, "Curve": "flat", "IG_OAS": -5, "HY_OAS": -5, "MBS_Basis": -2},
    "Assumptions": "The economy grows steadily without major disruptions."
  },
  {
    "Scenario": "Regulatory Stability with Enhanced Liquidity Standards",
    "Description": "Regulatory environment remains stable, enhancing liquidity requirements.",
    "Probability": 0.10,
    "Rationale": "Stability in regulations supports bank liquidity and confidence in HQLA.",
    "ImpactChannels": ["Regulation", "Deposits"],
    "Shocks": {"Rates": -5, "Curve": "flat", "IG_OAS": -3, "HY_OAS": -2, "MBS_Basis": -1},
    "Assumptions": "Regulatory environment does not introduce new risks; banks maintain strong liquidity."
  }
]
```

