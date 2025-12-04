# Debate Transcript — Run 1

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening with Rising Credit Spreads",
        "Description": "A bear steepening of the yield curve with 50 bps increase in 10-year UST yields, leading to wider credit spreads (IG OAS +15 bps, HY OAS +45 bps).",
        "Probability": 0.18,
        "Rationale": "Increased inflation expectations and risk aversion lead to long-term rates rising faster than short-term rates, impacting the valuation of Level 2 assets.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move": 50, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -2, "NSFR": -3, "OCI": -5},
        "TradeList": ["Add $1bn USTs via repo", "Reduce $500mn corporate bonds"],
        "Assumptions": "Inflation remains a concern; credit quality continues to deteriorate."
    },
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Macroeconomic indicators show controlled inflation and gradual easing, supporting consumer and SME resilience, which leads to increased loan demand and stable net interest income.",
        "Probability": 0.18,
        "Rationale": "Stable inflation supports a favorable economic environment, boosting consumer confidence and spending, which in turn drives loan demand.",
        "ImpactChannels": ["Macro", "Consumer"],
        "Shocks": {"inflation": 0.5},
        "MetricsDelta": {"NII": 3, "LCR": 2},
        "TradeList": ["Increase holdings in Agency MBS by $500mn", "Expand consumer loan offerings by $1bn in personal loans and credit products"],
        "Assumptions": "Inflation remains controlled; consumer spending stays strong."
    },
    {
        "Scenario": "Diversified Funding Flows and Deposit Stability",
        "Description": "Stable deposit growth and diversified funding flows reinforce BoA's liquidity profile, allowing for more flexible asset management.",
        "Probability": 0.16,
        "Rationale": "A diversified funding stack reduces reliance on any single source and enhances liquidity, enabling BoA to respond effectively to market changes.",
        "ImpactChannels": ["Funding"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": 3, "NSFR": 2},
        "TradeList": ["Rebalance deposit pricing to attract more retail deposits", "Increase term funding by $1bn through various channels"],
        "Assumptions": "Deposit competition remains stable; customer loyalty strengthens."
    },
    {
        "Scenario": "Increased Treasury Issuance with MBS Basis Widening",
        "Description": "Surge in Treasury issuance leads to a wider MBS basis of +35 bps.",
        "Probability": 0.13,
        "Rationale": "Government fiscal policies adjust, increasing Treasury supply and impacting MBS valuations.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 35},
        "MetricsDelta": {"OCI": -4},
        "TradeList": ["Increase MBS purchases by $1bn", "Sell $300mn in less liquid MBS"],
        "Assumptions": "Fiscal policy remains expansionary."
    },
    {
        "Scenario": "Potential Regulatory Relief for HQLA",
        "Description": "Expectations of regulatory relief could benefit BoA's Level 1 and Level 2 asset mix, improving overall capital ratios and liquidity metrics.",
        "Probability": 0.12,
        "Rationale": "Regulatory changes may favor banks with strong liquidity profiles, allowing for a more favorable capital structure.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"tlac_relief": 25},
        "MetricsDelta": {"LCR": 4, "NSFR": 3},
        "TradeList": ["Increase high-quality asset purchases by $500mn", "Reduce reliance on short-term funding"],
        "Assumptions": "Regulatory environment improves; capital requirements ease."
    },
    {
        "Scenario": "Geopolitical Tensions Affecting Commodity Prices and Credit Spreads",
        "Description": "Geopolitical tensions lead to inflation increase, affecting IG and HY spreads (+20 bps and +30 bps respectively).",
        "Probability": 0.08,
        "Rationale": "Heightened geopolitical risks trigger a flight-to-quality and impact overall credit markets.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"ig_oas": 20, "hy_oas": 30},
        "MetricsDelta": {"LCR": -2, "NSFR": -3, "OCI": -6},
        "TradeList": ["Adjust credit exposure to IG bonds", "Reduce holdings in affected sectors"],
        "Assumptions": "Commodity prices remain volatile; global tensions escalate."
    },
    {
        "Scenario": "Favorable Basis Dynamics and Convexity Management",
        "Description": "Effective management of convexity risk through strategic asset allocation in a favorable basis environment allows BoA to maintain strong HQLA levels.",
        "Probability": 0.08,
        "Rationale": "Managing convexity risk through asset rotation can help mitigate the impact of widening spreads on the bank's asset valuations.",
        "ImpactChannels": ["Basis", "Convexity"],
        "Shocks": {"basis_widening": 15},
        "MetricsDelta": {"OCI": -2},
        "TradeList": ["Rotate into longer-duration munis by $400mn", "Sell $300mn in corporates to maintain liquidity"],
        "Assumptions": "Interest rate environment remains stable; spreads widen gradually."
    },
    {
        "Scenario": "Resilient Consumer Behavior Supporting NII Growth",
        "Description": "Strong consumer behavior, driven by economic stability, supports net interest income growth amidst rising rates.",
        "Probability": 0.05,
        "Rationale": "Resilient consumers can sustain loan demand, positively impacting NII and contributing to overall profitability.",
        "ImpactChannels": ["Consumer", "NII"],
        "Shocks": {"loan_demand": 5},
        "MetricsDelta": {"NII": 5},
        "TradeList": ["Increase consumer loan originations by $1bn in auto and personal loans", "Expand credit card offerings to boost market share"],
        "Assumptions": "Consumer confidence remains high; economic conditions support spending."
    }
]
```

## Round 1

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening with Rising Credit Spreads",
        "Description": "A bear steepening of the yield curve with 50 bps increase in 10-year UST yields, leading to wider credit spreads (IG OAS +15 bps, HY OAS +45 bps).",
        "Probability": 0.25,
        "Rationale": "Increased inflation expectations and risk aversion lead to long-term rates rising faster than short-term rates, impacting the valuation of Level 2 assets.",
        "ImpactChannels": ["Rates", "Credit"],
        "Shocks": {"move": 50, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -2, "NSFR": -3, "OCI": -5},
        "TradeList": ["Add $1bn USTs via repo", "Reduce $500mn corporate bonds"],
        "Assumptions": "Inflation remains a concern; credit quality continues to deteriorate."
    },
    {
        "Scenario": "Regulatory Changes and Increased TLAC Requirements",
        "Description": "Potential increase in GSIB surcharge by 25 bps and liquidity add-ons affecting the NSFR.",
        "Probability": 0.15,
        "Rationale": "Ongoing regulatory discussions could lead to increased capital requirements for G-SIBs.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"tlac_increase": 25},
        "MetricsDelta": {"LCR": -3, "NSFR": -5},
        "TradeList": ["Rebalance capital allocation to offset TLAC increase"],
        "Assumptions": "Regulatory environment tightens; capital markets remain stable."
    },
    {
        "Scenario": "Stable Deposit Growth with Rising Retail Beta",
        "Description": "Retail beta increases by 10%, while wealth segment experiences 5% runoff.",
        "Probability": 0.30,
        "Rationale": "Higher interest rates lead to consumers seeking better yields, impacting overall liquidity and funding costs.",
        "ImpactChannels": ["Deposits"],
        "Shocks": {"retail_beta": 10, "wealth_runoff": 5},
        "MetricsDelta": {"LCR": -1, "NII": -2},
        "TradeList": ["Add $500mn in retail deposits", "Adjust pricing on deposits"],
        "Assumptions": "Consumer sentiment shifts due to economic conditions."
    },
    {
        "Scenario": "Increased Treasury Issuance with MBS Basis Widening",
        "Description": "Surge in Treasury issuance leads to a wider MBS basis of +35 bps.",
        "Probability": 0.20,
        "Rationale": "Government fiscal policies adjust, increasing Treasury supply and impacting MBS valuations.",
        "ImpactChannels": ["MBS"],
        "Shocks": {"mbs_basis": 35},
        "MetricsDelta": {"OCI": -4},
        "TradeList": ["Increase MBS purchases by $1bn", "Sell $300mn in less liquid MBS"],
        "Assumptions": "Fiscal policy remains expansionary."
    },
    {
        "Scenario": "Geopolitical Tensions Affecting Commodity Prices and Credit Spreads",
        "Description": "Geopolitical tensions lead to inflation increase, affecting IG and HY spreads (+20 bps and +30 bps respectively).",
        "Probability": 0.10,
        "Rationale": "Heightened geopolitical risks trigger a flight-to-quality and impact overall credit markets.",
        "ImpactChannels": ["Credit"],
        "Shocks": {"ig_oas": 20, "hy_oas": 30},
        "MetricsDelta": {"LCR": -2, "NSFR": -3, "OCI": -6},
        "TradeList": ["Adjust credit exposure to IG bonds", "Reduce holdings in affected sectors"],
        "Assumptions": "Commodity prices remain volatile; global tensions escalate."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Macroeconomic indicators show controlled inflation and gradual easing, supporting consumer and SME resilience.",
        "Probability": 0.30,
        "Rationale": "Stable inflation supports a favorable economic environment, boosting consumer confidence and spending.",
        "ImpactChannels": ["Macro", "Consumer"],
        "Shocks": {"inflation": 0.5},
        "MetricsDelta": {"NII": +3, "LCR": +2},
        "TradeList": ["Increase holdings in consumer-focused loans", "Add $500mn in Agency MBS"],
        "Assumptions": "Inflation remains controlled; consumer spending stays strong."
    },
    {
        "Scenario": "Diversified Funding Flows and Deposit Stability",
        "Description": "Stable deposit growth and diversified funding flows reinforce BoA's liquidity profile.",
        "Probability": 0.25,
        "Rationale": "A diversified funding stack reduces reliance on any single source and enhances liquidity.",
        "ImpactChannels": ["Funding"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Rebalance deposit pricing to attract more retail deposits", "Increase term funding by $1bn"],
        "Assumptions": "Deposit competition remains stable; customer loyalty strengthens."
    },
    {
        "Scenario": "Favorable Basis Dynamics and Convexity Management",
        "Description": "Managing convexity risk through strategic asset allocation in a favorable basis environment.",
        "Probability": 0.20,
        "Rationale": "Effective management of asset allocation can mitigate the impact of widening spreads.",
        "ImpactChannels": ["Basis", "Convexity"],
        "Shocks": {"basis_widening": 15},
        "MetricsDelta": {"OCI": -2},
        "TradeList": ["Rotate into longer-duration munis", "Sell $300mn in corporates"],
        "Assumptions": "Interest rate environment remains stable; spreads widen gradually."
    },
    {
        "Scenario": "Potential Regulatory Relief for HQLA",
        "Description": "Expectations of regulatory relief could benefit BoA's Level 1 and Level 2 asset mix.",
        "Probability": 0.15,
        "Rationale": "Regulatory changes may favor banks with strong liquidity profiles, improving capital requirements.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"tlac_relief": 25},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Increase high-quality asset purchases", "Reduce reliance on short-term funding"],
        "Assumptions": "Regulatory environment improves; capital requirements ease."
    },
    {
        "Scenario": "Resilient Consumer Behavior Supporting NII Growth",
        "Description": "Strong consumer behavior supports net interest income growth amidst rising rates.",
        "Probability": 0.10,
        "Rationale": "Resilient consumers can sustain loan demand, positively impacting NII.",
        "ImpactChannels": ["Consumer", "NII"],
        "Shocks": {"loan_demand": 5},
        "MetricsDelta": {"NII": +5},
        "TradeList": ["Increase consumer loan originations by $1bn", "Expand credit card offerings"],
        "Assumptions": "Consumer confidence remains high; economic conditions support spending."
    }
]
```

## Round 2

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Macroeconomic indicators show controlled inflation and gradual easing, supporting consumer and SME resilience.",
        "Probability": 0.30,
        "Rationale": "Stable inflation supports a favorable economic environment, boosting consumer confidence and spending.",
        "ImpactChannels": ["Macro", "Consumer"],
        "Shocks": {"inflation": 0.5},
        "MetricsDelta": {"NII": +3, "LCR": +2},
        "TradeList": ["Increase holdings in Agency MBS by $500mn", "Expand consumer loan offerings by $1bn"],
        "Assumptions": "Inflation remains controlled; consumer spending stays strong."
    },
    {
        "Scenario": "Diversified Funding Flows and Deposit Stability",
        "Description": "Stable deposit growth and diversified funding flows reinforce BoA's liquidity profile.",
        "Probability": 0.25,
        "Rationale": "A diversified funding stack reduces reliance on any single source and enhances liquidity.",
        "ImpactChannels": ["Funding"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Rebalance deposit pricing to attract more retail deposits", "Increase term funding by $1bn"],
        "Assumptions": "Deposit competition remains stable; customer loyalty strengthens."
    },
    {
        "Scenario": "Favorable Basis Dynamics and Convexity Management",
        "Description": "Managing convexity risk through strategic asset allocation in a favorable basis environment.",
        "Probability": 0.20,
        "Rationale": "Effective management of asset allocation can mitigate the impact of widening spreads.",
        "ImpactChannels": ["Basis", "Convexity"],
        "Shocks": {"basis_widening": 15},
        "MetricsDelta": {"OCI": -2},
        "TradeList": ["Rotate into longer-duration munis by $400mn", "Sell $300mn in corporates"],
        "Assumptions": "Interest rate environment remains stable; spreads widen gradually."
    },
    {
        "Scenario": "Potential Regulatory Relief for HQLA",
        "Description": "Expectations of regulatory relief could benefit BoA's Level 1 and Level 2 asset mix.",
        "Probability": 0.15,
        "Rationale": "Regulatory changes may favor banks with strong liquidity profiles, improving capital requirements.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"tlac_relief": 25},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Increase high-quality asset purchases by $500mn", "Reduce reliance on short-term funding"],
        "Assumptions": "Regulatory environment improves; capital requirements ease."
    },
    {
        "Scenario": "Resilient Consumer Behavior Supporting NII Growth",
        "Description": "Strong consumer behavior supports net interest income growth amidst rising rates.",
        "Probability": 0.10,
        "Rationale": "Resilient consumers can sustain loan demand, positively impacting NII.",
        "ImpactChannels": ["Consumer", "NII"],
        "Shocks": {"loan_demand": 5},
        "MetricsDelta": {"NII": +5},
        "TradeList": ["Increase consumer loan originations by $1bn", "Expand credit card offerings"],
        "Assumptions": "Consumer confidence remains high; economic conditions support spending."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Macroeconomic indicators show controlled inflation and gradual easing, supporting consumer and SME resilience.",
        "Probability": 0.30,
        "Rationale": "Stable inflation supports a favorable economic environment, boosting consumer confidence and spending.",
        "ImpactChannels": ["Macro", "Consumer"],
        "Shocks": {"inflation": 0.5},
        "MetricsDelta": {"NII": +3, "LCR": +2},
        "TradeList": ["Increase holdings in Agency MBS by $500mn", "Expand consumer loan offerings by $1bn"],
        "Assumptions": "Inflation remains controlled; consumer spending stays strong."
    },
    {
        "Scenario": "Diversified Funding Flows and Deposit Stability",
        "Description": "Stable deposit growth and diversified funding flows reinforce BoA's liquidity profile.",
        "Probability": 0.25,
        "Rationale": "A diversified funding stack reduces reliance on any single source and enhances liquidity.",
        "ImpactChannels": ["Funding"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Rebalance deposit pricing to attract more retail deposits", "Increase term funding by $1bn"],
        "Assumptions": "Deposit competition remains stable; customer loyalty strengthens."
    },
    {
        "Scenario": "Favorable Basis Dynamics and Convexity Management",
        "Description": "Managing convexity risk through strategic asset allocation in a favorable basis environment.",
        "Probability": 0.20,
        "Rationale": "Effective management of asset allocation can mitigate the impact of widening spreads.",
        "ImpactChannels": ["Basis", "Convexity"],
        "Shocks": {"basis_widening": 15},
        "MetricsDelta": {"OCI": -2},
        "TradeList": ["Rotate into longer-duration munis by $400mn", "Sell $300mn in corporates"],
        "Assumptions": "Interest rate environment remains stable; spreads widen gradually."
    },
    {
        "Scenario": "Potential Regulatory Relief for HQLA",
        "Description": "Expectations of regulatory relief could benefit BoA's Level 1 and Level 2 asset mix.",
        "Probability": 0.15,
        "Rationale": "Regulatory changes may favor banks with strong liquidity profiles, improving capital requirements.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"tlac_relief": 25},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Increase high-quality asset purchases by $500mn", "Reduce reliance on short-term funding"],
        "Assumptions": "Regulatory environment improves; capital requirements ease."
    },
    {
        "Scenario": "Resilient Consumer Behavior Supporting NII Growth",
        "Description": "Strong consumer behavior supports net interest income growth amidst rising rates.",
        "Probability": 0.10,
        "Rationale": "Resilient consumers can sustain loan demand, positively impacting NII.",
        "ImpactChannels": ["Consumer", "NII"],
        "Shocks": {"loan_demand": 5},
        "MetricsDelta": {"NII": +5},
        "TradeList": ["Increase consumer loan originations by $1bn", "Expand credit card offerings"],
        "Assumptions": "Consumer confidence remains high; economic conditions support spending."
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
        "Description": "Macroeconomic indicators show controlled inflation and gradual easing, supporting consumer and SME resilience, which leads to increased loan demand and stable net interest income.",
        "Probability": 0.30,
        "Rationale": "Stable inflation supports a favorable economic environment, boosting consumer confidence and spending, which in turn drives loan demand.",
        "ImpactChannels": ["Macro", "Consumer"],
        "Shocks": {"inflation": 0.5},
        "MetricsDelta": {"NII": +3, "LCR": +2},
        "TradeList": ["Increase holdings in Agency MBS by $500mn", "Expand consumer loan offerings by $1bn in personal loans and credit products"],
        "Assumptions": "Inflation remains controlled; consumer spending stays strong."
    },
    {
        "Scenario": "Diversified Funding Flows and Deposit Stability",
        "Description": "Stable deposit growth and diversified funding flows reinforce BoA's liquidity profile, allowing for more flexible asset management.",
        "Probability": 0.25,
        "Rationale": "A diversified funding stack reduces reliance on any single source and enhances liquidity, enabling BoA to respond effectively to market changes.",
        "ImpactChannels": ["Funding"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Rebalance deposit pricing to attract more retail deposits", "Increase term funding by $1bn through various channels"],
        "Assumptions": "Deposit competition remains stable; customer loyalty strengthens."
    },
    {
        "Scenario": "Favorable Basis Dynamics and Convexity Management",
        "Description": "Effective management of convexity risk through strategic asset allocation in a favorable basis environment allows BoA to maintain strong HQLA levels.",
        "Probability": 0.20,
        "Rationale": "Managing convexity risk through asset rotation can help mitigate the impact of widening spreads on the bank's asset valuations.",
        "ImpactChannels": ["Basis", "Convexity"],
        "Shocks": {"basis_widening": 15},
        "MetricsDelta": {"OCI": -2},
        "TradeList": ["Rotate into longer-duration munis by $400mn", "Sell $300mn in corporates to maintain liquidity"],
        "Assumptions": "Interest rate environment remains stable; spreads widen gradually."
    },
    {
        "Scenario": "Potential Regulatory Relief for HQLA",
        "Description": "Expectations of regulatory relief could benefit BoA's Level 1 and Level 2 asset mix, improving overall capital ratios and liquidity metrics.",
        "Probability": 0.15,
        "Rationale": "Regulatory changes may favor banks with strong liquidity profiles, allowing for a more favorable capital structure.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"tlac_relief": 25},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Increase high-quality asset purchases by $500mn", "Reduce reliance on short-term funding"],
        "Assumptions": "Regulatory environment improves; capital requirements ease."
    },
    {
        "Scenario": "Resilient Consumer Behavior Supporting NII Growth",
        "Description": "Strong consumer behavior, driven by economic stability, supports net interest income growth amidst rising rates.",
        "Probability": 0.10,
        "Rationale": "Resilient consumers can sustain loan demand, positively impacting NII and contributing to overall profitability.",
        "ImpactChannels": ["Consumer", "NII"],
        "Shocks": {"loan_demand": 5},
        "MetricsDelta": {"NII": +5},
        "TradeList": ["Increase consumer loan originations by $1bn in auto and personal loans", "Expand credit card offerings to boost market share"],
        "Assumptions": "Consumer confidence remains high; economic conditions support spending."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation with Gradual Easing",
        "Description": "Macroeconomic indicators show controlled inflation and gradual easing, supporting consumer and SME resilience, which leads to increased loan demand and stable net interest income.",
        "Probability": 0.30,
        "Rationale": "Stable inflation supports a favorable economic environment, boosting consumer confidence and spending, which in turn drives loan demand.",
        "ImpactChannels": ["Macro", "Consumer"],
        "Shocks": {"inflation": 0.5},
        "MetricsDelta": {"NII": +3, "LCR": +2},
        "TradeList": ["Increase holdings in Agency MBS by $500mn", "Expand consumer loan offerings by $1bn in personal loans and credit products"],
        "Assumptions": "Inflation remains controlled; consumer spending stays strong."
    },
    {
        "Scenario": "Diversified Funding Flows and Deposit Stability",
        "Description": "Stable deposit growth and diversified funding flows reinforce BoA's liquidity profile, allowing for more flexible asset management.",
        "Probability": 0.25,
        "Rationale": "A diversified funding stack reduces reliance on any single source and enhances liquidity, enabling BoA to respond effectively to market changes.",
        "ImpactChannels": ["Funding"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Rebalance deposit pricing to attract more retail deposits", "Increase term funding by $1bn through various channels"],
        "Assumptions": "Deposit competition remains stable; customer loyalty strengthens."
    },
    {
        "Scenario": "Favorable Basis Dynamics and Convexity Management",
        "Description": "Effective management of convexity risk through strategic asset allocation in a favorable basis environment allows BoA to maintain strong HQLA levels.",
        "Probability": 0.20,
        "Rationale": "Managing convexity risk through asset rotation can help mitigate the impact of widening spreads on the bank's asset valuations.",
        "ImpactChannels": ["Basis", "Convexity"],
        "Shocks": {"basis_widening": 15},
        "MetricsDelta": {"OCI": -2},
        "TradeList": ["Rotate into longer-duration munis by $400mn", "Sell $300mn in corporates to maintain liquidity"],
        "Assumptions": "Interest rate environment remains stable; spreads widen gradually."
    },
    {
        "Scenario": "Potential Regulatory Relief for HQLA",
        "Description": "Expectations of regulatory relief could benefit BoA's Level 1 and Level 2 asset mix, improving overall capital ratios and liquidity metrics.",
        "Probability": 0.15,
        "Rationale": "Regulatory changes may favor banks with strong liquidity profiles, allowing for a more favorable capital structure.",
        "ImpactChannels": ["Regulation"],
        "Shocks": {"tlac_relief": 25},
        "MetricsDelta": {"LCR": +4, "NSFR": +3},
        "TradeList": ["Increase high-quality asset purchases by $500mn", "Reduce reliance on short-term funding"],
        "Assumptions": "Regulatory environment improves; capital requirements ease."
    },
    {
        "Scenario": "Resilient Consumer Behavior Supporting NII Growth",
        "Description": "Strong consumer behavior, driven by economic stability, supports net interest income growth amidst rising rates.",
        "Probability": 0.10,
        "Rationale": "Resilient consumers can sustain loan demand, positively impacting NII and contributing to overall profitability.",
        "ImpactChannels": ["Consumer", "NII"],
        "Shocks": {"loan_demand": 5},
        "MetricsDelta": {"NII": +5},
        "TradeList": ["Increase consumer loan originations by $1bn in auto and personal loans", "Expand credit card offerings to boost market share"],
        "Assumptions": "Consumer confidence remains high; economic conditions support spending."
    }
]
```

