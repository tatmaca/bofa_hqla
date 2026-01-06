# Debate Transcript — Run 4

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term interest rates rise faster than short-term rates, leading to a bear steepening of the yield curve.",
        "Probability": 0.12,
        "Rationale": "A bear steepener will negatively impact the valuation of fixed income securities, especially in the Level 1 HQLA stack. Probability renormalized for total sum of 1.00.",
        "ImpactChannels": "Rates, Curve",
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Add $2bn USTs via repo", "Reduce Level 2A Agency MBS by $1bn"],
        "Assumptions": "Long-term rates increase due to inflation fears and Fed rate hikes.",
        "Signals": ["10y UST yield > 3.5%", "2y UST yield < 4.0%", "VIX > 18"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Credit Spread Widening",
        "Description": "A significant widening of credit spreads across investment-grade and high-yield bonds.",
        "Probability": 0.08,
        "Rationale": "Widening credit spreads could reflect market stress, impacting the valuation of corporate bonds in BoA's Level 2 stack. Probability renormalized for total sum of 1.00.",
        "ImpactChannels": "Credit",
        "Shocks": {"move_index": 110, "yield_curve": "flat", "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Reduce corporate bond holdings by $1bn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased defaults in the corporate sector due to economic slowdown.",
        "Signals": ["IG spread > 145 bps", "HY spread > 470 bps", "S&P 500 below 3,500"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Retail Deposit Beta Rise",
        "Description": "Increased beta on retail deposits leading to higher funding costs.",
        "Probability": 0.25,
        "Rationale": "As rates rise, depositors may seek higher interest returns, increasing the cost of funding for BoA. Probability renormalized for total sum of 1.00.",
        "ImpactChannels": "Deposits",
        "Shocks": {"move_index": 115, "yield_curve": "bear flattening", "credit_spreads": {"ig_oas": 10, "hy_oas": 20}},
        "MetricsDelta": {"LCR": -5, "NII": -3},
        "TradeList": ["Increase deposit rates by 25 bps", "Issue $1bn in term debt"],
        "Assumptions": "Consumers shift to higher-yielding savings accounts due to competitive market.",
        "Signals": ["Retail deposit growth < 1%", "Beta on deposits > 30%", "Fed rate increase > 50 bps"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "A tightening of the MBS basis due to reduced supply and increased demand for mortgage-backed securities.",
        "Probability": 0.25,
        "Rationale": "A tighter MBS basis would enhance the value of BoA's Level 2A Agency MBS holdings. Probability renormalized for total sum of 1.00.",
        "ImpactChannels": "MBS",
        "Shocks": {"move_index": 105, "yield_curve": "bull steepener", "credit_spreads": {"ig_oas": 5, "hy_oas": 15}},
        "MetricsDelta": {"LCR": 4, "OCI": 2},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce cash reserves by $500mn"],
        "Assumptions": "Lower mortgage origination volumes lead to higher prices for existing MBS.",
        "Signals": ["MBS basis < 20 bps", "Mortgage applications < 200k", "Fed MBS purchases announced"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Capital Changes",
        "Description": "Changes in regulatory capital requirements that increase the GSIB surcharge.",
        "Probability": 0.30,
        "Rationale": "Increased capital requirements could pressure BoA's capital ratios and limit growth. Probability renormalized for total sum of 1.00.",
        "ImpactChannels": "Regulation",
        "Shocks": {"move_index": 100, "yield_curve": "flat", "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Retain earnings to bolster capital ratios", "Limit share buybacks"],
        "Assumptions": "Regulatory environment becomes more stringent post-crisis.",
        "Signals": ["Basel IV implementation announcements", "Fed stress test results", "TLAC updates"],
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
        "Description": "Long-term interest rates rise faster than short-term rates, leading to a bear steepening of the yield curve.",
        "Probability": 0.20,
        "Rationale": "A bear steepener will negatively impact the valuation of fixed income securities, especially in the Level 1 HQLA stack.",
        "ImpactChannels": "Rates, Curve",
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Add $2bn USTs via repo", "Reduce Level 2A Agency MBS by $1bn"],
        "Assumptions": "Long-term rates increase due to inflation fears and Fed rate hikes.",
        "Signals": ["10y UST yield > 3.5%", "2y UST yield < 4.0%", "VIX > 18"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Credit Spread Widening",
        "Description": "A significant widening of credit spreads across investment-grade and high-yield bonds.",
        "Probability": 0.15,
        "Rationale": "Widening credit spreads could reflect market stress, impacting the valuation of corporate bonds in BoA's Level 2 stack.",
        "ImpactChannels": "Credit",
        "Shocks": {"move_index": 110, "yield_curve": "flat", "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Reduce corporate bond holdings by $1bn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased defaults in the corporate sector due to economic slowdown.",
        "Signals": ["IG spread > 145 bps", "HY spread > 470 bps", "S&P 500 below 3,500"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Retail Deposit Beta Rise",
        "Description": "Increased beta on retail deposits leading to higher funding costs.",
        "Probability": 0.25,
        "Rationale": "As rates rise, depositors may seek higher interest returns, increasing the cost of funding for BoA.",
        "ImpactChannels": "Deposits",
        "Shocks": {"move_index": 115, "yield_curve": "bear flattening", "credit_spreads": {"ig_oas": 10, "hy_oas": 20}},
        "MetricsDelta": {"LCR": -5, "NII": -3},
        "TradeList": ["Increase deposit rates by 25 bps", "Issue $1bn in term debt"],
        "Assumptions": "Consumers shift to higher-yielding savings accounts due to competitive market.",
        "Signals": ["Retail deposit growth < 1%", "Beta on deposits > 30%", "Fed rate increase > 50 bps"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "A tightening of the MBS basis due to reduced supply and increased demand for mortgage-backed securities.",
        "Probability": 0.10,
        "Rationale": "A tighter MBS basis would enhance the value of BoA's Level 2A Agency MBS holdings.",
        "ImpactChannels": "MBS",
        "Shocks": {"move_index": 105, "yield_curve": "bull steepener", "credit_spreads": {"ig_oas": 5, "hy_oas": 15}},
        "MetricsDelta": {"LCR": +4, "OCI": +2},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce cash reserves by $500mn"],
        "Assumptions": "Lower mortgage origination volumes lead to higher prices for existing MBS.",
        "Signals": ["MBS basis < 20 bps", "Mortgage applications < 200k", "Fed MBS purchases announced"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Capital Changes",
        "Description": "Changes in regulatory capital requirements that increase the GSIB surcharge.",
        "Probability": 0.30,
        "Rationale": "Increased capital requirements could pressure BoA's capital ratios and limit growth.",
        "ImpactChannels": "Regulation",
        "Shocks": {"move_index": 100, "yield_curve": "flat", "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Retain earnings to bolster capital ratios", "Limit share buybacks"],
        "Assumptions": "Regulatory environment becomes more stringent post-crisis.",
        "Signals": ["Basel IV implementation announcements", "Fed stress test results", "TLAC updates"],
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
        "Description": "Long-term interest rates rise faster than short-term rates, leading to a bear steepening of the yield curve.",
        "Probability": 0.15,
        "Rationale": "A bear steepener will negatively impact the valuation of fixed income securities, especially in the Level 1 HQLA stack.",
        "ImpactChannels": "Rates, Curve",
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Add $2bn USTs via repo", "Reduce Level 2A Agency MBS by $1bn"],
        "Assumptions": "Long-term rates increase due to inflation fears and Fed rate hikes.",
        "Signals": ["10y UST yield > 3.5%", "2y UST yield < 4.0%", "VIX > 18"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Credit Spread Widening",
        "Description": "A significant widening of credit spreads across investment-grade and high-yield bonds.",
        "Probability": 0.10,
        "Rationale": "Widening credit spreads could reflect market stress, impacting the valuation of corporate bonds in BoA's Level 2 stack.",
        "ImpactChannels": "Credit",
        "Shocks": {"move_index": 110, "yield_curve": "flat", "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Reduce corporate bond holdings by $1bn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased defaults in the corporate sector due to economic slowdown.",
        "Signals": ["IG spread > 145 bps", "HY spread > 470 bps", "S&P 500 below 3,500"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Retail Deposit Beta Rise",
        "Description": "Increased beta on retail deposits leading to higher funding costs.",
        "Probability": 0.25,
        "Rationale": "As rates rise, depositors may seek higher interest returns, increasing the cost of funding for BoA.",
        "ImpactChannels": "Deposits",
        "Shocks": {"move_index": 115, "yield_curve": "bear flattening", "credit_spreads": {"ig_oas": 10, "hy_oas": 20}},
        "MetricsDelta": {"LCR": -5, "NII": -3},
        "TradeList": ["Increase deposit rates by 25 bps", "Issue $1bn in term debt"],
        "Assumptions": "Consumers shift to higher-yielding savings accounts due to competitive market.",
        "Signals": ["Retail deposit growth < 1%", "Beta on deposits > 30%", "Fed rate increase > 50 bps"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "A tightening of the MBS basis due to reduced supply and increased demand for mortgage-backed securities.",
        "Probability": 0.20,
        "Rationale": "A tighter MBS basis would enhance the value of BoA's Level 2A Agency MBS holdings.",
        "ImpactChannels": "MBS",
        "Shocks": {"move_index": 105, "yield_curve": "bull steepener", "credit_spreads": {"ig_oas": 5, "hy_oas": 15}},
        "MetricsDelta": {"LCR": +4, "OCI": +2},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce cash reserves by $500mn"],
        "Assumptions": "Lower mortgage origination volumes lead to higher prices for existing MBS.",
        "Signals": ["MBS basis < 20 bps", "Mortgage applications < 200k", "Fed MBS purchases announced"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Capital Changes",
        "Description": "Changes in regulatory capital requirements that increase the GSIB surcharge.",
        "Probability": 0.30,
        "Rationale": "Increased capital requirements could pressure BoA's capital ratios and limit growth.",
        "ImpactChannels": "Regulation",
        "Shocks": {"move_index": 100, "yield_curve": "flat", "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Retain earnings to bolster capital ratios", "Limit share buybacks"],
        "Assumptions": "Regulatory environment becomes more stringent post-crisis.",
        "Signals": ["Basel IV implementation announcements", "Fed stress test results", "TLAC updates"],
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
        "Description": "Long-term interest rates rise faster than short-term rates, leading to a bear steepening of the yield curve.",
        "Probability": 0.15,
        "Rationale": "A bear steepener will negatively impact the valuation of fixed income securities, especially in the Level 1 HQLA stack.",
        "ImpactChannels": "Rates, Curve",
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Add $2bn USTs via repo", "Reduce Level 2A Agency MBS by $1bn"],
        "Assumptions": "Long-term rates increase due to inflation fears and Fed rate hikes.",
        "Signals": ["10y UST yield > 3.5%", "2y UST yield < 4.0%", "VIX > 18"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Credit Spread Widening",
        "Description": "A significant widening of credit spreads across investment-grade and high-yield bonds.",
        "Probability": 0.10,
        "Rationale": "Widening credit spreads could reflect market stress, impacting the valuation of corporate bonds in BoA's Level 2 stack.",
        "ImpactChannels": "Credit",
        "Shocks": {"move_index": 110, "yield_curve": "flat", "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Reduce corporate bond holdings by $1bn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased defaults in the corporate sector due to economic slowdown.",
        "Signals": ["IG spread > 145 bps", "HY spread > 470 bps", "S&P 500 below 3,500"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Retail Deposit Beta Rise",
        "Description": "Increased beta on retail deposits leading to higher funding costs.",
        "Probability": 0.30,
        "Rationale": "As rates rise, depositors may seek higher interest returns, increasing the cost of funding for BoA.",
        "ImpactChannels": "Deposits",
        "Shocks": {"move_index": 115, "yield_curve": "bear flattening", "credit_spreads": {"ig_oas": 10, "hy_oas": 20}},
        "MetricsDelta": {"LCR": -5, "NII": -3},
        "TradeList": ["Increase deposit rates by 25 bps", "Issue $1bn in term debt"],
        "Assumptions": "Consumers shift to higher-yielding savings accounts due to competitive market.",
        "Signals": ["Retail deposit growth < 1%", "Beta on deposits > 30%", "Fed rate increase > 50 bps"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "A tightening of the MBS basis due to reduced supply and increased demand for mortgage-backed securities.",
        "Probability": 0.25,
        "Rationale": "A tighter MBS basis would enhance the value of BoA's Level 2A Agency MBS holdings.",
        "ImpactChannels": "MBS",
        "Shocks": {"move_index": 105, "yield_curve": "bull steepener", "credit_spreads": {"ig_oas": 5, "hy_oas": 15}},
        "MetricsDelta": {"LCR": +4, "OCI": +2},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce cash reserves by $500mn"],
        "Assumptions": "Lower mortgage origination volumes lead to higher prices for existing MBS.",
        "Signals": ["MBS basis < 20 bps", "Mortgage applications < 200k", "Fed MBS purchases announced"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Capital Changes",
        "Description": "Changes in regulatory capital requirements that increase the GSIB surcharge.",
        "Probability": 0.20,
        "Rationale": "Increased capital requirements could pressure BoA's capital ratios and limit growth.",
        "ImpactChannels": "Regulation",
        "Shocks": {"move_index": 100, "yield_curve": "flat", "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Retain earnings to bolster capital ratios", "Limit share buybacks"],
        "Assumptions": "Regulatory environment becomes more stringent post-crisis.",
        "Signals": ["Basel IV implementation announcements", "Fed stress test results", "TLAC updates"],
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
        "Description": "Long-term interest rates rise faster than short-term rates, leading to a bear steepening of the yield curve.",
        "Probability": 0.15,
        "Rationale": "A bear steepener will negatively impact the valuation of fixed income securities, especially in the Level 1 HQLA stack.",
        "ImpactChannels": "Rates, Curve",
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Add $2bn USTs via repo", "Reduce Level 2A Agency MBS by $1bn"],
        "Assumptions": "Long-term rates increase due to inflation fears and Fed rate hikes.",
        "Signals": ["10y UST yield > 3.5%", "2y UST yield < 4.0%", "VIX > 18"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Credit Spread Widening",
        "Description": "A significant widening of credit spreads across investment-grade and high-yield bonds.",
        "Probability": 0.10,
        "Rationale": "Widening credit spreads could reflect market stress, impacting the valuation of corporate bonds in BoA's Level 2 stack.",
        "ImpactChannels": "Credit",
        "Shocks": {"move_index": 110, "yield_curve": "flat", "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Reduce corporate bond holdings by $1bn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased defaults in the corporate sector due to economic slowdown.",
        "Signals": ["IG spread > 145 bps", "HY spread > 470 bps", "S&P 500 below 3,500"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Retail Deposit Beta Rise",
        "Description": "Increased beta on retail deposits leading to higher funding costs.",
        "Probability": 0.25,
        "Rationale": "As rates rise, depositors may seek higher interest returns, increasing the cost of funding for BoA.",
        "ImpactChannels": "Deposits",
        "Shocks": {"move_index": 115, "yield_curve": "bear flattening", "credit_spreads": {"ig_oas": 10, "hy_oas": 20}},
        "MetricsDelta": {"LCR": -5, "NII": -3},
        "TradeList": ["Increase deposit rates by 25 bps", "Issue $1bn in term debt"],
        "Assumptions": "Consumers shift to higher-yielding savings accounts due to competitive market.",
        "Signals": ["Retail deposit growth < 1%", "Beta on deposits > 30%", "Fed rate increase > 50 bps"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "A tightening of the MBS basis due to reduced supply and increased demand for mortgage-backed securities.",
        "Probability": 0.25,
        "Rationale": "A tighter MBS basis would enhance the value of BoA's Level 2A Agency MBS holdings.",
        "ImpactChannels": "MBS",
        "Shocks": {"move_index": 105, "yield_curve": "bull steepener", "credit_spreads": {"ig_oas": 5, "hy_oas": 15}},
        "MetricsDelta": {"LCR": +4, "OCI": +2},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce cash reserves by $500mn"],
        "Assumptions": "Lower mortgage origination volumes lead to higher prices for existing MBS.",
        "Signals": ["MBS basis < 20 bps", "Mortgage applications < 200k", "Fed MBS purchases announced"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Capital Changes",
        "Description": "Changes in regulatory capital requirements that increase the GSIB surcharge.",
        "Probability": 0.25,
        "Rationale": "Increased capital requirements could pressure BoA's capital ratios and limit growth.",
        "ImpactChannels": "Regulation",
        "Shocks": {"move_index": 100, "yield_curve": "flat", "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Retain earnings to bolster capital ratios", "Limit share buybacks"],
        "Assumptions": "Regulatory environment becomes more stringent post-crisis.",
        "Signals": ["Basel IV implementation announcements", "Fed stress test results", "TLAC updates"],
        "PredictionDate": "2025-12-17"
    }
]
```

## Round 3

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener",
        "Description": "Long-term interest rates rise faster than short-term rates, leading to a bear steepening of the yield curve.",
        "Probability": 0.12,
        "Rationale": "A bear steepener will negatively impact the valuation of fixed income securities, especially in the Level 1 HQLA stack.",
        "ImpactChannels": "Rates, Curve",
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Add $2bn USTs via repo", "Reduce Level 2A Agency MBS by $1bn"],
        "Assumptions": "Long-term rates increase due to inflation fears and Fed rate hikes.",
        "Signals": ["10y UST yield > 3.5%", "2y UST yield < 4.0%", "VIX > 18"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Credit Spread Widening",
        "Description": "A significant widening of credit spreads across investment-grade and high-yield bonds.",
        "Probability": 0.08,
        "Rationale": "Widening credit spreads could reflect market stress, impacting the valuation of corporate bonds in BoA's Level 2 stack.",
        "ImpactChannels": "Credit",
        "Shocks": {"move_index": 110, "yield_curve": "flat", "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Reduce corporate bond holdings by $1bn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased defaults in the corporate sector due to economic slowdown.",
        "Signals": ["IG spread > 145 bps", "HY spread > 470 bps", "S&P 500 below 3,500"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Retail Deposit Beta Rise",
        "Description": "Increased beta on retail deposits leading to higher funding costs.",
        "Probability": 0.25,
        "Rationale": "As rates rise, depositors may seek higher interest returns, increasing the cost of funding for BoA.",
        "ImpactChannels": "Deposits",
        "Shocks": {"move_index": 115, "yield_curve": "bear flattening", "credit_spreads": {"ig_oas": 10, "hy_oas": 20}},
        "MetricsDelta": {"LCR": -5, "NII": -3},
        "TradeList": ["Increase deposit rates by 25 bps", "Issue $1bn in term debt"],
        "Assumptions": "Consumers shift to higher-yielding savings accounts due to competitive market.",
        "Signals": ["Retail deposit growth < 1%", "Beta on deposits > 30%", "Fed rate increase > 50 bps"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "A tightening of the MBS basis due to reduced supply and increased demand for mortgage-backed securities.",
        "Probability": 0.25,
        "Rationale": "A tighter MBS basis would enhance the value of BoA's Level 2A Agency MBS holdings.",
        "ImpactChannels": "MBS",
        "Shocks": {"move_index": 105, "yield_curve": "bull steepener", "credit_spreads": {"ig_oas": 5, "hy_oas": 15}},
        "MetricsDelta": {"LCR": +4, "OCI": +2},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce cash reserves by $500mn"],
        "Assumptions": "Lower mortgage origination volumes lead to higher prices for existing MBS.",
        "Signals": ["MBS basis < 20 bps", "Mortgage applications < 200k", "Fed MBS purchases announced"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Capital Changes",
        "Description": "Changes in regulatory capital requirements that increase the GSIB surcharge.",
        "Probability": 0.30,
        "Rationale": "Increased capital requirements could pressure BoA's capital ratios and limit growth.",
        "ImpactChannels": "Regulation",
        "Shocks": {"move_index": 100, "yield_curve": "flat", "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Retain earnings to bolster capital ratios", "Limit share buybacks"],
        "Assumptions": "Regulatory environment becomes more stringent post-crisis.",
        "Signals": ["Basel IV implementation announcements", "Fed stress test results", "TLAC updates"],
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
        "Description": "Long-term interest rates rise faster than short-term rates, leading to a bear steepening of the yield curve.",
        "Probability": 0.12,
        "Rationale": "A bear steepener will negatively impact the valuation of fixed income securities, especially in the Level 1 HQLA stack.",
        "ImpactChannels": "Rates, Curve",
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -3, "NSFR": -2},
        "TradeList": ["Add $2bn USTs via repo", "Reduce Level 2A Agency MBS by $1bn"],
        "Assumptions": "Long-term rates increase due to inflation fears and Fed rate hikes.",
        "Signals": ["10y UST yield > 3.5%", "2y UST yield < 4.0%", "VIX > 18"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Credit Spread Widening",
        "Description": "A significant widening of credit spreads across investment-grade and high-yield bonds.",
        "Probability": 0.08,
        "Rationale": "Widening credit spreads could reflect market stress, impacting the valuation of corporate bonds in BoA's Level 2 stack.",
        "ImpactChannels": "Credit",
        "Shocks": {"move_index": 110, "yield_curve": "flat", "credit_spreads": {"ig_oas": 25, "hy_oas": 60}},
        "MetricsDelta": {"LCR": -2, "OCI": -1},
        "TradeList": ["Reduce corporate bond holdings by $1bn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased defaults in the corporate sector due to economic slowdown.",
        "Signals": ["IG spread > 145 bps", "HY spread > 470 bps", "S&P 500 below 3,500"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Retail Deposit Beta Rise",
        "Description": "Increased beta on retail deposits leading to higher funding costs.",
        "Probability": 0.25,
        "Rationale": "As rates rise, depositors may seek higher interest returns, increasing the cost of funding for BoA.",
        "ImpactChannels": "Deposits",
        "Shocks": {"move_index": 115, "yield_curve": "bear flattening", "credit_spreads": {"ig_oas": 10, "hy_oas": 20}},
        "MetricsDelta": {"LCR": -5, "NII": -3},
        "TradeList": ["Increase deposit rates by 25 bps", "Issue $1bn in term debt"],
        "Assumptions": "Consumers shift to higher-yielding savings accounts due to competitive market.",
        "Signals": ["Retail deposit growth < 1%", "Beta on deposits > 30%", "Fed rate increase > 50 bps"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "A tightening of the MBS basis due to reduced supply and increased demand for mortgage-backed securities.",
        "Probability": 0.25,
        "Rationale": "A tighter MBS basis would enhance the value of BoA's Level 2A Agency MBS holdings.",
        "ImpactChannels": "MBS",
        "Shocks": {"move_index": 105, "yield_curve": "bull steepener", "credit_spreads": {"ig_oas": 5, "hy_oas": 15}},
        "MetricsDelta": {"LCR": +4, "OCI": +2},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce cash reserves by $500mn"],
        "Assumptions": "Lower mortgage origination volumes lead to higher prices for existing MBS.",
        "Signals": ["MBS basis < 20 bps", "Mortgage applications < 200k", "Fed MBS purchases announced"],
        "PredictionDate": "2025-12-17"
    },
    {
        "Scenario": "Regulatory Capital Changes",
        "Description": "Changes in regulatory capital requirements that increase the GSIB surcharge.",
        "Probability": 0.30,
        "Rationale": "Increased capital requirements could pressure BoA's capital ratios and limit growth.",
        "ImpactChannels": "Regulation",
        "Shocks": {"move_index": 100, "yield_curve": "flat", "credit_spreads": {"ig_oas": 0, "hy_oas": 0}},
        "MetricsDelta": {"LCR": -4, "NSFR": -3},
        "TradeList": ["Retain earnings to bolster capital ratios", "Limit share buybacks"],
        "Assumptions": "Regulatory environment becomes more stringent post-crisis.",
        "Signals": ["Basel IV implementation announcements", "Fed stress test results", "TLAC updates"],
        "PredictionDate": "2025-12-17"
    }
]
```

