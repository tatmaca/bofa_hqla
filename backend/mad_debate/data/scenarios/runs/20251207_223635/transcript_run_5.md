# Debate Transcript — Run 5

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term interest rates rise due to inflationary pressures, steepening the yield curve.",
        "Probability": 0.20,
        "Rationale": "Current inflation trends suggest potential Fed adjustments, impacting long-term borrowing costs.",
        "ImpactChannels": ["Rates: +50 bps", "Curve: bear steepener"],
        "Shocks": {"move": 50, "slope_2s10s_bps": 50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $2bn in long-term USTs", "Reduce $1bn short-term repo exposure"],
        "Assumptions": "Inflation remains persistent, Fed signals a tightening approach."
    },
    {
        "Scenario": "Widening Credit Spreads",
        "Description": "Credit spreads widen by 25 bps in IG and 50 bps in HY due to heightened risk aversion.",
        "Probability": 0.25,
        "Rationale": "Economic uncertainty may lead to wider spreads, impacting portfolio valuations.",
        "ImpactChannels": ["Credit OAS: IG +25 bps, HY +50 bps"],
        "Shocks": {"ig_oas": 25, "hy_oas": 50},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase liquidity buffer by $1bn through repo", "Monitor corporate exposure closely"],
        "Assumptions": "Increased risk aversion persists in the market."
    },
    {
        "Scenario": "Funding Pressure from Deposit Runoff",
        "Description": "Increased interest rates lead to significant runoff in deposits, affecting funding stability.",
        "Probability": 0.20,
        "Rationale": "As rates rise, consumers may seek better returns, impacting Bank of America's funding stack.",
        "ImpactChannels": ["Deposit outflows increase", "Funding costs rise"],
        "Shocks": {"depo_beta": -5},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Extend maturity on $1bn in wholesale funding", "Enhance retail deposit offerings"],
        "Assumptions": "Depositor behavior shifts due to competitive rate offerings."
    },
    {
        "Scenario": "Stricter Regulatory Environment",
        "Description": "Potential implementation of stricter liquidity requirements impacts funding costs.",
        "Probability": 0.15,
        "Rationale": "Ongoing discussions around Basel reforms could lead to tighter liquidity requirements.",
        "ImpactChannels": ["Increased capital requirements", "Higher compliance costs"],
        "Shocks": {"move_index": 0},
        "MetricsDelta": {"LCR": -5, "NSFR": -4},
        "TradeList": ["Prepare for $1bn increase in TLAC requirements", "Review capital structure"],
        "Assumptions": "Regulatory environment becomes more stringent."
    },
    {
        "Scenario": "Geopolitical Risks Heightened",
        "Description": "Escalation in geopolitical tensions leads to increased market volatility and demand for safe-haven assets.",
        "Probability": 0.10,
        "Rationale": "Increased geopolitical risks could lead to liquidity challenges despite temporary asset boosts.",
        "ImpactChannels": ["Rates react negatively, credit spreads widen"],
        "Shocks": {"move": -30},
        "MetricsDelta": {"LCR": 2, "NSFR": 1},
        "TradeList": ["Add $1bn in USTs through market operations", "Evaluate credit risk exposure"],
        "Assumptions": "Geopolitical tensions escalate, creating market instability."
    },
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Inflation remains stable, allowing for gradual easing of monetary policy, supporting consumer spending.",
        "Probability": 0.10,
        "Rationale": "Resilient consumer behavior and stable inflation suggest ongoing economic growth but with caution.",
        "ImpactChannels": ["Consumer spending remains robust", "Stable loan demand"],
        "Shocks": {"move": 25},
        "MetricsDelta": {"LCR": 1, "NSFR": 1},
        "TradeList": ["Increase allocation to Agency MBS by $1bn", "Rebalance towards consumer loans"],
        "Assumptions": "Economic growth continues at a steady pace but with risks of inflation."
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
        "Description": "Long-term interest rates rise due to inflationary pressures, steepening the yield curve.",
        "Probability": 0.30,
        "Rationale": "Current inflation trends suggest potential Fed adjustments, impacting long-term borrowing costs.",
        "ImpactChannels": ["Rates: +50 bps", "Curve: bear steepener"],
        "Shocks": {"move": 50, "slope_2s10s_bps": +50},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Add $2bn in long-term USTs", "Reduce $1bn short-term repo exposure"],
        "Assumptions": "Inflation remains persistent, Fed signals a tightening approach."
    },
    {
        "Scenario": "Widening Credit Spreads",
        "Description": "Credit spreads widen by 15 bps in IG and 45 bps in HY due to heightened risk aversion.",
        "Probability": 0.25,
        "Rationale": "Economic uncertainty may lead to increased corporate defaults, impacting risk premiums.",
        "ImpactChannels": ["Credit OAS: IG +15 bps, HY +45 bps"],
        "Shocks": {"ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Increase liquidity buffer by $1bn through repo", "Monitor corporate exposure closely"],
        "Assumptions": "Increased risk aversion persists in the market."
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "Potential implementation of Basel Endgame liquidity requirements impacting funding costs.",
        "Probability": 0.20,
        "Rationale": "Ongoing discussions around Basel reforms could lead to tighter liquidity requirements for G-SIBs.",
        "ImpactChannels": ["Reg changes: potential TLAC increase"],
        "Shocks": {"move_index": 0},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Prepare for $1bn increase in TLAC requirements", "Review capital structure"],
        "Assumptions": "Regulatory environment becomes stricter."
    },
    {
        "Scenario": "Deposit Behavior Shift",
        "Description": "Significant runoff in wealth management deposits as rates rise, impacting funding stability.",
        "Probability": 0.15,
        "Rationale": "Retail depositors may seek higher returns elsewhere as interest rates rise.",
        "ImpactChannels": ["Deposits: -5% runoff"],
        "Shocks": {"depo_beta": -5},
        "MetricsDelta": {"LCR": -5, "NSFR": -4},
        "TradeList": ["Increase retail deposit rates by 25 bps", "Enhance marketing for deposit products"],
        "Assumptions": "Retail depositors react strongly to rate changes."
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Escalation in geopolitical tensions leads to increased demand for USTs, impacting liquidity metrics positively.",
        "Probability": 0.10,
        "Rationale": "Increased demand for safe-haven assets could provide a temporary liquidity boost.",
        "ImpactChannels": ["Rates: -30 bps, Credit: tighter spreads"],
        "Shocks": {"move": -30},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Add $1bn in USTs through market operations", "Evaluate credit risk exposure"],
        "Assumptions": "Geopolitical risks escalate, leading to market flight to safety."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Inflation remains stable, allowing for gradual easing of monetary policy, supporting consumer spending.",
        "Probability": 0.35,
        "Rationale": "Resilient consumer behavior and stable inflation indicate ongoing economic growth.",
        "ImpactChannels": ["Consumer spending remains robust", "Stable loan demand"],
        "Shocks": {"move": 25},
        "MetricsDelta": {"LCR": 2, "NSFR": 1},
        "TradeList": ["Increase allocation to Agency MBS by $2bn", "Rebalance towards consumer loans"],
        "Assumptions": "Economic growth continues at a steady pace."
    },
    {
        "Scenario": "Diversified Funding Stack",
        "Description": "Strong mix of retail and wholesale funding mitigates risks associated with deposit runoff.",
        "Probability": 0.30,
        "Rationale": "A well-diversified funding stack supports liquidity and reduces reliance on any single source.",
        "ImpactChannels": ["Stable deposit flows", "Reduced funding costs"],
        "Shocks": {"depo_beta": 0},
        "MetricsDelta": {"LCR": 3, "NSFR": 2},
        "TradeList": ["Extend maturity on $1bn in wholesale funding", "Enhance retail deposit offerings"],
        "Assumptions": "Depositor behavior remains stable despite rate changes."
    },
    {
        "Scenario": "Tighter Credit Spreads",
        "Description": "Increased investor confidence leads to tighter spreads across sectors, benefiting Bank of America's portfolio.",
        "Probability": 0.20,
        "Rationale": "A favorable macroeconomic outlook can lead to reduced risk premiums in credit markets.",
        "ImpactChannels": ["Tighter OAS on investment-grade bonds", "Improved asset valuations"],
        "Shocks": {"ig_oas": -10},
        "MetricsDelta": {"LCR": 4, "NSFR": 3},
        "TradeList": ["Rotate into higher-rated corporate bonds", "Optimize asset allocation towards tighter spread sectors"],
        "Assumptions": "Investor sentiment improves in response to economic indicators."
    },
    {
        "Scenario": "Regulatory Relief",
        "Description": "Potential regulatory changes lead to reduced liquidity requirements, benefiting capital ratios.",
        "Probability": 0.10,
        "Rationale": "Ongoing discussions around regulatory reforms could ease capital constraints for G-SIBs.",
        "ImpactChannels": ["Lower TLAC requirements", "Increased flexibility in capital management"],
        "Shocks": {"move_index": 0},
        "MetricsDelta": {"LCR": 5, "NSFR": 4},
        "TradeList": ["Prepare for potential capital optimization strategies", "Evaluate impact of regulatory changes on funding"],
        "Assumptions": "Regulatory environment becomes more favorable for banks."
    },
    {
        "Scenario": "Stable Deposit Betas",
        "Description": "Deposit betas remain stable despite rising interest rates, preserving net interest income.",
        "Probability": 0.05,
        "Rationale": "Consumers may prioritize liquidity over yield in uncertain environments, maintaining stable deposit levels.",
        "ImpactChannels": ["Stable funding costs", "Preserved margins"],
        "Shocks": {"depo_beta": 0},
        "MetricsDelta": {"LCR": 1, "NSFR": 1},
        "TradeList": ["Monitor deposit rates closely", "Enhance customer engagement to retain deposits"],
        "Assumptions": "Consumer behavior remains conservative amid rate hikes."
    }
]
```

## Round 2

### **Proponent**

**Reasoning**

The Devil's Advocate's JSON scenarios present a generally optimistic outlook on Bank of America's liquidity and capital position, which may not fully account for potential risks in the current economic environment. While the scenarios emphasize stability and resilience, they tend to underplay significant market volatility and the impact of rising interest rates on consumer behavior and funding costs. 

1. The probability allocations suggest an overly positive view of the economic outlook, especially given the potential for external shocks (e.g., geopolitical tensions or unexpected monetary policy shifts) that could negatively impact liquidity metrics and credit spreads. The reliance on stable consumer behavior in a rising rate environment may be overly optimistic, as consumers may react unpredictably.

2. The scenario of "Tighter Credit Spreads" does not consider that credit spreads could widen due to economic stress or a downturn, which would negatively impact the bank's capital ratios and HQLA valuations. This scenario's probability may be inflated relative to potential risks.

3. The "Regulatory Relief" scenario assumes a favorable regulatory environment that may not materialize, particularly with ongoing pressures for banks to maintain higher capital and liquidity standards. This reflects a lack of acknowledgment of potential regulatory headwinds that could arise from increasing scrutiny on G-SIBs.

4. The "Stable Deposit Betas" scenario is overly simplistic in assuming that depositors will prioritize liquidity over yield. In a competitive environment with rising interest rates, banks may need to increase deposit rates significantly, which could compress margins and affect net interest income (NII).

5. The overall structure of the scenarios lacks a comprehensive approach to managing risk. While the focus on positive outcomes is beneficial, it does not sufficiently address potential adverse scenarios that could significantly impact the bank's liquidity and capital ratios.

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Inflation remains stable, allowing for gradual easing of monetary policy, supporting consumer spending.",
        "Probability": 0.20,
        "Rationale": "Resilient consumer behavior and stable inflation suggest ongoing economic growth but with caution.",
        "ImpactChannels": ["Consumer spending remains robust", "Stable loan demand"],
        "Shocks": {"move": 25},
        "MetricsDelta": {"LCR": 2, "NSFR": 1},
        "TradeList": ["Increase allocation to Agency MBS by $1bn", "Rebalance towards consumer loans"],
        "Assumptions": "Economic growth continues at a steady pace but with risks of inflation."
    },
    {
        "Scenario": "Diversified Funding Stack",
        "Description": "Strong mix of retail and wholesale funding mitigates risks associated with deposit runoff.",
        "Probability": 0.25,
        "Rationale": "A well-diversified funding stack supports liquidity and reduces reliance on any single source.",
        "ImpactChannels": ["Stable deposit flows", "Reduced funding costs"],
        "Shocks": {"depo_beta": 0},
        "MetricsDelta": {"LCR": 3, "NSFR": 2},
        "TradeList": ["Extend maturity on $1bn in wholesale funding", "Enhance retail deposit offerings"],
        "Assumptions": "Depositor behavior remains stable despite rate changes."
    },
    {
        "Scenario": "Widening Credit Spreads",
        "Description": "Credit spreads widen by 20 bps in IG and 50 bps in HY due to heightened risk aversion.",
        "Probability": 0.25,
        "Rationale": "Increased economic uncertainty may lead to wider spreads, impacting portfolio valuations.",
        "ImpactChannels": ["Credit OAS: IG +20 bps, HY +50 bps"],
        "Shocks": {"ig_oas": 20, "hy_oas": 50},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Increase liquidity buffer by $1bn through repo", "Monitor corporate exposure closely"],
        "Assumptions": "Increased risk aversion persists in the market."
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "Potential implementation of Basel Endgame liquidity requirements impacting funding costs.",
        "Probability": 0.20,
        "Rationale": "Ongoing discussions around Basel reforms could lead to tighter liquidity requirements for G-SIBs.",
        "ImpactChannels": ["Reg changes: potential TLAC increase"],
        "Shocks": {"move_index": 0},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Prepare for $1bn increase in TLAC requirements", "Review capital structure"],
        "Assumptions": "Regulatory environment becomes stricter."
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Escalation in geopolitical tensions leads to increased demand for USTs, impacting liquidity metrics positively.",
        "Probability": 0.10,
        "Rationale": "Increased demand for safe-haven assets could provide a temporary liquidity boost.",
        "ImpactChannels": ["Rates: -30 bps, Credit: tighter spreads"],
        "Shocks": {"move": -30},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Add $1bn in USTs through market operations", "Evaluate credit risk exposure"],
        "Assumptions": "Geopolitical risks escalate, leading to market flight to safety."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Inflation remains stable, allowing for gradual easing of monetary policy, supporting consumer spending.",
        "Probability": 0.20,
        "Rationale": "Resilient consumer behavior and stable inflation suggest ongoing economic growth but with caution.",
        "ImpactChannels": ["Consumer spending remains robust", "Stable loan demand"],
        "Shocks": {"move": 25},
        "MetricsDelta": {"LCR": 2, "NSFR": 1},
        "TradeList": ["Increase allocation to Agency MBS by $1bn", "Rebalance towards consumer loans"],
        "Assumptions": "Economic growth continues at a steady pace but with risks of inflation."
    },
    {
        "Scenario": "Diversified Funding Stack",
        "Description": "Strong mix of retail and wholesale funding mitigates risks associated with deposit runoff.",
        "Probability": 0.25,
        "Rationale": "A well-diversified funding stack supports liquidity and reduces reliance on any single source.",
        "ImpactChannels": ["Stable deposit flows", "Reduced funding costs"],
        "Shocks": {"depo_beta": 0},
        "MetricsDelta": {"LCR": 3, "NSFR": 2},
        "TradeList": ["Extend maturity on $1bn in wholesale funding", "Enhance retail deposit offerings"],
        "Assumptions": "Depositor behavior remains stable despite rate changes."
    },
    {
        "Scenario": "Widening Credit Spreads",
        "Description": "Credit spreads widen by 20 bps in IG and 50 bps in HY due to heightened risk aversion.",
        "Probability": 0.25,
        "Rationale": "Increased economic uncertainty may lead to wider spreads, impacting portfolio valuations.",
        "ImpactChannels": ["Credit OAS: IG +20 bps, HY +50 bps"],
        "Shocks": {"ig_oas": 20, "hy_oas": 50},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Increase liquidity buffer by $1bn through repo", "Monitor corporate exposure closely"],
        "Assumptions": "Increased risk aversion persists in the market."
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "Potential implementation of Basel Endgame liquidity requirements impacting funding costs.",
        "Probability": 0.20,
        "Rationale": "Ongoing discussions around Basel reforms could lead to tighter liquidity requirements for G-SIBs.",
        "ImpactChannels": ["Reg changes: potential TLAC increase"],
        "Shocks": {"move_index": 0},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Prepare for $1bn increase in TLAC requirements", "Review capital structure"],
        "Assumptions": "Regulatory environment becomes stricter."
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Escalation in geopolitical tensions leads to increased demand for USTs, impacting liquidity metrics positively.",
        "Probability": 0.10,
        "Rationale": "Increased demand for safe-haven assets could provide a temporary liquidity boost.",
        "ImpactChannels": ["Rates: -30 bps, Credit: tighter spreads"],
        "Shocks": {"move": -30},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Add $1bn in USTs through market operations", "Evaluate credit risk exposure"],
        "Assumptions": "Geopolitical risks escalate, leading to market flight to safety."
    }
]
```

## Round 3

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Inflation remains stable, allowing for gradual easing of monetary policy, supporting consumer spending.",
        "Probability": 0.15,
        "Rationale": "While consumer behavior shows resilience, inflationary pressures could lead to tightening.",
        "ImpactChannels": ["Consumer spending stabilizes", "Loan demand fluctuates"],
        "Shocks": {"move": 25},
        "MetricsDelta": {"LCR": 1, "NSFR": 1},
        "TradeList": ["Increase allocation to Agency MBS by $1bn", "Rebalance towards consumer loans"],
        "Assumptions": "Economic growth is steady but faces inflationary risks."
    },
    {
        "Scenario": "Diversified Funding Stack",
        "Description": "Strong mix of retail and wholesale funding mitigates risks associated with deposit runoff.",
        "Probability": 0.20,
        "Rationale": "A diversified funding stack supports liquidity but could be tested by rising rates.",
        "ImpactChannels": ["Stable deposit flows", "Potential funding cost increases"],
        "Shocks": {"depo_beta": -5},
        "MetricsDelta": {"LCR": 2, "NSFR": 2},
        "TradeList": ["Extend maturity on $1bn in wholesale funding", "Enhance retail deposit offerings"],
        "Assumptions": "Depositor behavior may shift as rates rise."
    },
    {
        "Scenario": "Widening Credit Spreads",
        "Description": "Credit spreads widen by 30 bps in IG and 60 bps in HY due to heightened risk aversion.",
        "Probability": 0.25,
        "Rationale": "Economic uncertainty and market volatility may lead to wider spreads.",
        "ImpactChannels": ["Credit OAS: IG +30 bps, HY +60 bps"],
        "Shocks": {"ig_oas": 30, "hy_oas": 60},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase liquidity buffer by $1bn through repo", "Monitor corporate exposure closely"],
        "Assumptions": "Increased risk aversion persists in the market."
    },
    {
        "Scenario": "Regulatory Changes",
        "Description": "Potential implementation of Basel Endgame liquidity requirements impacting funding costs.",
        "Probability": 0.25,
        "Rationale": "Ongoing discussions around Basel reforms could lead to stricter liquidity requirements for G-SIBs.",
        "ImpactChannels": ["Regulatory changes impact capital ratios"],
        "Shocks": {"move_index": 0},
        "MetricsDelta": {"LCR": -5, "NSFR": -4},
        "TradeList": ["Prepare for $1bn increase in TLAC requirements", "Review capital structure"],
        "Assumptions": "Regulatory environment becomes more stringent."
    },
    {
        "Scenario": "Geopolitical Tensions",
        "Description": "Escalation in geopolitical tensions leads to increased demand for USTs, impacting liquidity metrics positively.",
        "Probability": 0.15,
        "Rationale": "Increased demand for safe-haven assets could provide a temporary liquidity boost, but also risks volatility.",
        "ImpactChannels": ["Rates decrease, credit spreads react"],
        "Shocks": {"move": -30},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Add $1bn in USTs through market operations", "Evaluate credit risk exposure"],
        "Assumptions": "Geopolitical risks escalate, leading to market flight to safety."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Moderate Inflation with Consumer Caution",
        "Description": "Inflation remains moderate but leads to cautious consumer spending and borrowing.",
        "Probability": 0.25,
        "Rationale": "Consumer sentiment may shift in response to rising prices, impacting loan demand.",
        "ImpactChannels": ["Consumer spending slows", "Loan demand decreases"],
        "Shocks": {"move": 25},
        "MetricsDelta": {"LCR": -2, "NSFR": -1},
        "TradeList": ["Increase allocation to Agency MBS by $1bn", "Rebalance towards more stable loan products"],
        "Assumptions": "Economic growth is steady but faces inflationary pressures."
    },
    {
        "Scenario": "Funding Pressure from Deposit Runoff",
        "Description": "Increased interest rates lead to significant runoff in deposits, affecting funding stability.",
        "Probability": 0.30,
        "Rationale": "As rates rise, consumers may seek better returns, impacting Bank of America's funding stack.",
        "ImpactChannels": ["Deposit outflows increase", "Funding costs rise"],
        "Shocks": {"depo_beta": -5},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Extend maturity on $1bn in wholesale funding", "Enhance retail deposit offerings"],
        "Assumptions": "Depositor behavior shifts due to competitive rate offerings."
    },
    {
        "Scenario": "Widening Credit Spreads",
        "Description": "Credit spreads widen by 25 bps in IG and 50 bps in HY due to heightened risk aversion.",
        "Probability": 0.25,
        "Rationale": "Economic uncertainty may lead to wider spreads, impacting portfolio valuations.",
        "ImpactChannels": ["Credit OAS: IG +25 bps, HY +50 bps"],
        "Shocks": {"ig_oas": 25, "hy_oas": 50},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Increase liquidity buffer by $1bn through repo", "Monitor corporate exposure closely"],
        "Assumptions": "Increased risk aversion persists in the market."
    },
    {
        "Scenario": "Stricter Regulatory Environment",
        "Description": "Potential implementation of stricter liquidity requirements impacts funding costs.",
        "Probability": 0.15,
        "Rationale": "Ongoing discussions around Basel reforms could lead to tighter liquidity requirements.",
        "ImpactChannels": ["Increased capital requirements", "Higher compliance costs"],
        "Shocks": {"move_index": 0},
        "MetricsDelta": {"LCR": -5, "NSFR": -4},
        "TradeList": ["Prepare for $1bn increase in TLAC requirements", "Review capital structure"],
        "Assumptions": "Regulatory environment becomes more stringent."
    },
    {
        "Scenario": "Geopolitical Risks Heightened",
        "Description": "Escalation in geopolitical tensions leads to increased market volatility and demand for safe-haven assets.",
        "Probability": 0.05,
        "Rationale": "Increased geopolitical risks could lead to liquidity challenges despite temporary asset boosts.",
        "ImpactChannels": ["Rates react negatively, credit spreads widen"],
        "Shocks": {"move": -30},
        "MetricsDelta": {"LCR": +2, "NSFR": +1},
        "TradeList": ["Add $1bn in USTs through market operations", "Evaluate credit risk exposure"],
        "Assumptions": "Geopolitical tensions escalate, creating market instability."
    }
]
```

