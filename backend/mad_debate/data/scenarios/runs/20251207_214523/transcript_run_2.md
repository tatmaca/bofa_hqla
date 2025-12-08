# Debate Transcript — Run 2

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Spreads",
        "Description": "Interest rates rise with a bear steepening of the yield curve; IG credit spreads widen by 15 bps and HY spreads by 45 bps.",
        "Probability": 0.18,
        "Rationale": "Controlled inflation and stable economic growth lead to a gradual bear steepening, but consumer resilience limits extreme impacts on funding.",
        "ImpactChannels": "Rates (20 bps increase), Curve (bear steepener), Credit OAS (15 bps IG, 45 bps HY)",
        "Shocks": {"move": 120, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $1bn T-bills via repo", "Engage in interest rate hedging strategies"],
        "Assumptions": "Inflation stabilizes; economic growth remains consistent; credit quality holds firm."
    },
    {
        "Scenario": "Regulatory Shock from Basel Endgame",
        "Description": "Tighter capital requirements from Basel reforms increase G-SIB surcharges, impacting capital ratios.",
        "Probability": 0.22,
        "Rationale": "Ongoing discussions on regulatory reforms suggest an increased likelihood of stricter liquidity requirements.",
        "ImpactChannels": "Regulatory changes (increased capital requirements)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Increase liquidity reserves by $1bn", "Proactively engage with regulators to influence outcomes"],
        "Assumptions": "Regulatory environment changes rapidly; market adapts efficiently to new requirements."
    },
    {
        "Scenario": "Deposit Runoff from Wealth Segment",
        "Description": "Rising interest rates lead to a 5% runoff in wealth management deposits as clients seek higher yields.",
        "Probability": 0.15,
        "Rationale": "Higher-yielding investment alternatives may attract deposits, but BoA's diverse offerings help retain clients.",
        "ImpactChannels": "Deposits (5% runoff)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Enhance product offerings to retain clients", "Increase wholesale funding by $500mn"],
        "Assumptions": "Interest rates rise but remain within manageable limits; client loyalty remains strong."
    },
    {
        "Scenario": "MBS Market Dislocation",
        "Description": "MBS basis widens by 35 bps due to increased supply and reduced refinancing activity.",
        "Probability": 0.18,
        "Rationale": "Market dislocations may affect MBS valuations, but BoA's active management can mitigate negative impacts.",
        "ImpactChannels": "MBS basis (35 bps widening)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -6, "NSFR": -2},
        "TradeList": ["Reduce MBS holdings by $500mn", "Reallocate funds to T-bills to optimize portfolio"],
        "Assumptions": "Increased Treasury issuance; mortgage rates remain elevated but stable."
    },
    {
        "Scenario": "Commodity Price Shock",
        "Description": "Commodity prices rise 20% due to geopolitical tensions, leading to increased credit spreads.",
        "Probability": 0.12,
        "Rationale": "Rising commodity prices could trigger liquidity concerns, but BoA's credit risk management strategies are robust.",
        "ImpactChannels": "Credit OAS (20% increase in commodity-linked spreads)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -7, "NSFR": -3},
        "TradeList": ["Increase credit risk provisions by $500mn", "Monitor commodity-linked exposures closely and adjust accordingly"],
        "Assumptions": "Geopolitical tensions escalate; commodity market volatility remains high."
    },
    {
        "Scenario": "Benign Base Case",
        "Description": "Rates and spreads remain stable, deposit base is steady, and no major regulatory or market shocks occur.",
        "Probability": 0.15,
        "Rationale": "Macroeconomic conditions remain supportive, with moderate growth and no significant disruptions.",
        "ImpactChannels": "Rates (unchanged), Credit spreads (unchanged), Deposits (stable)",
        "Shocks": {},
        "MetricsDelta": {"LCR": 0, "NSFR": 0},
        "TradeList": ["Maintain current HQLA mix", "Continue standard client engagement"],
        "Assumptions": "Inflation is contained; regulatory environment is stable; no major geopolitical events."
    }
]
```

## Round 1

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Spreads",
        "Description": "Interest rates rise with a bear steepening of the yield curve; IG credit spreads widen by 15 bps and HY spreads by 45 bps.",
        "Probability": 0.25,
        "Rationale": "Inflationary pressures lead to rising rates, affecting HQLA valuations and increasing funding costs.",
        "ImpactChannels": "Rates (20 bps), Curve (bear steepener), Credit OAS (15 bps IG, 45 bps HY)",
        "Shocks": {"move": 120, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $1bn T-bills via repo", "Reduce Agency MBS exposure by $500mn"],
        "Assumptions": "Inflation remains elevated; economic growth slows; credit quality deteriorates."
    },
    {
        "Scenario": "Regulatory Shock from Basel Endgame",
        "Description": "Tighter capital requirements from Basel reforms increase G-SIB surcharges, impacting capital ratios.",
        "Probability": 0.15,
        "Rationale": "Increased regulatory scrutiny necessitates higher liquidity buffers, impacting profitability.",
        "ImpactChannels": "Reg changes (increased capital requirements)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Increase liquidity reserves by $2bn"],
        "Assumptions": "Regulatory discussions culminate in tighter rules; market reacts with heightened scrutiny."
    },
    {
        "Scenario": "Deposit Runoff from Wealth Segment",
        "Description": "Rising interest rates lead to a 5% runoff in wealth management deposits as clients seek better yields.",
        "Probability": 0.20,
        "Rationale": "As rates increase, higher-yielding alternatives attract deposits away from BoA.",
        "ImpactChannels": "Deposits (runoff 5%)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Increase wholesale funding by $1bn", "Adjust deposit rates to retain clients"],
        "Assumptions": "Rates continue to rise; competitive pressure increases from alternative investments."
    },
    {
        "Scenario": "MBS Market Dislocation",
        "Description": "MBS basis widens by 35 bps due to increased supply and reduced refinancing activity.",
        "Probability": 0.20,
        "Rationale": "Market dislocations affect MBS valuations, impacting overall portfolio health.",
        "ImpactChannels": "MBS basis (35 bps widening)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -6, "NSFR": -2},
        "TradeList": ["Reduce MBS holdings by $750mn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased Treasury issuance; mortgage rates remain elevated."
    },
    {
        "Scenario": "Commodity Price Shock",
        "Description": "Commodity prices rise 20% due to geopolitical tensions, leading to increased credit spreads.",
        "Probability": 0.20,
        "Rationale": "Rising commodity prices could trigger a liquidity squeeze, affecting credit quality.",
        "ImpactChannels": "Credit OAS (20% rise in commodity-linked spreads)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -7, "NSFR": -3},
        "TradeList": ["Increase credit risk provisions by $1bn", "Monitor commodity-linked exposures closely"],
        "Assumptions": "Geopolitical tensions escalate; commodity markets react violently."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Spreads",
        "Description": "Interest rates rise with a bear steepening of the yield curve; IG credit spreads widen by 15 bps and HY spreads by 45 bps.",
        "Probability": 0.25,
        "Rationale": "Inflationary pressures lead to rising rates, affecting HQLA valuations and increasing funding costs.",
        "ImpactChannels": "Rates (20 bps), Curve (bear steepener), Credit OAS (15 bps IG, 45 bps HY)",
        "Shocks": {"move": 120, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $1bn T-bills via repo", "Reduce Agency MBS exposure by $500mn"],
        "Assumptions": "Inflation remains elevated; economic growth slows; credit quality deteriorates."
    },
    {
        "Scenario": "Regulatory Shock from Basel Endgame",
        "Description": "Tighter capital requirements from Basel reforms increase G-SIB surcharges, impacting capital ratios.",
        "Probability": 0.15,
        "Rationale": "Increased regulatory scrutiny necessitates higher liquidity buffers, impacting profitability.",
        "ImpactChannels": "Reg changes (increased capital requirements)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Increase liquidity reserves by $2bn"],
        "Assumptions": "Regulatory discussions culminate in tighter rules; market reacts with heightened scrutiny."
    },
    {
        "Scenario": "Deposit Runoff from Wealth Segment",
        "Description": "Rising interest rates lead to a 5% runoff in wealth management deposits as clients seek better yields.",
        "Probability": 0.20,
        "Rationale": "As rates increase, higher-yielding alternatives attract deposits away from BoA.",
        "ImpactChannels": "Deposits (runoff 5%)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Increase wholesale funding by $1bn", "Adjust deposit rates to retain clients"],
        "Assumptions": "Rates continue to rise; competitive pressure increases from alternative investments."
    },
    {
        "Scenario": "MBS Market Dislocation",
        "Description": "MBS basis widens by 35 bps due to increased supply and reduced refinancing activity.",
        "Probability": 0.20,
        "Rationale": "Market dislocations affect MBS valuations, impacting overall portfolio health.",
        "ImpactChannels": "MBS basis (35 bps widening)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -6, "NSFR": -2},
        "TradeList": ["Reduce MBS holdings by $750mn", "Increase cash reserves by $500mn"],
        "Assumptions": "Increased Treasury issuance; mortgage rates remain elevated."
    },
    {
        "Scenario": "Commodity Price Shock",
        "Description": "Commodity prices rise 20% due to geopolitical tensions, leading to increased credit spreads.",
        "Probability": 0.20,
        "Rationale": "Rising commodity prices could trigger a liquidity squeeze, affecting credit quality.",
        "ImpactChannels": "Credit OAS (20% rise in commodity-linked spreads)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -7, "NSFR": -3},
        "TradeList": ["Increase credit risk provisions by $1bn", "Monitor commodity-linked exposures closely"],
        "Assumptions": "Geopolitical tensions escalate; commodity markets react violently."
    }
]
```

## Round 2

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Spreads",
        "Description": "Interest rates rise with a bear steepening of the yield curve; IG credit spreads widen by 15 bps and HY spreads by 45 bps.",
        "Probability": 0.20,
        "Rationale": "Persistent inflation leads to a bear steepening, impacting HQLA valuations and increasing funding costs.",
        "ImpactChannels": "Rates (20 bps increase), Curve (bear steepener), Credit OAS (15 bps IG, 45 bps HY)",
        "Shocks": {"move": 120, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $1bn T-bills via repo", "Reduce Agency MBS exposure by $500mn"],
        "Assumptions": "Inflation remains elevated; economic growth slows moderately; credit quality weakens slightly."
    },
    {
        "Scenario": "Regulatory Shock from Basel Endgame",
        "Description": "Tighter capital requirements from Basel reforms increase G-SIB surcharges, impacting capital ratios.",
        "Probability": 0.10,
        "Rationale": "Potential regulatory changes require higher liquidity buffers, impacting profitability.",
        "ImpactChannels": "Regulatory changes (increased capital requirements)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Increase liquidity reserves by $1bn", "Engage with regulators for clarity"],
        "Assumptions": "Regulatory environment evolves slowly; market adapts to changes without significant disruption."
    },
    {
        "Scenario": "Deposit Runoff from Wealth Segment",
        "Description": "Rising interest rates lead to a 5% runoff in wealth management deposits as clients seek higher yields.",
        "Probability": 0.15,
        "Rationale": "As rates increase, higher-yielding alternatives attract deposits away from BoA.",
        "ImpactChannels": "Deposits (5% runoff)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Increase wholesale funding by $500mn", "Enhance client engagement strategies"],
        "Assumptions": "Interest rates rise but remain within a manageable range; client loyalty remains strong."
    },
    {
        "Scenario": "MBS Market Dislocation",
        "Description": "MBS basis widens by 35 bps due to increased supply and reduced refinancing activity.",
        "Probability": 0.20,
        "Rationale": "Market dislocations affect MBS valuations, impacting overall portfolio health.",
        "ImpactChannels": "MBS basis (35 bps widening)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -6, "NSFR": -2},
        "TradeList": ["Reduce MBS holdings by $500mn", "Reallocate funds to T-bills"],
        "Assumptions": "Increased Treasury issuance; mortgage rates remain elevated but stable."
    },
    {
        "Scenario": "Commodity Price Shock",
        "Description": "Commodity prices rise 20% due to geopolitical tensions, leading to increased credit spreads.",
        "Probability": 0.15,
        "Rationale": "Rising commodity prices trigger a liquidity squeeze, affecting credit quality.",
        "ImpactChannels": "Credit OAS (20% increase in commodity-linked spreads)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -7, "NSFR": -3},
        "TradeList": ["Increase credit risk provisions by $500mn", "Monitor commodity-linked exposures closely"],
        "Assumptions": "Geopolitical tensions escalate; commodity market volatility remains high."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Spreads",
        "Description": "Interest rates rise with a bear steepening of the yield curve; IG credit spreads widen by 15 bps and HY spreads by 45 bps.",
        "Probability": 0.20,
        "Rationale": "Controlled inflation leads to rising rates, but consumer resilience mitigates extreme impacts on funding.",
        "ImpactChannels": "Rates (20 bps increase), Curve (bear steepener), Credit OAS (15 bps IG, 45 bps HY)",
        "Shocks": {"move": 120, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $1bn T-bills via repo", "Reduce Agency MBS exposure by $500mn"],
        "Assumptions": "Inflation remains elevated; economic growth slows moderately; credit quality weakens slightly."
    },
    {
        "Scenario": "Regulatory Shock from Basel Endgame",
        "Description": "Tighter capital requirements from Basel reforms increase G-SIB surcharges, impacting capital ratios.",
        "Probability": 0.10,
        "Rationale": "Regulatory changes may require higher liquidity buffers, but BoA's funding stack is robust enough to adapt.",
        "ImpactChannels": "Regulatory changes (increased capital requirements)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Increase liquidity reserves by $1bn", "Engage with regulators for clarity"],
        "Assumptions": "Regulatory environment evolves slowly; market adapts to changes without significant disruption."
    },
    {
        "Scenario": "Deposit Runoff from Wealth Segment",
        "Description": "Rising interest rates lead to a 5% runoff in wealth management deposits as clients seek higher yields.",
        "Probability": 0.15,
        "Rationale": "Higher-yielding alternatives may attract deposits, but BoA's diversified base may limit significant outflows.",
        "ImpactChannels": "Deposits (5% runoff)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Increase wholesale funding by $500mn", "Enhance client engagement strategies"],
        "Assumptions": "Interest rates rise but remain within a manageable range; client loyalty remains strong."
    },
    {
        "Scenario": "MBS Market Dislocation",
        "Description": "MBS basis widens by 35 bps due to increased supply and reduced refinancing activity.",
        "Probability": 0.20,
        "Rationale": "Market dislocations affect MBS valuations; however, BoA's active management can mitigate risks.",
        "ImpactChannels": "MBS basis (35 bps widening)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -6, "NSFR": -2},
        "TradeList": ["Reduce MBS holdings by $500mn", "Reallocate funds to T-bills"],
        "Assumptions": "Increased Treasury issuance; mortgage rates remain elevated but stable."
    },
    {
        "Scenario": "Commodity Price Shock",
        "Description": "Commodity prices rise 20% due to geopolitical tensions, leading to increased credit spreads.",
        "Probability": 0.15,
        "Rationale": "Rising commodity prices could trigger a liquidity squeeze, but BoA's position may remain stable.",
        "ImpactChannels": "Credit OAS (20% increase in commodity-linked spreads)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -7, "NSFR": -3},
        "TradeList": ["Increase credit risk provisions by $500mn", "Monitor commodity-linked exposures closely"],
        "Assumptions": "Geopolitical tensions escalate; commodity market volatility remains high."
    }
]
```

## Round 3

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Spreads",
        "Description": "Interest rates rise with a bear steepening of the yield curve; IG credit spreads widen by 15 bps and HY spreads by 45 bps.",
        "Probability": 0.15,
        "Rationale": "Controlled inflation and stable economic growth lead to a gradual bear steepening, but consumer resilience limits extreme impacts on funding.",
        "ImpactChannels": "Rates (20 bps increase), Curve (bear steepener), Credit OAS (15 bps IG, 45 bps HY)",
        "Shocks": {"move": 120, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $1bn T-bills via repo", "Engage in interest rate hedging strategies"],
        "Assumptions": "Inflation stabilizes; economic growth remains consistent; credit quality holds firm."
    },
    {
        "Scenario": "Regulatory Shock from Basel Endgame",
        "Description": "Tighter capital requirements from Basel reforms increase G-SIB surcharges, impacting capital ratios.",
        "Probability": 0.20,
        "Rationale": "Ongoing discussions on regulatory reforms suggest an increased likelihood of stricter liquidity requirements.",
        "ImpactChannels": "Regulatory changes (increased capital requirements)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Increase liquidity reserves by $1bn", "Proactively engage with regulators to influence outcomes"],
        "Assumptions": "Regulatory environment changes rapidly; market adapts efficiently to new requirements."
    },
    {
        "Scenario": "Deposit Runoff from Wealth Segment",
        "Description": "Rising interest rates lead to a 5% runoff in wealth management deposits as clients seek higher yields.",
        "Probability": 0.10,
        "Rationale": "Higher-yielding investment alternatives may attract deposits, but BoA's diverse offerings help retain clients.",
        "ImpactChannels": "Deposits (5% runoff)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Enhance product offerings to retain clients", "Increase wholesale funding by $500mn"],
        "Assumptions": "Interest rates rise but remain within manageable limits; client loyalty remains strong."
    },
    {
        "Scenario": "MBS Market Dislocation",
        "Description": "MBS basis widens by 35 bps due to increased supply and reduced refinancing activity.",
        "Probability": 0.15,
        "Rationale": "Market dislocations may affect MBS valuations, but BoA's active management can mitigate negative impacts.",
        "ImpactChannels": "MBS basis (35 bps widening)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -6, "NSFR": -2},
        "TradeList": ["Reduce MBS holdings by $500mn", "Reallocate funds to T-bills to optimize portfolio"],
        "Assumptions": "Increased Treasury issuance; mortgage rates remain elevated but stable."
    },
    {
        "Scenario": "Commodity Price Shock",
        "Description": "Commodity prices rise 20% due to geopolitical tensions, leading to increased credit spreads.",
        "Probability": 0.10,
        "Rationale": "Rising commodity prices could trigger liquidity concerns, but BoA's credit risk management strategies are robust.",
        "ImpactChannels": "Credit OAS (20% increase in commodity-linked spreads)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -7, "NSFR": -3},
        "TradeList": ["Increase credit risk provisions by $500mn", "Monitor commodity-linked exposures closely and adjust accordingly"],
        "Assumptions": "Geopolitical tensions escalate; commodity market volatility remains high."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Spreads",
        "Description": "Interest rates rise with a bear steepening of the yield curve; IG credit spreads widen by 15 bps and HY spreads by 45 bps.",
        "Probability": 0.15,
        "Rationale": "Controlled inflation and stable economic growth lead to a gradual bear steepening, but consumer resilience limits extreme impacts on funding.",
        "ImpactChannels": "Rates (20 bps increase), Curve (bear steepener), Credit OAS (15 bps IG, 45 bps HY)",
        "Shocks": {"move": 120, "ig_oas": 15, "hy_oas": 45},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Add $1bn T-bills via repo", "Engage in interest rate hedging strategies"],
        "Assumptions": "Inflation stabilizes; economic growth remains consistent; credit quality holds firm."
    },
    {
        "Scenario": "Regulatory Shock from Basel Endgame",
        "Description": "Tighter capital requirements from Basel reforms increase G-SIB surcharges, impacting capital ratios.",
        "Probability": 0.20,
        "Rationale": "Ongoing discussions on regulatory reforms suggest an increased likelihood of stricter liquidity requirements.",
        "ImpactChannels": "Regulatory changes (increased capital requirements)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -10, "NSFR": -5},
        "TradeList": ["Increase liquidity reserves by $1bn", "Proactively engage with regulators to influence outcomes"],
        "Assumptions": "Regulatory environment changes rapidly; market adapts efficiently to new requirements."
    },
    {
        "Scenario": "Deposit Runoff from Wealth Segment",
        "Description": "Rising interest rates lead to a 5% runoff in wealth management deposits as clients seek higher yields.",
        "Probability": 0.10,
        "Rationale": "Higher-yielding investment alternatives may attract deposits, but BoA's diverse offerings help retain clients.",
        "ImpactChannels": "Deposits (5% runoff)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -8, "NSFR": -4},
        "TradeList": ["Enhance product offerings to retain clients", "Increase wholesale funding by $500mn"],
        "Assumptions": "Interest rates rise but remain within manageable limits; client loyalty remains strong."
    },
    {
        "Scenario": "MBS Market Dislocation",
        "Description": "MBS basis widens by 35 bps due to increased supply and reduced refinancing activity.",
        "Probability": 0.15,
        "Rationale": "Market dislocations may affect MBS valuations, but BoA's active management can mitigate negative impacts.",
        "ImpactChannels": "MBS basis (35 bps widening)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -6, "NSFR": -2},
        "TradeList": ["Reduce MBS holdings by $500mn", "Reallocate funds to T-bills to optimize portfolio"],
        "Assumptions": "Increased Treasury issuance; mortgage rates remain elevated but stable."
    },
    {
        "Scenario": "Commodity Price Shock",
        "Description": "Commodity prices rise 20% due to geopolitical tensions, leading to increased credit spreads.",
        "Probability": 0.10,
        "Rationale": "Rising commodity prices could trigger liquidity concerns, but BoA's credit risk management strategies are robust.",
        "ImpactChannels": "Credit OAS (20% increase in commodity-linked spreads)",
        "Shocks": {},
        "MetricsDelta": {"LCR": -7, "NSFR": -3},
        "TradeList": ["Increase credit risk provisions by $500mn", "Monitor commodity-linked exposures closely and adjust accordingly"],
        "Assumptions": "Geopolitical tensions escalate; commodity market volatility remains high."
    }
]
```

