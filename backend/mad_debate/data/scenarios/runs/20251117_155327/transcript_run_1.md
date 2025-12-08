# Debate Transcript — Run 1

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening with Widening Credit Spreads",
        "Description": "Bear steepening of the yield curve with 10-year yields rising by 50 bps, IG OAS widening by 15 bps, and HY OAS widening by 45 bps.",
        "Probability": 0.22,
        "Rationale": "Reflects inflation fears and increased Treasury issuance leading to a bear steepening curve.",
        "ImpactChannels": ["Rates (50 bps)", "Credit OAS (15 bps IG, 45 bps HY)"],
        "Shocks": {"move_index": 50, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -5},
        "TradeList": ["Add $1bn in 10-year USTs", "Reduce $500mn in Level 2 MBS"],
        "Assumptions": "Economic conditions worsen, leading to increased yields and wider credit spreads."
    },
    {
        "Scenario": "Deposit Runoff Due to Economic Slowdown",
        "Description": "10% decline in retail deposits due to an economic slowdown.",
        "Probability": 0.18,
        "Rationale": "Consumer balance sheets are under pressure from inflation and rising rates.",
        "ImpactChannels": ["Deposits run-off (10%)"],
        "Shocks": {"depo_runoff": 10},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase $1bn in secured funding", "Reduce short-term borrowings by $500mn"],
        "Assumptions": "Economic conditions worsen, leading to reduced consumer deposits."
    },
    {
        "Scenario": "Gradual Easing with Controlled Inflation",
        "Description": "Gradual easing by the Fed amidst controlled inflation supports economic stability.",
        "Probability": 0.16,
        "Rationale": "Resilience of consumers and SMEs may contribute to gradual economic improvement, though risks remain.",
        "ImpactChannels": ["Rates stabilize", "Consumer confidence rises"],
        "Shocks": {"fed_easing": 25, "inflation_stability": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Increase allocation to stable corporate bonds by $250mn"],
        "Assumptions": "The Fed's approach to easing is gradual, supporting stable economic conditions."
    },
    {
        "Scenario": "Diversification Benefits from Deposits",
        "Description": "Continued diversification of deposits mitigates reliance on wholesale funding.",
        "Probability": 0.13,
        "Rationale": "A diversified deposit base strengthens liquidity position but economic uncertainties could impact growth.",
        "ImpactChannels": ["Deposit growth (3%)", "Reduced wholesale funding reliance"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +8, "NSFR": +5},
        "TradeList": ["Term out $250mn in wholesale funding", "Invest $500mn in high-quality munis"],
        "Assumptions": "Ongoing consumer confidence leads to modest deposit inflows amidst economic challenges."
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "Demand for MBS increases, leading to basis tightening by 15 bps.",
        "Probability": 0.14,
        "Rationale": "Improved market conditions and investor appetite support MBS demand, but risks in the mortgage market remain.",
        "ImpactChannels": ["MBS basis tightens (-15 bps)"],
        "Shocks": {"mbs_basis": -15},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Sell $200mn in lower-rated MBS"],
        "Assumptions": "Market conditions stabilize, fostering stronger demand for MBS while managing refinancing risks."
    },
    {
        "Scenario": "Regulatory Changes and TLAC Implications",
        "Description": "Announcement of new TLAC requirements increasing by 50 bps.",
        "Probability": 0.09,
        "Rationale": "Ongoing discussions about regulatory reforms suggest potential changes.",
        "ImpactChannels": ["Reg changes (TLAC increase)"],
        "Shocks": {"tlac_increase": 50},
        "MetricsDelta": {"LCR": -10, "NSFR": -10},
        "TradeList": ["Issue $1bn in long-term debt", "Reduce Level 2A holdings by $500mn"],
        "Assumptions": "Regulatory pressures mount, necessitating adjustments to capital structure."
    },
    {
        "Scenario": "Effective Convexity Management",
        "Description": "Strategic management of HQLA mitigates convexity risks.",
        "Probability": 0.05,
        "Rationale": "Maintaining a strong mix of Level 1 and Level 2 assets reduces rate sensitivity.",
        "ImpactChannels": ["Convexity risk mitigated"],
        "Shocks": {"convexity_risk": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Rebalance HQLA portfolio towards Level 1 assets", "Rotate $250mn into short-duration bonds"],
        "Assumptions": "Ongoing management effectively reduces exposure to interest rate volatility."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital efficiency and reduce compliance burdens.",
        "Probability": 0.03,
        "Rationale": "Favorable regulatory adjustments could improve capital management, though timing is uncertain.",
        "ImpactChannels": ["TLAC relief", "Improved capital ratios"],
        "Shocks": {"regulatory_relief": 25},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Issue $250mn in Tier 2 capital", "Reallocate capital reserves into productive assets"],
        "Assumptions": "Regulatory environment evolves positively, enhancing operational efficiency."
    }
]
```

## Round 1

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening with Widening Credit Spreads",
        "Description": "Bear steepening of the yield curve with 10-year yields rising by 50 bps, IG OAS widening by 15 bps, and HY OAS widening by 45 bps.",
        "Probability": 0.30,
        "Rationale": "Reflects inflation fears and increased Treasury issuance leading to a bear steepening curve.",
        "ImpactChannels": ["Rates (50 bps)", "Credit OAS (15 bps IG, 45 bps HY)"],
        "Shocks": {"move_index": 50, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -5},
        "TradeList": ["Add $1bn in 10-year USTs", "Reduce $500mn in Level 2 MBS"],
        "Assumptions": "Economic conditions worsen, leading to increased yields and wider credit spreads."
    },
    {
        "Scenario": "Regulatory Changes and TLAC Implications",
        "Description": "Announcement of new TLAC requirements increasing by 50 bps.",
        "Probability": 0.20,
        "Rationale": "Ongoing discussions about regulatory reforms suggest potential changes.",
        "ImpactChannels": ["Reg changes (TLAC increase)"],
        "Shocks": {"tlac_increase": 50},
        "MetricsDelta": {"LCR": -10, "NSFR": -10},
        "TradeList": ["Issue $1bn in long-term debt", "Reduce Level 2A holdings by $500mn"],
        "Assumptions": "Regulatory pressures mount, necessitating adjustments to capital structure."
    },
    {
        "Scenario": "Deposit Runoff Due to Economic Slowdown",
        "Description": "10% decline in retail deposits due to an economic slowdown.",
        "Probability": 0.25,
        "Rationale": "Consumer balance sheets are under pressure from inflation and rising rates.",
        "ImpactChannels": ["Deposits run-off (10%)"],
        "Shocks": {"depo_runoff": 10},
        "MetricsDelta": {"LCR": -15, "NSFR": -10},
        "TradeList": ["Increase $1bn in secured funding", "Reduce short-term borrowings by $500mn"],
        "Assumptions": "Economic conditions worsen, leading to reduced consumer deposits."
    },
    {
        "Scenario": "Stabilization of Credit Markets",
        "Description": "IG OAS decreases by 10 bps and HY OAS decreases by 20 bps.",
        "Probability": 0.15,
        "Rationale": "Improved investor sentiment stabilizes credit markets.",
        "ImpactChannels": ["Credit OAS (-10 bps IG, -20 bps HY)"],
        "Shocks": {"ig_oas": -10, "hy_oas": -20},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Buy $500mn in corporate bonds", "Increase MBS holdings by $300mn"],
        "Assumptions": "Investor sentiment improves, leading to tighter credit spreads."
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "MBS basis tightens by 25 bps.",
        "Probability": 0.10,
        "Rationale": "Improved liquidity and demand for MBS reflects market conditions.",
        "ImpactChannels": ["MBS basis (-25 bps)"],
        "Shocks": {"mbs_basis": -25},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Add $750mn in MBS via repo", "Sell $300mn in underperforming MBS"],
        "Assumptions": "MBS market stabilizes and demand increases, tightening the basis."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Gradual Easing with Stable Inflation",
        "Description": "Gradual easing by the Fed leads to stable inflation and improved consumer confidence.",
        "Probability": 0.35,
        "Rationale": "Resilience of consumers and SMEs supports economic growth.",
        "ImpactChannels": ["Rates stabilize", "Consumer spending increases"],
        "Shocks": {"fed_easing": 25, "inflation_stability": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $1bn in Agency MBS", "Increase allocation to stable corporate bonds by $500mn"],
        "Assumptions": "The Fed adopts a measured approach to easing, supporting economic stability."
    },
    {
        "Scenario": "Diversification Benefits from Deposit Growth",
        "Description": "Continued diversification of deposits and trading flows reduces reliance on wholesale funding.",
        "Probability": 0.25,
        "Rationale": "Increased consumer deposits bolster liquidity position.",
        "ImpactChannels": ["Deposit growth (5%)", "Reduced wholesale funding reliance"],
        "Shocks": {"deposit_growth": 5},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Term out $500mn in wholesale funding", "Invest $750mn in high-quality munis"],
        "Assumptions": "Ongoing consumer confidence leads to deposit inflows."
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "Demand for MBS increases, tightening the MBS basis by 25 bps.",
        "Probability": 0.20,
        "Rationale": "Improved market conditions and investor appetite support MBS.",
        "ImpactChannels": ["MBS basis tightens (-25 bps)"],
        "Shocks": {"mbs_basis": -25},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $1bn in Agency MBS", "Sell $300mn in lower-rated MBS"],
        "Assumptions": "Market conditions improve, leading to stronger demand for MBS."
    },
    {
        "Scenario": "Convexity Management via HQLA Adjustments",
        "Description": "Effective management of HQLA exposures mitigates convexity risks.",
        "Probability": 0.15,
        "Rationale": "Maintaining a strong mix of Level 1 and Level 2 assets reduces sensitivity to interest rate changes.",
        "ImpactChannels": ["Convexity risk mitigated"],
        "Shocks": {"convexity_risk": 0},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Rebalance HQLA portfolio towards Level 1 assets", "Rotate $500mn into short-duration bonds"],
        "Assumptions": "Ongoing management of asset mix effectively reduces interest rate sensitivity."
    },
    {
        "Scenario": "Regulatory Relief Enhancing Capital Efficiency",
        "Description": "Potential regulatory relief leads to enhanced capital efficiency.",
        "Probability": 0.05,
        "Rationale": "Regulatory changes could allow for better capital management.",
        "ImpactChannels": ["TLAC relief", "Improved capital ratios"],
        "Shocks": {"regulatory_relief": 50},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Issue $500mn in Tier 2 capital", "Reduce excess capital reserves by reallocating into productive assets"],
        "Assumptions": "Regulatory environment becomes more favorable, enhancing capital efficiency."
    }
]
```

## Round 2

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Gradual Easing with Stable Inflation",
        "Description": "Gradual easing by the Fed leads to stable inflation and improved consumer confidence.",
        "Probability": 0.20,
        "Rationale": "Resilience of consumers and SMEs supports economic growth, but inflation pressures remain.",
        "ImpactChannels": ["Rates stabilize", "Consumer spending increases"],
        "Shocks": {"fed_easing": 25, "inflation_stability": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Increase allocation to stable corporate bonds by $250mn"],
        "Assumptions": "The Fed adopts a cautious approach to easing, supporting economic stability amidst ongoing inflation."
    },
    {
        "Scenario": "Diversification Benefits from Deposit Growth",
        "Description": "Continued diversification of deposits and trading flows reduces reliance on wholesale funding.",
        "Probability": 0.15,
        "Rationale": "Increased consumer deposits bolster liquidity position, but economic uncertainty looms.",
        "ImpactChannels": ["Deposit growth (3%)", "Reduced wholesale funding reliance"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +8, "NSFR": +5},
        "TradeList": ["Term out $250mn in wholesale funding", "Invest $500mn in high-quality munis"],
        "Assumptions": "Ongoing consumer confidence leads to modest deposit inflows despite economic challenges."
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "Demand for MBS increases, tightening the MBS basis by 15 bps.",
        "Probability": 0.20,
        "Rationale": "Improved market conditions and investor appetite support MBS, but rate sensitivity remains.",
        "ImpactChannels": ["MBS basis tightens (-15 bps)"],
        "Shocks": {"mbs_basis": -15},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Sell $200mn in lower-rated MBS"],
        "Assumptions": "Market conditions stabilize, leading to stronger demand for MBS while managing refinancing risks."
    },
    {
        "Scenario": "Convexity Management via HQLA Adjustments",
        "Description": "Effective management of HQLA exposures mitigates convexity risks.",
        "Probability": 0.10,
        "Rationale": "Maintaining a strong mix of Level 1 and Level 2 assets reduces sensitivity to interest rate changes.",
        "ImpactChannels": ["Convexity risk mitigated"],
        "Shocks": {"convexity_risk": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Rebalance HQLA portfolio towards Level 1 assets", "Rotate $250mn into short-duration bonds"],
        "Assumptions": "Ongoing management of asset mix effectively reduces interest rate sensitivity."
    },
    {
        "Scenario": "Regulatory Relief Enhancing Capital Efficiency",
        "Description": "Potential regulatory relief leads to enhanced capital efficiency.",
        "Probability": 0.05,
        "Rationale": "Regulatory changes could allow for better capital management, though timing is uncertain.",
        "ImpactChannels": ["TLAC relief", "Improved capital ratios"],
        "Shocks": {"regulatory_relief": 25},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Issue $250mn in Tier 2 capital", "Reduce excess capital reserves by reallocating into productive assets"],
        "Assumptions": "Regulatory environment becomes more favorable, enhancing capital efficiency over time."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Gradual Easing with Controlled Inflation",
        "Description": "Gradual easing by the Fed amidst controlled inflation supports economic stability.",
        "Probability": 0.30,
        "Rationale": "Resilience of consumers and SMEs contributes to gradual economic improvement.",
        "ImpactChannels": ["Rates stabilize", "Consumer confidence rises"],
        "Shocks": {"fed_easing": 25, "inflation_stability": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $1bn in Agency MBS", "Increase allocation to stable corporate bonds by $500mn"],
        "Assumptions": "The Fed's approach to easing is gradual, supporting stable economic conditions."
    },
    {
        "Scenario": "Diversification Benefits from Deposits",
        "Description": "Continued diversification of deposits mitigates reliance on wholesale funding.",
        "Probability": 0.25,
        "Rationale": "A diversified deposit base strengthens liquidity position.",
        "ImpactChannels": ["Deposit growth (5%)", "Reduced wholesale funding reliance"],
        "Shocks": {"deposit_growth": 5},
        "MetricsDelta": {"LCR": +10, "NSFR": +5},
        "TradeList": ["Term out $500mn in wholesale funding", "Invest $750mn in high-quality munis"],
        "Assumptions": "Ongoing consumer confidence leads to deposit inflows, enhancing liquidity."
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "Demand for MBS increases, leading to basis tightening by 25 bps.",
        "Probability": 0.20,
        "Rationale": "Improved investor sentiment supports MBS demand.",
        "ImpactChannels": ["MBS basis tightens (-25 bps)"],
        "Shocks": {"mbs_basis": -25},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $750mn in Agency MBS", "Sell $300mn in lower-rated MBS"],
        "Assumptions": "Market conditions stabilize, fostering stronger demand for MBS."
    },
    {
        "Scenario": "Effective Convexity Management",
        "Description": "Strategic management of HQLA mitigates convexity risks.",
        "Probability": 0.15,
        "Rationale": "Maintaining a strong mix of Level 1 and Level 2 assets reduces rate sensitivity.",
        "ImpactChannels": ["Convexity risk mitigated"],
        "Shocks": {"convexity_risk": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Rebalance HQLA portfolio towards Level 1 assets", "Rotate $250mn into short-duration bonds"],
        "Assumptions": "Ongoing management effectively reduces exposure to interest rate volatility."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital efficiency and reduce compliance burdens.",
        "Probability": 0.10,
        "Rationale": "Favorable regulatory adjustments could improve capital management.",
        "ImpactChannels": ["TLAC relief", "Improved capital ratios"],
        "Shocks": {"regulatory_relief": 25},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Issue $250mn in Tier 2 capital", "Reallocate capital reserves into productive assets"],
        "Assumptions": "Regulatory environment evolves positively, enhancing operational efficiency."
    }
]
```

## Round 3

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Gradual Easing with Controlled Inflation",
        "Description": "Gradual easing by the Fed amidst controlled inflation supports economic stability.",
        "Probability": 0.20,
        "Rationale": "Resilience of consumers and SMEs may contribute to gradual economic improvement, though risks remain.",
        "ImpactChannels": ["Rates stabilize", "Consumer confidence rises"],
        "Shocks": {"fed_easing": 25, "inflation_stability": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Increase allocation to stable corporate bonds by $250mn"],
        "Assumptions": "The Fed's approach to easing is gradual, supporting stable economic conditions."
    },
    {
        "Scenario": "Diversification Benefits from Deposits",
        "Description": "Continued diversification of deposits mitigates reliance on wholesale funding.",
        "Probability": 0.15,
        "Rationale": "A diversified deposit base strengthens liquidity position but economic uncertainties could impact growth.",
        "ImpactChannels": ["Deposit growth (3%)", "Reduced wholesale funding reliance"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +8, "NSFR": +5},
        "TradeList": ["Term out $250mn in wholesale funding", "Invest $500mn in high-quality munis"],
        "Assumptions": "Ongoing consumer confidence leads to modest deposit inflows amidst economic challenges."
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "Demand for MBS increases, leading to basis tightening by 15 bps.",
        "Probability": 0.20,
        "Rationale": "Improved market conditions and investor appetite support MBS demand, but risks in the mortgage market remain.",
        "ImpactChannels": ["MBS basis tightens (-15 bps)"],
        "Shocks": {"mbs_basis": -15},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Sell $200mn in lower-rated MBS"],
        "Assumptions": "Market conditions stabilize, fostering stronger demand for MBS while managing refinancing risks."
    },
    {
        "Scenario": "Effective Convexity Management",
        "Description": "Strategic management of HQLA mitigates convexity risks.",
        "Probability": 0.10,
        "Rationale": "Maintaining a strong mix of Level 1 and Level 2 assets reduces rate sensitivity.",
        "ImpactChannels": ["Convexity risk mitigated"],
        "Shocks": {"convexity_risk": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Rebalance HQLA portfolio towards Level 1 assets", "Rotate $250mn into short-duration bonds"],
        "Assumptions": "Ongoing management effectively reduces exposure to interest rate volatility."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital efficiency and reduce compliance burdens.",
        "Probability": 0.05,
        "Rationale": "Favorable regulatory adjustments could improve capital management, though timing is uncertain.",
        "ImpactChannels": ["TLAC relief", "Improved capital ratios"],
        "Shocks": {"regulatory_relief": 25},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Issue $250mn in Tier 2 capital", "Reallocate capital reserves into productive assets"],
        "Assumptions": "Regulatory environment evolves positively, enhancing operational efficiency."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Gradual Easing with Controlled Inflation",
        "Description": "Gradual easing by the Fed amidst controlled inflation supports economic stability.",
        "Probability": 0.20,
        "Rationale": "Resilience of consumers and SMEs may contribute to gradual economic improvement, though risks remain.",
        "ImpactChannels": ["Rates stabilize", "Consumer confidence rises"],
        "Shocks": {"fed_easing": 25, "inflation_stability": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Increase allocation to stable corporate bonds by $250mn"],
        "Assumptions": "The Fed's approach to easing is gradual, supporting stable economic conditions."
    },
    {
        "Scenario": "Diversification Benefits from Deposits",
        "Description": "Continued diversification of deposits mitigates reliance on wholesale funding.",
        "Probability": 0.15,
        "Rationale": "A diversified deposit base strengthens liquidity position but economic uncertainties could impact growth.",
        "ImpactChannels": ["Deposit growth (3%)", "Reduced wholesale funding reliance"],
        "Shocks": {"deposit_growth": 3},
        "MetricsDelta": {"LCR": +8, "NSFR": +5},
        "TradeList": ["Term out $250mn in wholesale funding", "Invest $500mn in high-quality munis"],
        "Assumptions": "Ongoing consumer confidence leads to modest deposit inflows amidst economic challenges."
    },
    {
        "Scenario": "MBS Basis Tightening",
        "Description": "Demand for MBS increases, leading to basis tightening by 15 bps.",
        "Probability": 0.20,
        "Rationale": "Improved market conditions and investor appetite support MBS demand, but risks in the mortgage market remain.",
        "ImpactChannels": ["MBS basis tightens (-15 bps)"],
        "Shocks": {"mbs_basis": -15},
        "MetricsDelta": {"LCR": +5, "NSFR": +5},
        "TradeList": ["Add $500mn in Agency MBS", "Sell $200mn in lower-rated MBS"],
        "Assumptions": "Market conditions stabilize, fostering stronger demand for MBS while managing refinancing risks."
    },
    {
        "Scenario": "Effective Convexity Management",
        "Description": "Strategic management of HQLA mitigates convexity risks.",
        "Probability": 0.10,
        "Rationale": "Maintaining a strong mix of Level 1 and Level 2 assets reduces rate sensitivity.",
        "ImpactChannels": ["Convexity risk mitigated"],
        "Shocks": {"convexity_risk": 0},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Rebalance HQLA portfolio towards Level 1 assets", "Rotate $250mn into short-duration bonds"],
        "Assumptions": "Ongoing management effectively reduces exposure to interest rate volatility."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital efficiency and reduce compliance burdens.",
        "Probability": 0.05,
        "Rationale": "Favorable regulatory adjustments could improve capital management, though timing is uncertain.",
        "ImpactChannels": ["TLAC relief", "Improved capital ratios"],
        "Shocks": {"regulatory_relief": 25},
        "MetricsDelta": {"LCR": +3, "NSFR": +2},
        "TradeList": ["Issue $250mn in Tier 2 capital", "Reallocate capital reserves into productive assets"],
        "Assumptions": "Regulatory environment evolves positively, enhancing operational efficiency."
    }
]
```

