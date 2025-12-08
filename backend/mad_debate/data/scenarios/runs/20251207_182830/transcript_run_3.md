# Debate Transcript — Run 3

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening with Increased Credit Spreads",
        "Description": "Long-term rates rise faster than short-term rates, leading to a bear steepening of the yield curve and widening credit spreads.",
        "Probability": 0.20,
        "Rationale": "Inflation pressures and cautious risk sentiment prompt investors to reassess credit risks.",
        "ImpactChannels": ["Rates: +50 bps", "Credit OAS: +30 bps", "MBS basis: +20 bps"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": 30, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3, "OCI": -100},
        "TradeList": ["Add $2bn USTs via repo", "Reduce $1bn MBS holdings"],
        "Assumptions": "Inflation remains a concern; investor sentiment shifts toward safety."
    },
    {
        "Scenario": "Regulatory Tightening and TLAC Changes",
        "Description": "New regulatory requirements increase capital and liquidity requirements for G-SIBs, impacting lending capacity.",
        "Probability": 0.15,
        "Rationale": "Ongoing regulatory discussions suggest potential for increased capital surcharges impacting large banks.",
        "ImpactChannels": ["Reg changes: Increased TLAC requirements"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2, "OCI": 0},
        "TradeList": ["Increase $1bn liquidity reserves", "Reduce risk-weighted assets by $1.5bn"],
        "Assumptions": "Regulatory environment becomes more stringent; BoA adapts proactively."
    },
    {
        "Scenario": "Stable Macroeconomic Recovery",
        "Description": "Robust consumer spending and SME growth support stable deposit flows and lending activity.",
        "Probability": 0.20,
        "Rationale": "Economic resilience mitigates risk-off sentiment and drives banking activities.",
        "ImpactChannels": ["Deposits: Stable", "Lending: Growth"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -10, "hy_oas": -15}},
        "MetricsDelta": {"LCR": 3, "NSFR": 2, "OCI": 0},
        "TradeList": ["Increase lending by $2bn from retail deposits", "Add $500mm in short-term USTs through repo"],
        "Assumptions": "Continued economic activity; consumer confidence remains high."
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS market experiences a widening basis due to market volatility and a slowdown in prepayments.",
        "Probability": 0.10,
        "Rationale": "Market caution leads to increased risk premiums in MBS valuations.",
        "ImpactChannels": ["MBS basis: +25 bps"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1, "OCI": -50},
        "TradeList": ["Reduce MBS holdings by $500mm", "Increase UST holdings by $500mm"],
        "Assumptions": "Investor caution remains high; prepayment speeds decline."
    },
    {
        "Scenario": "Yield Curve Dynamics Favorable",
        "Description": "Interest rate adjustments lead to favorable yield curve dynamics as inflation expectations stabilize.",
        "Probability": 0.15,
        "Rationale": "Market adjustments positively impact Bank of America's funding and NII.",
        "ImpactChannels": ["Rates: +50 bps", "MBS basis: Stable"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 50},
        "TradeList": ["Increase long-term UST holdings by $1bn funded by deposits", "Rotate $500mm into munis for yield enhancement"],
        "Assumptions": "Positive market reaction to stable economic indicators."
    },
    {
        "Scenario": "Proactive Basis and Convexity Management",
        "Description": "Bank of America employs strategic hedging to manage basis and convexity risks effectively.",
        "Probability": 0.10,
        "Rationale": "Risk management can stabilize MBS valuations and protect NII.",
        "ImpactChannels": ["Basis: Stabilization", "Convexity: Mitigated"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 1, "NSFR": 1, "OCI": 10},
        "TradeList": ["Implement hedging strategies on MBS holdings worth $500mm", "Increase short positions in convexity-sensitive assets by $300mm"],
        "Assumptions": "Effective execution of risk management strategies."
    },
    {
        "Scenario": "Geopolitical Tensions and Commodities Spike",
        "Description": "Increased geopolitical tensions lead to rising commodity prices and inflation expectations, prompting Fed rate hikes.",
        "Probability": 0.10,
        "Rationale": "Ongoing geopolitical risks could lead to market instability and inflation pressures.",
        "ImpactChannels": ["Rates: +75 bps", "Curve: bear steepening"],
        "Shocks": {"move": 75, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2, "OCI": -75},
        "TradeList": ["Add $1bn to short-term USTs", "Increase commodity hedges by $500mm"],
        "Assumptions": "Geopolitical landscape remains volatile; inflation expectations rise."
    }
]
```

## Round 1

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening with Increased Credit Spreads",
        "Description": "Long-term rates rise faster than short-term rates, leading to a bear steepening of the yield curve and widening credit spreads.",
        "Probability": 0.30,
        "Rationale": "Inflation pressures are increasing and risk sentiment is cautious, prompting investors to reassess credit risks.",
        "ImpactChannels": ["Rates: +50 bps", "Credit OAS: +30 bps", "MBS basis: +20 bps"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": 30, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3, "OCI": -100},
        "TradeList": ["Add $2bn USTs via repo", "Reduce $1bn MBS holdings"],
        "Assumptions": "Inflation remains a concern; investor sentiment shifts toward safety."
    },
    {
        "Scenario": "Regulatory Tightening and TLAC Changes",
        "Description": "New regulatory requirements increase capital and liquidity requirements for G-SIBs, impacting lending capacity.",
        "Probability": 0.20,
        "Rationale": "Ongoing regulatory discussions suggest potential for increased capital surcharges impacting large banks.",
        "ImpactChannels": ["Reg changes: Increased TLAC requirements"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2, "OCI": 0},
        "TradeList": ["Increase $1bn liquidity reserves", "Reduce risk-weighted assets by $1.5bn"],
        "Assumptions": "Regulatory environment becomes more stringent; BoA adapts proactively."
    },
    {
        "Scenario": "Stable Deposits but Wealth Runoff",
        "Description": "Retail deposits remain stable while wealth management clients withdraw funds, resulting in a net outflow.",
        "Probability": 0.25,
        "Rationale": "High-net-worth individuals are seeking better returns, leading to outflows from wealth management.",
        "ImpactChannels": ["Deposits: -5%", "Rates: 0"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -2, "NSFR": -4, "OCI": 0},
        "TradeList": ["Increase retail deposit incentives by $500mm", "Add $1bn to secured funding"],
        "Assumptions": "Wealth management clients are more sensitive to market fluctuations."
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "MBS market experiences a widening basis due to market volatility and a slowdown in prepayments.",
        "Probability": 0.15,
        "Rationale": "Market caution leads to increased risk premiums in MBS valuations.",
        "ImpactChannels": ["MBS basis: +25 bps"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -2, "NSFR": -1, "OCI": -50},
        "TradeList": ["Reduce MBS holdings by $500mm", "Increase UST holdings by $500mm"],
        "Assumptions": "Investor caution remains high; prepayment speeds decline."
    },
    {
        "Scenario": "Geopolitical Tensions and Commodities Spike",
        "Description": "Increased geopolitical tensions lead to rising commodity prices and inflation expectations, prompting Fed rate hikes.",
        "Probability": 0.10,
        "Rationale": "Ongoing geopolitical risks could lead to market instability and inflation pressures.",
        "ImpactChannels": ["Rates: +75 bps", "Curve: bear steepening"],
        "Shocks": {"move": 75, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2, "OCI": -75},
        "TradeList": ["Add $1bn to short-term USTs", "Increase commodity hedges by $500mm"],
        "Assumptions": "Geopolitical landscape remains volatile; inflation expectations rise."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Resilient Macro Environment",
        "Description": "Consumer and SME spending remains robust, supporting stable deposit flows and lending activity.",
        "Probability": 0.35,
        "Rationale": "The current economic environment shows resilience, which may mitigate risk-off sentiment.",
        "ImpactChannels": ["Deposits: Stable", "Lending: Growth"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -10, "hy_oas": -15}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 0},
        "TradeList": ["Increase lending by $2bn", "Add $500mm in short-term USTs"],
        "Assumptions": "Economic activity remains steady; consumer confidence stays high."
    },
    {
        "Scenario": "Stable Funding Stack with Improved Liquidity",
        "Description": "Bank of America leverages its strong liquidity position to navigate potential market volatility effectively.",
        "Probability": 0.30,
        "Rationale": "A diversified funding strategy provides resilience against market fluctuations.",
        "ImpactChannels": ["Funding Costs: Stable", "Liquidity Coverage: Improved"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 3, "NSFR": 2, "OCI": 0},
        "TradeList": ["Term out $1bn of wholesale funding", "Add $1bn in Agency MBS"],
        "Assumptions": "Liquidity management strategies remain effective; market conditions stabilize."
    },
    {
        "Scenario": "Bull Steepening/Flattening Yield Curve",
        "Description": "Interest rate adjustments lead to a bull steepening or flattening of the yield curve as inflation expectations stabilize.",
        "Probability": 0.20,
        "Rationale": "Market adjustments could lead to favorable yield curve dynamics for Bank of America.",
        "ImpactChannels": ["Rates: +50 bps", "MBS basis: Stable"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": 1, "NSFR": 0, "OCI": 50},
        "TradeList": ["Increase long-term UST holdings by $1bn", "Rotate $500mm into munis"],
        "Assumptions": "Market reacts positively to stable economic indicators; inflation expectations align."
    },
    {
        "Scenario": "Tighter Credit Spreads and Stable Betas",
        "Description": "As confidence returns, credit spreads tighten, and deposit betas stabilize, benefiting Bank of America’s funding profile.",
        "Probability": 0.10,
        "Rationale": "Improved investor sentiment can lead to a more favorable credit environment.",
        "ImpactChannels": ["Credit Spreads: -20 bps"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -25}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 25},
        "TradeList": ["Add $1bn to investment-grade corporate bonds", "Reduce reliance on higher-cost funding sources"],
        "Assumptions": "Market sentiment improves; lending conditions ease."
    },
    {
        "Scenario": "Effective Management of Basis and Convexity Risks",
        "Description": "Bank of America employs strategic hedging to manage basis and convexity risks in the MBS market.",
        "Probability": 0.05,
        "Rationale": "Proactive risk management can mitigate potential losses from MBS volatility.",
        "ImpactChannels": ["Basis: Stabilization", "Convexity: Mitigated"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 1, "NSFR": 1, "OCI": 10},
        "TradeList": ["Implement hedging strategies on MBS holdings", "Increase short positions in convexity-sensitive assets"],
        "Assumptions": "Risk management strategies are effectively executed; market fluctuations are contained."
    }
]
```

## Round 2

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Resilient Macro Environment",
        "Description": "Consumer and SME spending remains robust, supporting stable deposit flows and lending activity.",
        "Probability": 0.30,
        "Rationale": "The current economic environment shows resilience, which may mitigate risk-off sentiment and support banking activities.",
        "ImpactChannels": ["Deposits: Stable", "Lending: Growth"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -10, "hy_oas": -15}},
        "MetricsDelta": {"LCR": 3, "NSFR": 2, "OCI": 0},
        "TradeList": ["Increase lending by $2bn", "Add $500mm in short-term USTs"],
        "Assumptions": "Economic activity remains steady; consumer confidence stays high."
    },
    {
        "Scenario": "Stable Funding Stack with Improved Liquidity",
        "Description": "Bank of America leverages its strong liquidity position to navigate potential market volatility effectively.",
        "Probability": 0.25,
        "Rationale": "A diversified funding strategy provides resilience against market fluctuations and enhances liquidity coverage.",
        "ImpactChannels": ["Funding Costs: Stable", "Liquidity Coverage: Improved"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 4, "NSFR": 3, "OCI": 0},
        "TradeList": ["Term out $1bn of wholesale funding", "Add $1bn in Agency MBS"],
        "Assumptions": "Liquidity management strategies remain effective; market conditions stabilize."
    },
    {
        "Scenario": "Bull Steepening/Flattening Yield Curve",
        "Description": "Interest rate adjustments lead to a bull steepening or flattening of the yield curve as inflation expectations stabilize.",
        "Probability": 0.20,
        "Rationale": "Market adjustments could lead to favorable yield curve dynamics for Bank of America, impacting net interest income positively.",
        "ImpactChannels": ["Rates: +50 bps", "MBS basis: Stable"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 50},
        "TradeList": ["Increase long-term UST holdings by $1bn", "Rotate $500mm into munis"],
        "Assumptions": "Market reacts positively to stable economic indicators; inflation expectations align."
    },
    {
        "Scenario": "Tighter Credit Spreads and Stable Betas",
        "Description": "As confidence returns, credit spreads tighten, and deposit betas stabilize, benefiting Bank of America’s funding profile.",
        "Probability": 0.15,
        "Rationale": "Improved investor sentiment can lead to a more favorable credit environment, enhancing liquidity metrics.",
        "ImpactChannels": ["Credit Spreads: -20 bps"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -25}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 25},
        "TradeList": ["Add $1bn to investment-grade corporate bonds", "Reduce reliance on higher-cost funding sources"],
        "Assumptions": "Market sentiment improves; lending conditions ease."
    },
    {
        "Scenario": "Effective Management of Basis and Convexity Risks",
        "Description": "Bank of America employs strategic hedging to manage basis and convexity risks in the MBS market.",
        "Probability": 0.10,
        "Rationale": "Proactive risk management can mitigate potential losses from MBS volatility and stabilize liquidity metrics.",
        "ImpactChannels": ["Basis: Stabilization", "Convexity: Mitigated"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 1, "NSFR": 1, "OCI": 10},
        "TradeList": ["Implement hedging strategies on MBS holdings", "Increase short positions in convexity-sensitive assets"],
        "Assumptions": "Risk management strategies are effectively executed; market fluctuations are contained."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Stable Macroeconomic Recovery",
        "Description": "Robust consumer spending and SME growth support stable deposit flows and lending activity.",
        "Probability": 0.30,
        "Rationale": "Economic resilience mitigates risk-off sentiment and drives banking activities.",
        "ImpactChannels": ["Deposits: Stable", "Lending: Growth"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -10, "hy_oas": -15}},
        "MetricsDelta": {"LCR": 3, "NSFR": 2, "OCI": 0},
        "TradeList": ["Increase lending by $2bn", "Add $500mm in short-term USTs"],
        "Assumptions": "Continued economic activity; consumer confidence remains high."
    },
    {
        "Scenario": "Robust Funding Stack",
        "Description": "Bank of America leverages a diversified funding strategy to navigate market volatility effectively.",
        "Probability": 0.25,
        "Rationale": "Strong liquidity positions enhance resilience against funding pressures.",
        "ImpactChannels": ["Funding Costs: Stable", "Liquidity Coverage: Improved"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 4, "NSFR": 3, "OCI": 0},
        "TradeList": ["Term out $1bn of wholesale funding", "Add $1bn in Agency MBS"],
        "Assumptions": "Effective liquidity management; stable market conditions."
    },
    {
        "Scenario": "Yield Curve Dynamics Favorable",
        "Description": "Interest rate adjustments lead to favorable yield curve dynamics as inflation expectations stabilize.",
        "Probability": 0.20,
        "Rationale": "Market adjustments positively impact Bank of America's funding and NII.",
        "ImpactChannels": ["Rates: +50 bps", "MBS basis: Stable"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 50},
        "TradeList": ["Increase long-term UST holdings by $1bn", "Rotate $500mm into munis"],
        "Assumptions": "Positive market reaction to stable economic indicators."
    },
    {
        "Scenario": "Tightening Credit Spreads",
        "Description": "Investor sentiment improves, leading to tighter credit spreads and stable deposit betas.",
        "Probability": 0.15,
        "Rationale": "Favorable credit environment enhances liquidity metrics for Bank of America.",
        "ImpactChannels": ["Credit Spreads: -20 bps"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -25}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 25},
        "TradeList": ["Add $1bn to investment-grade corporate bonds", "Reduce reliance on higher-cost funding"],
        "Assumptions": "Improved market sentiment; easing lending conditions."
    },
    {
        "Scenario": "Proactive Basis and Convexity Management",
        "Description": "Bank of America employs strategic hedging to manage basis and convexity risks effectively.",
        "Probability": 0.10,
        "Rationale": "Risk management can stabilize MBS valuations and protect NII.",
        "ImpactChannels": ["Basis: Stabilization", "Convexity: Mitigated"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 1, "NSFR": 1, "OCI": 10},
        "TradeList": ["Implement hedging strategies on MBS holdings", "Increase short positions in convexity-sensitive assets"],
        "Assumptions": "Effective execution of risk management strategies."
    }
]
```

## Round 3

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Stable Macroeconomic Recovery",
        "Description": "Robust consumer spending and SME growth support stable deposit flows and lending activity.",
        "Probability": 0.30,
        "Rationale": "Economic resilience mitigates risk-off sentiment and drives banking activities.",
        "ImpactChannels": ["Deposits: Stable", "Lending: Growth"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -10, "hy_oas": -15}},
        "MetricsDelta": {"LCR": 3, "NSFR": 2, "OCI": 0},
        "TradeList": ["Increase lending by $2bn from retail deposits", "Add $500mm in short-term USTs through repo"],
        "Assumptions": "Continued economic activity; consumer confidence remains high."
    },
    {
        "Scenario": "Robust Funding Stack",
        "Description": "Bank of America leverages a diversified funding strategy to navigate market volatility effectively.",
        "Probability": 0.25,
        "Rationale": "Strong liquidity positions enhance resilience against funding pressures.",
        "ImpactChannels": ["Funding Costs: Stable", "Liquidity Coverage: Improved"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 4, "NSFR": 3, "OCI": 0},
        "TradeList": ["Term out $1bn of wholesale funding to lower costs", "Add $1bn in Agency MBS from HQLA"],
        "Assumptions": "Effective liquidity management; stable market conditions."
    },
    {
        "Scenario": "Yield Curve Dynamics Favorable",
        "Description": "Interest rate adjustments lead to favorable yield curve dynamics as inflation expectations stabilize.",
        "Probability": 0.20,
        "Rationale": "Market adjustments positively impact Bank of America's funding and NII.",
        "ImpactChannels": ["Rates: +50 bps", "MBS basis: Stable"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 50},
        "TradeList": ["Increase long-term UST holdings by $1bn funded by deposits", "Rotate $500mm into munis for yield enhancement"],
        "Assumptions": "Positive market reaction to stable economic indicators."
    },
    {
        "Scenario": "Tightening Credit Spreads",
        "Description": "Investor sentiment improves, leading to tighter credit spreads and stable deposit betas.",
        "Probability": 0.15,
        "Rationale": "Favorable credit environment enhances liquidity metrics for Bank of America.",
        "ImpactChannels": ["Credit Spreads: -20 bps"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -25}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 25},
        "TradeList": ["Add $1bn to investment-grade corporate bonds from the trading book", "Reduce reliance on higher-cost funding sources by $500mm"],
        "Assumptions": "Improved market sentiment; easing lending conditions."
    },
    {
        "Scenario": "Proactive Basis and Convexity Management",
        "Description": "Bank of America employs strategic hedging to manage basis and convexity risks effectively.",
        "Probability": 0.10,
        "Rationale": "Risk management can stabilize MBS valuations and protect NII.",
        "ImpactChannels": ["Basis: Stabilization", "Convexity: Mitigated"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 1, "NSFR": 1, "OCI": 10},
        "TradeList": ["Implement hedging strategies on MBS holdings worth $500mm", "Increase short positions in convexity-sensitive assets by $300mm"],
        "Assumptions": "Effective execution of risk management strategies."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Stable Macroeconomic Recovery",
        "Description": "Robust consumer spending and SME growth support stable deposit flows and lending activity.",
        "Probability": 0.30,
        "Rationale": "Economic resilience mitigates risk-off sentiment and drives banking activities.",
        "ImpactChannels": ["Deposits: Stable", "Lending: Growth"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -10, "hy_oas": -15}},
        "MetricsDelta": {"LCR": 3, "NSFR": 2, "OCI": 0},
        "TradeList": ["Increase lending by $2bn from retail deposits", "Add $500mm in short-term USTs through repo"],
        "Assumptions": "Continued economic activity; consumer confidence remains high."
    },
    {
        "Scenario": "Robust Funding Stack",
        "Description": "Bank of America leverages a diversified funding strategy to navigate market volatility effectively.",
        "Probability": 0.25,
        "Rationale": "Strong liquidity positions enhance resilience against funding pressures.",
        "ImpactChannels": ["Funding Costs: Stable", "Liquidity Coverage: Improved"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 4, "NSFR": 3, "OCI": 0},
        "TradeList": ["Term out $1bn of wholesale funding to lower costs", "Add $1bn in Agency MBS from HQLA"],
        "Assumptions": "Effective liquidity management; stable market conditions."
    },
    {
        "Scenario": "Yield Curve Dynamics Favorable",
        "Description": "Interest rate adjustments lead to favorable yield curve dynamics as inflation expectations stabilize.",
        "Probability": 0.20,
        "Rationale": "Market adjustments positively impact Bank of America's funding and NII.",
        "ImpactChannels": ["Rates: +50 bps", "MBS basis: Stable"],
        "Shocks": {"move": 50, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 50},
        "TradeList": ["Increase long-term UST holdings by $1bn funded by deposits", "Rotate $500mm into munis for yield enhancement"],
        "Assumptions": "Positive market reaction to stable economic indicators."
    },
    {
        "Scenario": "Tightening Credit Spreads",
        "Description": "Investor sentiment improves, leading to tighter credit spreads and stable deposit betas.",
        "Probability": 0.15,
        "Rationale": "Favorable credit environment enhances liquidity metrics for Bank of America.",
        "ImpactChannels": ["Credit Spreads: -20 bps"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": -20, "hy_oas": -25}},
        "MetricsDelta": {"LCR": 2, "NSFR": 1, "OCI": 25},
        "TradeList": ["Add $1bn to investment-grade corporate bonds from the trading book", "Reduce reliance on higher-cost funding sources by $500mm"],
        "Assumptions": "Improved market sentiment; easing lending conditions."
    },
    {
        "Scenario": "Proactive Basis and Convexity Management",
        "Description": "Bank of America employs strategic hedging to manage basis and convexity risks effectively.",
        "Probability": 0.10,
        "Rationale": "Risk management can stabilize MBS valuations and protect NII.",
        "ImpactChannels": ["Basis: Stabilization", "Convexity: Mitigated"],
        "Shocks": {"move": 0, "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": 1, "NSFR": 1, "OCI": 10},
        "TradeList": ["Implement hedging strategies on MBS holdings worth $500mm", "Increase short positions in convexity-sensitive assets by $300mm"],
        "Assumptions": "Effective execution of risk management strategies."
    }
]
```

