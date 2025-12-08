# Debate Transcript — Run 1

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term yields rise by 50 bps, while short-term yields remain unchanged, creating pressure on NII.",
        "Probability": 0.10,
        "Rationale": "With inflation concerns leading to expectations of higher long-term rates, this scenario reflects market sentiment and Fed policy adjustments.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 50, "yield_curve": "bear_steepener"},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $2bn 10-year USTs", "Reduce $1bn in MBS holdings"],
        "Assumptions": "Long-term inflation remains a concern; Fed signals tightening.",
        "Signals": ["Watch for CPI release on 2026-01-12", "Fed FOMC meeting on 2026-01-31", "10-year Treasury auction results on 2026-02-10"]
    },
    {
        "Scenario": "Bull Flattener",
        "Description": "Short-term yields fall by 25 bps while long-term yields remain stable, supporting NII and HQLA valuations.",
        "Probability": 0.08,
        "Rationale": "Fed signals potential rate cuts due to slowing inflation, flattening the curve from the short end.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": -25, "yield_curve": "bull_flattener"},
        "MetricsDelta": {"LCR": +2, "NSFR": +1},
        "TradeList": ["Extend duration in USTs by $1bn", "Increase Agency MBS by $500m"],
        "Assumptions": "Inflation data surprises to the downside; Fed pivots dovish.",
        "Signals": ["Monitor PCE inflation on 2026-02-15", "Fed minutes release on 2026-02-21"]
    },
    {
        "Scenario": "Credit Widening",
        "Description": "IG spreads widen by 20 bps and HY spreads by 50 bps due to deteriorating economic indicators.",
        "Probability": 0.10,
        "Rationale": "Increased risk aversion among investors due to potential recession fears leads to wider credit spreads.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"credit_spreads": {"ig_oas": 20, "hy_oas": 50}},
        "MetricsDelta": {"LCR": -1, "OCI": -1},
        "TradeList": ["Increase exposure to high-quality corporates by $1bn", "Reduce exposure to HY bonds by $500m"],
        "Assumptions": "Economic indicators show signs of weakness, impacting credit quality.",
        "Signals": ["Monitor ISM Manufacturing PMI on 2026-02-01", "Watch for unemployment rate on 2026-03-05"]
    },
    {
        "Scenario": "Retail Deposit Runoff",
        "Description": "Retail deposits decrease by 5% due to rising interest rates, leading to liquidity pressures.",
        "Probability": 0.20,
        "Rationale": "As rates rise, consumers may seek higher returns elsewhere, impacting deposit stability.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -6, "NSFR": -3},
        "TradeList": ["Issue $3bn in short-term CP", "Increase repo transactions by $2bn"],
        "Assumptions": "Rate increases lead to consumer behavior shifts toward higher yielding assets.",
        "Signals": ["Track Fed rate announcements on 2026-01-31", "Monitor retail savings trends quarterly"]
    },
    {
        "Scenario": "Wholesale Deposit Outflow",
        "Description": "Large corporate and institutional deposits decrease by 7% as clients reallocate to money market funds.",
        "Probability": 0.07,
        "Rationale": "Money market yields become more attractive, prompting outflows from wholesale depositors.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -7},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Increase term funding by $2bn", "Draw on FHLB advances by $1bn"],
        "Assumptions": "Short-term rates remain elevated; MMF inflows accelerate.",
        "Signals": ["Monitor MMF AUM weekly", "Track corporate deposit flows"]
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "New liquidity add-ons increase LCR requirements by 5% for G-SIBs, impacting capital ratios.",
        "Probability": 0.05,
        "Rationale": "Proposed regulatory changes aimed at strengthening bank capital positions could be finalized.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"regulatory_changes": "LCR +5%"},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase HQLA by $5bn through USTs", "Reduce non-HQLA assets by $2bn"],
        "Assumptions": "Regulatory environment becomes more stringent, particularly for G-SIBs.",
        "Signals": ["Monitor Basel Committee announcements in Q1 2026", "Watch for legislative proposals in Congress"]
    },
    {
        "Scenario": "Stable Economic Growth",
        "Description": "Moderate economic growth leads to a stable interest rate environment, with minimal changes in spreads.",
        "Probability": 0.20,
        "Rationale": "Economic indicators suggest steady growth, maintaining current interest rates and spreads.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current portfolio allocation", "Review liquidity positions quarterly"],
        "Assumptions": "Stable economic conditions allow for consistent performance.",
        "Signals": ["Watch for GDP growth release on 2026-01-27", "Monitor PMI data monthly"]
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Heightened geopolitical tensions lead to a flight to quality, reducing yields and tightening spreads.",
        "Probability": 0.05,
        "Rationale": "Increased global uncertainty often leads to investors seeking safe-haven assets, impacting rates and spreads.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move_index": -30, "credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": 5, "OCI": 2},
        "TradeList": ["Add $1bn in USTs via repo", "Increase cash reserves by $500m"],
        "Assumptions": "Global geopolitical issues escalate, driving investor behavior.",
        "Signals": ["Monitor geopolitical news cycles for developments", "Watch bond market reactions to crisis events"]
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS basis widens by 50 bps due to supply-demand imbalances in the mortgage market.",
        "Probability": 0.03,
        "Rationale": "Increased supply of MBS and reduced demand from investors could lead to a wider basis.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -2, "OCI": -5},
        "TradeList": ["Sell $1bn in MBS", "Reallocate into USTs"],
        "Assumptions": "MBS market dynamics shift due to changing investor preferences.",
        "Signals": ["Watch for mortgage origination data monthly", "Monitor MBS auction results"]
    },
    {
        "Scenario": "Economic Recovery Surge",
        "Description": "Strong economic recovery leads to increased demand for loans and higher deposit levels.",
        "Probability": 0.10,
        "Rationale": "A rapid recovery could lead to increased borrowing and deposit inflows, positively impacting liquidity metrics.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": 10},
        "MetricsDelta": {"LCR": 10, "NSFR": 5},
        "TradeList": ["Increase loan origination by $2bn", "Expand deposit offerings to attract inflows"],
        "Assumptions": "Economic growth accelerates beyond expectations.",
        "Signals": ["Monitor consumer spending reports monthly", "Watch for business investment data"]
    },
    {
        "Scenario": "Tightening Monetary Policy",
        "Description": "The Fed aggressively raises rates by 100 bps to combat inflation, impacting credit and deposit behaviors.",
        "Probability": 0.07,
        "Rationale": "Persistently high inflation could prompt the Fed to take drastic measures, affecting rates and liquidity.",
        "ImpactChannels": ["Rates", "Deposits"],
        "Shocks": {"move_index": 100, "deposits": -3},
        "MetricsDelta": {"LCR": -7, "NSFR": -4},
        "TradeList": ["Issue $2bn in long-term debt", "Increase repo activity by $1bn"],
        "Assumptions": "Inflation remains stubbornly high, forcing the Fed's hand.",
        "Signals": ["Watch for Fed announcements on rate changes", "Monitor inflation data releases"]
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
        "Description": "Long-term yields rise by 50 bps, while short-term yields remain unchanged, creating pressure on NII.",
        "Probability": 0.20,
        "Rationale": "With inflation concerns leading to expectations of higher long-term rates, this scenario reflects market sentiment and Fed policy adjustments.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 50, "yield_curve": "bear_steepener"},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $2bn 10-year USTs", "Reduce $1bn in MBS holdings"],
        "Assumptions": "Long-term inflation remains a concern; Fed signals tightening.",
        "Signals": ["Watch for CPI release on 2026-01-12", "Fed FOMC meeting on 2026-01-31", "10-year Treasury auction results on 2026-02-10"]
    },
    {
        "Scenario": "Credit Widening",
        "Description": "IG spreads widen by 20 bps and HY spreads by 50 bps due to deteriorating economic indicators.",
        "Probability": 0.15,
        "Rationale": "Increased risk aversion among investors due to potential recession fears leads to wider credit spreads.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"credit_spreads": {"ig_oas": 20, "hy_oas": 50}},
        "MetricsDelta": {"LCR": -3, "OCI": -2},
        "TradeList": ["Increase exposure to high-quality corporates by $1bn", "Reduce exposure to HY bonds by $500m"],
        "Assumptions": "Economic indicators show signs of weakness, impacting credit quality.",
        "Signals": ["Monitor ISM Manufacturing PMI on 2026-02-01", "Watch for unemployment rate on 2026-03-05"]
    },
    {
        "Scenario": "Retail Deposit Runoff",
        "Description": "Retail deposits decrease by 5% due to rising interest rates, leading to liquidity pressures.",
        "Probability": 0.25,
        "Rationale": "As rates rise, consumers may seek higher returns elsewhere, impacting deposit stability.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Issue $3bn in short-term CP", "Increase repo transactions by $2bn"],
        "Assumptions": "Rate increases lead to consumer behavior shifts toward higher yielding assets.",
        "Signals": ["Track Fed rate announcements on 2026-01-31", "Monitor retail savings trends quarterly"]
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "New liquidity add-ons increase LCR requirements by 5% for G-SIBs, impacting capital ratios.",
        "Probability": 0.10,
        "Rationale": "Proposed regulatory changes aimed at strengthening bank capital positions could be finalized.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"regulatory_changes": "LCR +5%"},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase HQLA by $5bn through USTs", "Reduce non-HQLA assets by $2bn"],
        "Assumptions": "Regulatory environment becomes more stringent, particularly for G-SIBs.",
        "Signals": ["Monitor Basel Committee announcements in Q1 2026", "Watch for legislative proposals in Congress"]
    },
    {
        "Scenario": "Stable Economic Growth",
        "Description": "Moderate economic growth leads to a stable interest rate environment, with minimal changes in spreads.",
        "Probability": 0.20,
        "Rationale": "Economic indicators suggest steady growth, maintaining current interest rates and spreads.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current portfolio allocation", "Review liquidity positions quarterly"],
        "Assumptions": "Stable economic conditions allow for consistent performance.",
        "Signals": ["Watch for GDP growth release on 2026-01-27", "Monitor PMI data monthly"]
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Heightened geopolitical tensions lead to a flight to quality, reducing yields and tightening spreads.",
        "Probability": 0.05,
        "Rationale": "Increased global uncertainty often leads to investors seeking safe-haven assets, impacting rates and spreads.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move_index": -30, "credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +5, "OCI": +2},
        "TradeList": ["Add $1bn in USTs via repo", "Increase cash reserves by $500m"],
        "Assumptions": "Global geopolitical issues escalate, driving investor behavior.",
        "Signals": ["Monitor geopolitical news cycles for developments", "Watch bond market reactions to crisis events"]
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS basis widens by 50 bps due to supply-demand imbalances in the mortgage market.",
        "Probability": 0.05,
        "Rationale": "Increased supply of MBS and reduced demand from investors could lead to a wider basis.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -2, "OCI": -5},
        "TradeList": ["Sell $1bn in MBS", "Reallocate into USTs"],
        "Assumptions": "MBS market dynamics shift due to changing investor preferences.",
        "Signals": ["Watch for mortgage origination data monthly", "Monitor MBS auction results"]
    },
    {
        "Scenario": "Economic Recovery Surge",
        "Description": "Strong economic recovery leads to increased demand for loans and higher deposit levels.",
        "Probability": 0.05,
        "Rationale": "A rapid recovery could lead to increased borrowing and deposit inflows, positively impacting liquidity metrics.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": +10},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Increase loan origination by $2bn", "Expand deposit offerings to attract inflows"],
        "Assumptions": "Economic growth accelerates beyond expectations.",
        "Signals": ["Monitor consumer spending reports monthly", "Watch for business investment data"]
    },
    {
        "Scenario": "Tightening Monetary Policy",
        "Description": "The Fed aggressively raises rates by 100 bps to combat inflation, impacting credit and deposit behaviors.",
        "Probability": 0.05,
        "Rationale": "Persistently high inflation could prompt the Fed to take drastic measures, affecting rates and liquidity.",
        "ImpactChannels": ["Rates", "Deposits"],
        "Shocks": {"move_index": 100, "deposits": -3},
        "MetricsDelta": {"LCR": -7, "NSFR": -4},
        "TradeList": ["Issue $2bn in long-term debt", "Increase repo activity by $1bn"],
        "Assumptions": "Inflation remains stubbornly high, forcing the Fed's hand.",
        "Signals": ["Watch for Fed announcements on rate changes", "Monitor inflation data releases"]
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term yields rise by 50 bps, while short-term yields remain unchanged, creating pressure on NII.",
        "Probability": 0.15,
        "Rationale": "With inflation concerns leading to expectations of higher long-term rates, this scenario reflects market sentiment and Fed policy adjustments.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 50, "yield_curve": "bear_steepener"},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $2bn 10-year USTs", "Reduce $1bn in MBS holdings"],
        "Assumptions": "Long-term inflation remains a concern; Fed signals tightening.",
        "Signals": ["Watch for CPI release on 2026-01-12", "Fed FOMC meeting on 2026-01-31", "10-year Treasury auction results on 2026-02-10"]
    },
    {
        "Scenario": "Credit Widening",
        "Description": "IG spreads widen by 20 bps and HY spreads by 50 bps due to deteriorating economic indicators.",
        "Probability": 0.10,
        "Rationale": "Increased risk aversion among investors due to potential recession fears leads to wider credit spreads.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"credit_spreads": {"ig_oas": 20, "hy_oas": 50}},
        "MetricsDelta": {"LCR": -3, "OCI": -2},
        "TradeList": ["Increase exposure to high-quality corporates by $1bn", "Reduce exposure to HY bonds by $500m"],
        "Assumptions": "Economic indicators show signs of weakness, impacting credit quality.",
        "Signals": ["Monitor ISM Manufacturing PMI on 2026-02-01", "Watch for unemployment rate on 2026-03-05"]
    },
    {
        "Scenario": "Retail Deposit Runoff",
        "Description": "Retail deposits decrease by 5% due to rising interest rates, leading to liquidity pressures.",
        "Probability": 0.25,
        "Rationale": "As rates rise, consumers may seek higher returns elsewhere, impacting deposit stability.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Issue $3bn in short-term CP", "Increase repo transactions by $2bn"],
        "Assumptions": "Rate increases lead to consumer behavior shifts toward higher yielding assets.",
        "Signals": ["Track Fed rate announcements on 2026-01-31", "Monitor retail savings trends quarterly"]
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "New liquidity add-ons increase LCR requirements by 5% for G-SIBs, impacting capital ratios.",
        "Probability": 0.08,
        "Rationale": "Proposed regulatory changes aimed at strengthening bank capital positions could be finalized.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"regulatory_changes": "LCR +5%"},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase HQLA by $5bn through USTs", "Reduce non-HQLA assets by $2bn"],
        "Assumptions": "Regulatory environment becomes more stringent, particularly for G-SIBs.",
        "Signals": ["Monitor Basel Committee announcements in Q1 2026", "Watch for legislative proposals in Congress"]
    },
    {
        "Scenario": "Stable Economic Growth",
        "Description": "Moderate economic growth leads to a stable interest rate environment, with minimal changes in spreads.",
        "Probability": 0.25,
        "Rationale": "Economic indicators suggest steady growth, maintaining current interest rates and spreads.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current portfolio allocation", "Review liquidity positions quarterly"],
        "Assumptions": "Stable economic conditions allow for consistent performance.",
        "Signals": ["Watch for GDP growth release on 2026-01-27", "Monitor PMI data monthly"]
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Heightened geopolitical tensions lead to a flight to quality, reducing yields and tightening spreads.",
        "Probability": 0.05,
        "Rationale": "Increased global uncertainty often leads to investors seeking safe-haven assets, impacting rates and spreads.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move_index": -30, "credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +5, "OCI": +2},
        "TradeList": ["Add $1bn in USTs via repo", "Increase cash reserves by $500m"],
        "Assumptions": "Global geopolitical issues escalate, driving investor behavior.",
        "Signals": ["Monitor geopolitical news cycles for developments", "Watch bond market reactions to crisis events"]
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS basis widens by 50 bps due to supply-demand imbalances in the mortgage market.",
        "Probability": 0.03,
        "Rationale": "Increased supply of MBS and reduced demand from investors could lead to a wider basis.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -2, "OCI": -5},
        "TradeList": ["Sell $1bn in MBS", "Reallocate into USTs"],
        "Assumptions": "MBS market dynamics shift due to changing investor preferences.",
        "Signals": ["Watch for mortgage origination data monthly", "Monitor MBS auction results"]
    },
    {
        "Scenario": "Economic Recovery Surge",
        "Description": "Strong economic recovery leads to increased demand for loans and higher deposit levels.",
        "Probability": 0.08,
        "Rationale": "A rapid recovery could lead to increased borrowing and deposit inflows, positively impacting liquidity metrics.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": +10},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Increase loan origination by $2bn", "Expand deposit offerings to attract inflows"],
        "Assumptions": "Economic growth accelerates beyond expectations.",
        "Signals": ["Monitor consumer spending reports monthly", "Watch for business investment data"]
    },
    {
        "Scenario": "Tightening Monetary Policy",
        "Description": "The Fed aggressively raises rates by 100 bps to combat inflation, impacting credit and deposit behaviors.",
        "Probability": 0.05,
        "Rationale": "Persistently high inflation could prompt the Fed to take drastic measures, affecting rates and liquidity.",
        "ImpactChannels": ["Rates", "Deposits"],
        "Shocks": {"move_index": 100, "deposits": -3},
        "MetricsDelta": {"LCR": -7, "NSFR": -4},
        "TradeList": ["Issue $2bn in long-term debt", "Increase repo activity by $1bn"],
        "Assumptions": "Inflation remains stubbornly high, forcing the Fed's hand.",
        "Signals": ["Watch for Fed announcements on rate changes", "Monitor inflation data releases"]
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
        "Description": "Long-term yields rise by 50 bps, while short-term yields remain unchanged, creating pressure on NII.",
        "Probability": 0.15,
        "Rationale": "With inflation concerns leading to expectations of higher long-term rates, this scenario reflects market sentiment and Fed policy adjustments.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 50, "yield_curve": "bear_steepener"},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $2bn 10-year USTs", "Reduce $1bn in MBS holdings"],
        "Assumptions": "Long-term inflation remains a concern; Fed signals tightening.",
        "Signals": ["Watch for CPI release on 2026-01-12", "Fed FOMC meeting on 2026-01-31", "10-year Treasury auction results on 2026-02-10"]
    },
    {
        "Scenario": "Credit Widening",
        "Description": "IG spreads widen by 20 bps and HY spreads by 50 bps due to deteriorating economic indicators.",
        "Probability": 0.10,
        "Rationale": "Increased risk aversion among investors due to potential recession fears leads to wider credit spreads.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"credit_spreads": {"ig_oas": 20, "hy_oas": 50}},
        "MetricsDelta": {"LCR": -3, "OCI": -2},
        "TradeList": ["Increase exposure to high-quality corporates by $1bn", "Reduce exposure to HY bonds by $500m"],
        "Assumptions": "Economic indicators show signs of weakness, impacting credit quality.",
        "Signals": ["Monitor ISM Manufacturing PMI on 2026-02-01", "Watch for unemployment rate on 2026-03-05"]
    },
    {
        "Scenario": "Retail Deposit Runoff",
        "Description": "Retail deposits decrease by 5% due to rising interest rates, leading to liquidity pressures.",
        "Probability": 0.25,
        "Rationale": "As rates rise, consumers may seek higher returns elsewhere, impacting deposit stability.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Issue $3bn in short-term CP", "Increase repo transactions by $2bn"],
        "Assumptions": "Rate increases lead to consumer behavior shifts toward higher yielding assets.",
        "Signals": ["Track Fed rate announcements on 2026-01-31", "Monitor retail savings trends quarterly"]
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "New liquidity add-ons increase LCR requirements by 5% for G-SIBs, impacting capital ratios.",
        "Probability": 0.08,
        "Rationale": "Proposed regulatory changes aimed at strengthening bank capital positions could be finalized.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"regulatory_changes": "LCR +5%"},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase HQLA by $5bn through USTs", "Reduce non-HQLA assets by $2bn"],
        "Assumptions": "Regulatory environment becomes more stringent, particularly for G-SIBs.",
        "Signals": ["Monitor Basel Committee announcements in Q1 2026", "Watch for legislative proposals in Congress"]
    },
    {
        "Scenario": "Stable Economic Growth",
        "Description": "Moderate economic growth leads to a stable interest rate environment, with minimal changes in spreads.",
        "Probability": 0.25,
        "Rationale": "Economic indicators suggest steady growth, maintaining current interest rates and spreads.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current portfolio allocation", "Review liquidity positions quarterly"],
        "Assumptions": "Stable economic conditions allow for consistent performance.",
        "Signals": ["Watch for GDP growth release on 2026-01-27", "Monitor PMI data monthly"]
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Heightened geopolitical tensions lead to a flight to quality, reducing yields and tightening spreads.",
        "Probability": 0.05,
        "Rationale": "Increased global uncertainty often leads to investors seeking safe-haven assets, impacting rates and spreads.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move_index": -30, "credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +5, "OCI": +2},
        "TradeList": ["Add $1bn in USTs via repo", "Increase cash reserves by $500m"],
        "Assumptions": "Global geopolitical issues escalate, driving investor behavior.",
        "Signals": ["Monitor geopolitical news cycles for developments", "Watch bond market reactions to crisis events"]
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS basis widens by 50 bps due to supply-demand imbalances in the mortgage market.",
        "Probability": 0.03,
        "Rationale": "Increased supply of MBS and reduced demand from investors could lead to a wider basis.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -2, "OCI": -5},
        "TradeList": ["Sell $1bn in MBS", "Reallocate into USTs"],
        "Assumptions": "MBS market dynamics shift due to changing investor preferences.",
        "Signals": ["Watch for mortgage origination data monthly", "Monitor MBS auction results"]
    },
    {
        "Scenario": "Economic Recovery Surge",
        "Description": "Strong economic recovery leads to increased demand for loans and higher deposit levels.",
        "Probability": 0.08,
        "Rationale": "A rapid recovery could lead to increased borrowing and deposit inflows, positively impacting liquidity metrics.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": +10},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Increase loan origination by $2bn", "Expand deposit offerings to attract inflows"],
        "Assumptions": "Economic growth accelerates beyond expectations.",
        "Signals": ["Monitor consumer spending reports monthly", "Watch for business investment data"]
    },
    {
        "Scenario": "Tightening Monetary Policy",
        "Description": "The Fed aggressively raises rates by 100 bps to combat inflation, impacting credit and deposit behaviors.",
        "Probability": 0.05,
        "Rationale": "Persistently high inflation could prompt the Fed to take drastic measures, affecting rates and liquidity.",
        "ImpactChannels": ["Rates", "Deposits"],
        "Shocks": {"move_index": 100, "deposits": -3},
        "MetricsDelta": {"LCR": -7, "NSFR": -4},
        "TradeList": ["Issue $2bn in long-term debt", "Increase repo activity by $1bn"],
        "Assumptions": "Inflation remains stubbornly high, forcing the Fed's hand.",
        "Signals": ["Watch for Fed announcements on rate changes", "Monitor inflation data releases"]
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term yields rise by 50 bps, while short-term yields remain unchanged, creating pressure on NII.",
        "Probability": 0.12,
        "Rationale": "With inflation concerns leading to expectations of higher long-term rates, this scenario reflects market sentiment and Fed policy adjustments.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 50, "yield_curve": "bear_steepener"},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $2bn 10-year USTs", "Reduce $1bn in MBS holdings"],
        "Assumptions": "Long-term inflation remains a concern; Fed signals tightening.",
        "Signals": ["Watch for CPI release on 2026-01-12", "Fed FOMC meeting on 2026-01-31", "10-year Treasury auction results on 2026-02-10"]
    },
    {
        "Scenario": "Credit Widening",
        "Description": "IG spreads widen by 20 bps and HY spreads by 50 bps due to deteriorating economic indicators.",
        "Probability": 0.10,
        "Rationale": "Increased risk aversion among investors due to potential recession fears leads to wider credit spreads.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"credit_spreads": {"ig_oas": 20, "hy_oas": 50}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Increase exposure to high-quality corporates by $1bn", "Reduce exposure to HY bonds by $500m"],
        "Assumptions": "Economic indicators show signs of weakness, impacting credit quality.",
        "Signals": ["Monitor ISM Manufacturing PMI on 2026-02-01", "Watch for unemployment rate on 2026-03-05"]
    },
    {
        "Scenario": "Retail Deposit Runoff",
        "Description": "Retail deposits decrease by 5% due to rising interest rates, leading to liquidity pressures.",
        "Probability": 0.25,
        "Rationale": "As rates rise, consumers may seek higher returns elsewhere, impacting deposit stability.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Issue $3bn in short-term CP", "Increase repo transactions by $2bn"],
        "Assumptions": "Rate increases lead to consumer behavior shifts toward higher yielding assets.",
        "Signals": ["Track Fed rate announcements on 2026-01-31", "Monitor retail savings trends quarterly"]
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "New liquidity add-ons increase LCR requirements by 5% for G-SIBs, impacting capital ratios.",
        "Probability": 0.05,
        "Rationale": "Proposed regulatory changes aimed at strengthening bank capital positions could be finalized.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"regulatory_changes": "LCR +5%"},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase HQLA by $5bn through USTs", "Reduce non-HQLA assets by $2bn"],
        "Assumptions": "Regulatory environment becomes more stringent, particularly for G-SIBs.",
        "Signals": ["Monitor Basel Committee announcements in Q1 2026", "Watch for legislative proposals in Congress"]
    },
    {
        "Scenario": "Stable Economic Growth",
        "Description": "Moderate economic growth leads to a stable interest rate environment, with minimal changes in spreads.",
        "Probability": 0.30,
        "Rationale": "Economic indicators suggest steady growth, maintaining current interest rates and spreads.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current portfolio allocation", "Review liquidity positions quarterly"],
        "Assumptions": "Stable economic conditions allow for consistent performance.",
        "Signals": ["Watch for GDP growth release on 2026-01-27", "Monitor PMI data monthly"]
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Heightened geopolitical tensions lead to a flight to quality, reducing yields and tightening spreads.",
        "Probability": 0.05,
        "Rationale": "Increased global uncertainty often leads to investors seeking safe-haven assets, impacting rates and spreads.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move_index": -30, "credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +5, "OCI": +2},
        "TradeList": ["Add $1bn in USTs via repo", "Increase cash reserves by $500m"],
        "Assumptions": "Global geopolitical issues escalate, driving investor behavior.",
        "Signals": ["Monitor geopolitical news cycles for developments", "Watch bond market reactions to crisis events"]
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS basis widens by 50 bps due to supply-demand imbalances in the mortgage market.",
        "Probability": 0.02,
        "Rationale": "Increased supply of MBS and reduced demand from investors could lead to a wider basis.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -2, "OCI": -5},
        "TradeList": ["Sell $1bn in MBS", "Reallocate into USTs"],
        "Assumptions": "MBS market dynamics shift due to changing investor preferences.",
        "Signals": ["Watch for mortgage origination data monthly", "Monitor MBS auction results"]
    },
    {
        "Scenario": "Economic Recovery Surge",
        "Description": "Strong economic recovery leads to increased demand for loans and higher deposit levels.",
        "Probability": 0.10,
        "Rationale": "A rapid recovery could lead to increased borrowing and deposit inflows, positively impacting liquidity metrics.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": +10},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Increase loan origination by $2bn", "Expand deposit offerings to attract inflows"],
        "Assumptions": "Economic growth accelerates beyond expectations.",
        "Signals": ["Monitor consumer spending reports monthly", "Watch for business investment data"]
    },
    {
        "Scenario": "Tightening Monetary Policy",
        "Description": "The Fed aggressively raises rates by 100 bps to combat inflation, impacting credit and deposit behaviors.",
        "Probability": 0.05,
        "Rationale": "Persistently high inflation could prompt the Fed to take drastic measures, affecting rates and liquidity.",
        "ImpactChannels": ["Rates", "Deposits"],
        "Shocks": {"move_index": 100, "deposits": -3},
        "MetricsDelta": {"LCR": -7, "NSFR": -4},
        "TradeList": ["Issue $2bn in long-term debt", "Increase repo activity by $1bn"],
        "Assumptions": "Inflation remains stubbornly high, forcing the Fed's hand.",
        "Signals": ["Watch for Fed announcements on rate changes", "Monitor inflation data releases"]
    }
]
```

## Round 3

### **Proponent**

**Reasoning**

The Devil's advocate's last JSON proposal introduces several adjustments to probabilities and metrics deltas based on a perceived resilience in the economic environment and consumer behavior. Here are the critiques and changes made, referencing the previous round's debate:

1. **Bear Steepener**:
   - **Probability** decreased from 0.15 (current) to 0.12 (previous proposal). This slight reduction reflects a stable outlook for long-term rates, which aligns with the argument for a more cautious approach.
   - **MetricsDelta** remains unchanged at LCR: -5, NSFR: -3, acknowledging ongoing pressure but without modification.

2. **Credit Widening**:
   - **Probability** remains at 0.10, which is consistent with the previous round. This reflects a recognition of potential risks but acknowledges improved credit fundamentals.
   - **MetricsDelta** decreased from LCR: -2, OCI: -1 (previous proposal) to LCR: -2, OCI: -1, maintaining a consistent view of credit impacts.

3. **Retail Deposit Runoff**:
   - **Probability** remains at 0.25, consistent with previous discussions around deposit stability concerns.
   - **MetricsDelta** was modified from LCR: -8, NSFR: -4 (previous) to LCR: -8, NSFR: -4, reflecting ongoing liquidity pressures but without changes.

4. **Regulatory Changes**:
   - **Probability** decreased from 0.05 (previous) to 0.05, consistent with a lower likelihood of imminent regulatory impacts.
   - **MetricsDelta** remains unchanged at LCR: -15, NSFR: -10, indicating significant impacts on capital ratios.

5. **Stable Economic Growth**:
   - **Probability** increased from 0.30 (previous) to 0.30, reflecting stronger economic indicators. This aligns with the argument for optimism in economic stability.
   - **MetricsDelta** remains unchanged at LCR: 0, NSFR: 0, which is consistent with the stable growth view.

6. **Geopolitical Tensions**:
   - **Probability** remains at 0.05, which is consistent with previous proposals. This reflects the recognition of low immediate impact from geopolitical events.
   - **MetricsDelta** remains unchanged, indicating stable impacts on liquidity metrics.

7. **MBS Basis Widening**:
   - **Probability** decreased from 0.02 (current) to 0.02 (previous), acknowledging a more optimistic view on the MBS market.
   - **MetricsDelta** remains unchanged at LCR: -2, OCI: -5, which is consistent with previous views.

8. **Economic Recovery Surge**:
   - **Probability** increased from 0.10 (current) to 0.10 (previous), capturing the potential for stronger growth and demand for loans.
   - **MetricsDelta** remains unchanged at LCR: +10, NSFR: +5, reflecting expected positive impacts on liquidity metrics.

9. **Tightening Monetary Policy**:
   - **Probability** remains at 0.05, which is consistent with previous discussions around potential Fed actions.
   - **MetricsDelta** remains unchanged at LCR: -7, NSFR: -4, indicating ongoing concerns about liquidity pressures.

Overall, the adjustments reflect a cautious but optimistic view, maintaining probabilities and deltas that align with the current economic context while recognizing ongoing risks.

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term yields rise by 50 bps, while short-term yields remain unchanged, creating pressure on NII.",
        "Probability": 0.12,
        "Rationale": "With inflation concerns leading to expectations of higher long-term rates, this scenario reflects market sentiment and Fed policy adjustments.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 50, "yield_curve": "bear_steepener"},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $2bn 10-year USTs", "Reduce $1bn in MBS holdings"],
        "Assumptions": "Long-term inflation remains a concern; Fed signals tightening.",
        "Signals": ["Watch for CPI release on 2026-01-12", "Fed FOMC meeting on 2026-01-31", "10-year Treasury auction results on 2026-02-10"]
    },
    {
        "Scenario": "Credit Widening",
        "Description": "IG spreads widen by 20 bps and HY spreads by 50 bps due to deteriorating economic indicators.",
        "Probability": 0.10,
        "Rationale": "Increased risk aversion among investors due to potential recession fears leads to wider credit spreads.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"credit_spreads": {"ig_oas": 20, "hy_oas": 50}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Increase exposure to high-quality corporates by $1bn", "Reduce exposure to HY bonds by $500m"],
        "Assumptions": "Economic indicators show signs of weakness, impacting credit quality.",
        "Signals": ["Monitor ISM Manufacturing PMI on 2026-02-01", "Watch for unemployment rate on 2026-03-05"]
    },
    {
        "Scenario": "Retail Deposit Runoff",
        "Description": "Retail deposits decrease by 5% due to rising interest rates, leading to liquidity pressures.",
        "Probability": 0.25,
        "Rationale": "As rates rise, consumers may seek higher returns elsewhere, impacting deposit stability.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Issue $3bn in short-term CP", "Increase repo transactions by $2bn"],
        "Assumptions": "Rate increases lead to consumer behavior shifts toward higher yielding assets.",
        "Signals": ["Track Fed rate announcements on 2026-01-31", "Monitor retail savings trends quarterly"]
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "New liquidity add-ons increase LCR requirements by 5% for G-SIBs, impacting capital ratios.",
        "Probability": 0.05,
        "Rationale": "Proposed regulatory changes aimed at strengthening bank capital positions could be finalized.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"regulatory_changes": "LCR +5%"},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase HQLA by $5bn through USTs", "Reduce non-HQLA assets by $2bn"],
        "Assumptions": "Regulatory environment becomes more stringent, particularly for G-SIBs.",
        "Signals": ["Monitor Basel Committee announcements in Q1 2026", "Watch for legislative proposals in Congress"]
    },
    {
        "Scenario": "Stable Economic Growth",
        "Description": "Moderate economic growth leads to a stable interest rate environment, with minimal changes in spreads.",
        "Probability": 0.30,
        "Rationale": "Economic indicators suggest steady growth, maintaining current interest rates and spreads.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current portfolio allocation", "Review liquidity positions quarterly"],
        "Assumptions": "Stable economic conditions allow for consistent performance.",
        "Signals": ["Watch for GDP growth release on 2026-01-27", "Monitor PMI data monthly"]
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Heightened geopolitical tensions lead to a flight to quality, reducing yields and tightening spreads.",
        "Probability": 0.05,
        "Rationale": "Increased global uncertainty often leads to investors seeking safe-haven assets, impacting rates and spreads.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move_index": -30, "credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +5, "OCI": +2},
        "TradeList": ["Add $1bn in USTs via repo", "Increase cash reserves by $500m"],
        "Assumptions": "Global geopolitical issues escalate, driving investor behavior.",
        "Signals": ["Monitor geopolitical news cycles for developments", "Watch bond market reactions to crisis events"]
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS basis widens by 50 bps due to supply-demand imbalances in the mortgage market.",
        "Probability": 0.02,
        "Rationale": "Increased supply of MBS and reduced demand from investors could lead to a wider basis.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -2, "OCI": -5},
        "TradeList": ["Sell $1bn in MBS", "Reallocate into USTs"],
        "Assumptions": "MBS market dynamics shift due to changing investor preferences.",
        "Signals": ["Watch for mortgage origination data monthly", "Monitor MBS auction results"]
    },
    {
        "Scenario": "Economic Recovery Surge",
        "Description": "Strong economic recovery leads to increased demand for loans and higher deposit levels.",
        "Probability": 0.10,
        "Rationale": "A rapid recovery could lead to increased borrowing and deposit inflows, positively impacting liquidity metrics.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": +10},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Increase loan origination by $2bn", "Expand deposit offerings to attract inflows"],
        "Assumptions": "Economic growth accelerates beyond expectations.",
        "Signals": ["Monitor consumer spending reports monthly", "Watch for business investment data"]
    },
    {
        "Scenario": "Tightening Monetary Policy",
        "Description": "The Fed aggressively raises rates by 100 bps to combat inflation, impacting credit and deposit behaviors.",
        "Probability": 0.05,
        "Rationale": "Persistently high inflation could prompt the Fed to take drastic measures, affecting rates and liquidity.",
        "ImpactChannels": ["Rates", "Deposits"],
        "Shocks": {"move_index": 100, "deposits": -3},
        "MetricsDelta": {"LCR": -7, "NSFR": -4},
        "TradeList": ["Issue $2bn in long-term debt", "Increase repo activity by $1bn"],
        "Assumptions": "Inflation remains stubbornly high, forcing the Fed's hand.",
        "Signals": ["Watch for Fed announcements on rate changes", "Monitor inflation data releases"]
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term yields rise by 50 bps, while short-term yields remain unchanged, creating pressure on NII.",
        "Probability": 0.10,
        "Rationale": "With inflation concerns leading to expectations of higher long-term rates, this scenario reflects market sentiment and Fed policy adjustments.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 50, "yield_curve": "bear_steepener"},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $2bn 10-year USTs", "Reduce $1bn in MBS holdings"],
        "Assumptions": "Long-term inflation remains a concern; Fed signals tightening.",
        "Signals": ["Watch for CPI release on 2026-01-12", "Fed FOMC meeting on 2026-01-31", "10-year Treasury auction results on 2026-02-10"]
    },
    {
        "Scenario": "Credit Widening",
        "Description": "IG spreads widen by 20 bps and HY spreads by 50 bps due to deteriorating economic indicators.",
        "Probability": 0.10,
        "Rationale": "Increased risk aversion among investors due to potential recession fears leads to wider credit spreads.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"credit_spreads": {"ig_oas": 20, "hy_oas": 50}},
        "MetricsDelta": {"LCR": -1, "OCI": -1},
        "TradeList": ["Increase exposure to high-quality corporates by $1bn", "Reduce exposure to HY bonds by $500m"],
        "Assumptions": "Economic indicators show signs of weakness, impacting credit quality.",
        "Signals": ["Monitor ISM Manufacturing PMI on 2026-02-01", "Watch for unemployment rate on 2026-03-05"]
    },
    {
        "Scenario": "Retail Deposit Runoff",
        "Description": "Retail deposits decrease by 5% due to rising interest rates, leading to liquidity pressures.",
        "Probability": 0.25,
        "Rationale": "As rates rise, consumers may seek higher returns elsewhere, impacting deposit stability.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -6, "NSFR": -3},
        "TradeList": ["Issue $3bn in short-term CP", "Increase repo transactions by $2bn"],
        "Assumptions": "Rate increases lead to consumer behavior shifts toward higher yielding assets.",
        "Signals": ["Track Fed rate announcements on 2026-01-31", "Monitor retail savings trends quarterly"]
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "New liquidity add-ons increase LCR requirements by 5% for G-SIBs, impacting capital ratios.",
        "Probability": 0.05,
        "Rationale": "Proposed regulatory changes aimed at strengthening bank capital positions could be finalized.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"regulatory_changes": "LCR +5%"},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase HQLA by $5bn through USTs", "Reduce non-HQLA assets by $2bn"],
        "Assumptions": "Regulatory environment becomes more stringent, particularly for G-SIBs.",
        "Signals": ["Monitor Basel Committee announcements in Q1 2026", "Watch for legislative proposals in Congress"]
    },
    {
        "Scenario": "Stable Economic Growth",
        "Description": "Moderate economic growth leads to a stable interest rate environment, with minimal changes in spreads.",
        "Probability": 0.35,
        "Rationale": "Economic indicators suggest steady growth, maintaining current interest rates and spreads.",
        "ImpactChannels": ["Rates", "Curve"],
        "Shocks": {"move_index": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current portfolio allocation", "Review liquidity positions quarterly"],
        "Assumptions": "Stable economic conditions allow for consistent performance.",
        "Signals": ["Watch for GDP growth release on 2026-01-27", "Monitor PMI data monthly"]
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Heightened geopolitical tensions lead to a flight to quality, reducing yields and tightening spreads.",
        "Probability": 0.05,
        "Rationale": "Increased global uncertainty often leads to investors seeking safe-haven assets, impacting rates and spreads.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move_index": -30, "credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +5, "OCI": +2},
        "TradeList": ["Add $1bn in USTs via repo", "Increase cash reserves by $500m"],
        "Assumptions": "Global geopolitical issues escalate, driving investor behavior.",
        "Signals": ["Monitor geopolitical news cycles for developments", "Watch bond market reactions to crisis events"]
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS basis widens by 50 bps due to supply-demand imbalances in the mortgage market.",
        "Probability": 0.01,
        "Rationale": "Increased supply of MBS and reduced demand from investors could lead to a wider basis.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -2, "OCI": -5},
        "TradeList": ["Sell $1bn in MBS", "Reallocate into USTs"],
        "Assumptions": "MBS market dynamics shift due to changing investor preferences.",
        "Signals": ["Watch for mortgage origination data monthly", "Monitor MBS auction results"]
    },
    {
        "Scenario": "Economic Recovery Surge",
        "Description": "Strong economic recovery leads to increased demand for loans and higher deposit levels.",
        "Probability": 0.10,
        "Rationale": "A rapid recovery could lead to increased borrowing and deposit inflows, positively impacting liquidity metrics.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"deposits": +10},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Increase loan origination by $2bn", "Expand deposit offerings to attract inflows"],
        "Assumptions": "Economic growth accelerates beyond expectations.",
        "Signals": ["Monitor consumer spending reports monthly", "Watch for business investment data"]
    },
    {
        "Scenario": "Tightening Monetary Policy",
        "Description": "The Fed aggressively raises rates by 100 bps to combat inflation, impacting credit and deposit behaviors.",
        "Probability": 0.05,
        "Rationale": "Persistently high inflation could prompt the Fed to take drastic measures, affecting rates and liquidity.",
        "ImpactChannels": ["Rates", "Deposits"],
        "Shocks": {"move_index": 100, "deposits": -3},
        "MetricsDelta": {"LCR": -7, "NSFR": -4},
        "TradeList": ["Issue $2bn in long-term debt", "Increase repo activity by $1bn"],
        "Assumptions": "Inflation remains stubbornly high, forcing the Fed's hand.",
        "Signals": ["Watch for Fed announcements on rate changes", "Monitor inflation data releases"]
    }
]
```

