# Debate Transcript — Run 2

### **JUDGE** (Judge)

**JSON**

```json
[
  {
    "Scenario": "Bear Steepening with Rising Credit Spreads",
    "Description": "Short-term rates rise by 50 bps while long-term rates rise by 15 bps, widening IG OAS by 15 bps and HY OAS by 45 bps.",
    "Probability": 0.20,
    "Rationale": "Inflationary pressures force the Fed to raise rates, leading to risk aversion and wider credit spreads.",
    "ImpactChannels": "Rates (50 bps), Credit OAS (IG +15, HY +45)",
    "Shocks": "yield_curve: bear_steepener, credit_spreads: { ig_oas: +15, hy_oas: +45 }",
    "MetricsDelta": "LCR -3%, NSFR -2%",
    "TradeList": ["Add $1bn UST via repo", "Reduce $500mm Level 2 assets"],
    "Assumptions": "Stable consumer balance sheets, heightened risk aversion."
  },
  {
    "Scenario": "Regulatory Changes with Increased TLAC Requirements",
    "Description": "Implementation of Basel Endgame increases TLAC requirements by 50 bps, impacting capital ratios.",
    "Probability": 0.15,
    "Rationale": "Regulatory changes could pressure capital and liquidity metrics, necessitating adjustments to funding strategies.",
    "ImpactChannels": "Reg changes (TLAC +50 bps)",
    "Shocks": "regulatory: Basel Endgame TLAC increase",
    "MetricsDelta": "Capital ratio -25 bps, LCR -2%",
    "TradeList": ["Issue $1bn TLAC-eligible debt", "Increase secured funding by $500mm"],
    "Assumptions": "Regulatory environment remains fluid; no immediate market disruption."
  },
  {
    "Scenario": "Increased Depositor Runoff in Wealth Segment",
    "Description": "Retail beta rises, causing a 5% runoff in wealth deposits, impacting liquidity metrics.",
    "Probability": 0.13,
    "Rationale": "A more attractive market for alternatives could lead to outflows from retail deposits, straining liquidity.",
    "ImpactChannels": "Deposits runoff (5%)",
    "Shocks": "deposits: -5%",
    "MetricsDelta": "LCR -4%, NSFR -3%",
    "TradeList": ["Sell $750mm of Level 2 assets", "Increase repo financing by $500mm"],
    "Assumptions": "Consumer sentiment shifts towards higher-yielding investments."
  },
  {
    "Scenario": "MBS Basis Widening",
    "Description": "MBS basis widens by 35 bps due to increased supply from Fed tapering.",
    "Probability": 0.12,
    "Rationale": "Higher MBS supply could reduce the valuation of MBS, impacting Level 2a assets.",
    "ImpactChannels": "MBS basis (35 bps)",
    "Shocks": "mbs_basis: +35",
    "MetricsDelta": "OCI -2%, LCR -1%",
    "TradeList": ["Reduce MBS holdings by $500mm", "Increase repo transactions in MBS by $250mm"],
    "Assumptions": "Market adjusts to increased MBS supply with limited investor appetite."
  },
  {
    "Scenario": "Commodities Price Surge and Geopolitical Tensions",
    "Description": "Surge in commodity prices causes a 25 bps rise in long-term yields and a flattening of the yield curve.",
    "Probability": 0.13,
    "Rationale": "Geopolitical tensions could lead to inflationary pressures, impacting deposit costs and net interest income.",
    "ImpactChannels": "Rates (25 bps), Curve (flattening)",
    "Shocks": "move: 25",
    "MetricsDelta": "NII -3%, LCR -2%",
    "TradeList": ["Increase holdings in inflation-linked bonds by $500mm", "Adjust asset mix to prioritize liquidity"],
    "Assumptions": "Geopolitical tensions remain elevated; consumer price index increases."
  },
  {
    "Scenario": "Controlled Inflation with Gradual Easing",
    "Description": "Inflation stabilizes around 2.5%, allowing the Fed to ease rates gradually, benefiting borrowers and consumers.",
    "Probability": 0.15,
    "Rationale": "Consumer spending remains robust, supporting economic growth and maintaining a stable lending environment.",
    "ImpactChannels": "Inflation (2.5%), Fed Rates (easing by 25 bps)",
    "Shocks": "inflation: 2.5%, fed_rate: -25 bps",
    "MetricsDelta": "NII +5%, LCR +3%",
    "TradeList": ["Increase loan book by $1bn", "Add $500mm Agency MBS"],
    "Assumptions": "Consumer confidence remains high; labor market continues to strengthen."
  },
  {
    "Scenario": "Diversified Funding Stack Stabilizes Liquidity",
    "Description": "Increased reliance on diversified funding sources mitigates risks from potential deposit runoff.",
    "Probability": 0.12,
    "Rationale": "Bank of America maintains a strong mix of retail deposits and wholesale funding, ensuring liquidity.",
    "ImpactChannels": "Deposits stability (flat), wholesale funding (increased by 10%)",
    "Shocks": "deposits: stable, wholesale_funding: +10%",
    "MetricsDelta": "LCR +4%, NSFR +3%",
    "TradeList": ["Increase secured funding by $1bn", "Issue $750mm in senior unsecured debt"],
    "Assumptions": "Market conditions remain favorable for funding; investor sentiment is stable."
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
    "Description": "Short-term rates rise by 50 bps while long-term rates rise by 15 bps, widening IG OAS by 15 bps and HY OAS by 45 bps.",
    "Probability": 0.25,
    "Rationale": "Inflationary pressures force the Fed to raise rates, leading to risk aversion and wider credit spreads.",
    "ImpactChannels": "Rates (50 bps), Credit OAS (IG +15, HY +45)",
    "Shocks": "yield_curve: bear_steepener, credit_spreads: { ig_oas: +15, hy_oas: +45 }",
    "MetricsDelta": "LCR -3%, NSFR -2%",
    "TradeList": ["Add $1bn UST via repo", "Reduce $500mm Level 2 assets"],
    "Assumptions": "Stable consumer balance sheets, heightened risk aversion."
  },
  {
    "Scenario": "Regulatory Changes with Increased TLAC Requirements",
    "Description": "Implementation of Basel Endgame increases TLAC requirements by 50 bps, impacting capital ratios.",
    "Probability": 0.20,
    "Rationale": "Regulatory changes could pressure capital and liquidity metrics, necessitating adjustments to funding strategies.",
    "ImpactChannels": "Reg changes (TLAC +50 bps)",
    "Shocks": "regulatory: Basel Endgame TLAC increase",
    "MetricsDelta": "Capital ratio -25 bps, LCR -2%",
    "TradeList": ["Issue $1bn TLAC-eligible debt", "Increase secured funding by $500mm"],
    "Assumptions": "Regulatory environment remains fluid; no immediate market disruption."
  },
  {
    "Scenario": "Increased Depositor Runoff in Wealth Segment",
    "Description": "Retail beta rises, causing a 5% runoff in wealth deposits, impacting liquidity metrics.",
    "Probability": 0.15,
    "Rationale": "A more attractive market for alternatives could lead to outflows from retail deposits, straining liquidity.",
    "ImpactChannels": "Deposits runoff (5%)",
    "Shocks": "deposits: -5%",
    "MetricsDelta": "LCR -4%, NSFR -3%",
    "TradeList": ["Sell $750mm of Level 2 assets", "Increase repo financing by $500mm"],
    "Assumptions": "Consumer sentiment shifts towards higher-yielding investments."
  },
  {
    "Scenario": "MBS Basis Widening",
    "Description": "MBS basis widens by 35 bps due to increased supply from Fed tapering.",
    "Probability": 0.20,
    "Rationale": "Higher MBS supply could reduce the valuation of MBS, impacting Level 2a assets.",
    "ImpactChannels": "MBS basis (35 bps)",
    "Shocks": "mbs_basis: +35",
    "MetricsDelta": "OCI -2%, LCR -1%",
    "TradeList": ["Reduce MBS holdings by $500mm", "Increase repo transactions in MBS by $250mm"],
    "Assumptions": "Market adjusts to increased MBS supply with limited investor appetite."
  },
  {
    "Scenario": "Commodities Price Surge and Geopolitical Tensions",
    "Description": "Surge in commodity prices causes a 25 bps rise in long-term yields and a flattening of the yield curve.",
    "Probability": 0.20,
    "Rationale": "Geopolitical tensions could lead to inflationary pressures, impacting deposit costs and net interest income.",
    "ImpactChannels": "Rates (25 bps), Curve (flattening)",
    "Shocks": "move: 25",
    "MetricsDelta": "NII -3%, LCR -2%",
    "TradeList": ["Increase holdings in inflation-linked bonds by $500mm", "Adjust asset mix to prioritize liquidity"],
    "Assumptions": "Geopolitical tensions remain elevated; consumer price index increases."
  }
]
```

### **Devil's advocate**

**JSON**

```json
[
  {
    "Scenario": "Controlled Inflation with Gradual Easing",
    "Description": "Inflation stabilizes around 2.5%, allowing the Fed to ease rates gradually, benefiting borrowers and consumers.",
    "Probability": 0.30,
    "Rationale": "Consumer spending remains robust, supporting economic growth and maintaining a stable lending environment.",
    "ImpactChannels": "Inflation (2.5%), Fed Rates (easing by 25 bps)",
    "Shocks": "inflation: 2.5%, fed_rate: -25 bps",
    "MetricsDelta": "NII +5%, LCR +3%",
    "TradeList": ["Increase loan book by $1bn", "Add $500mm Agency MBS"],
    "Assumptions": "Consumer confidence remains high; labor market continues to strengthen."
  },
  {
    "Scenario": "Diversified Funding Stack Stabilizes Liquidity",
    "Description": "Increased reliance on diversified funding sources mitigates risks from potential deposit runoff.",
    "Probability": 0.25,
    "Rationale": "Bank of America maintains a strong mix of retail deposits and wholesale funding, ensuring liquidity.",
    "ImpactChannels": "Deposits stability (flat), wholesale funding (increased by 10%)",
    "Shocks": "deposits: stable, wholesale_funding: +10%",
    "MetricsDelta": "LCR +4%, NSFR +3%",
    "TradeList": ["Increase secured funding by $1bn", "Issue $750mm in senior unsecured debt"],
    "Assumptions": "Market conditions remain favorable for funding; investor sentiment is stable."
  },
  {
    "Scenario": "Positive Convexity from MBS Demand",
    "Description": "Strong demand for MBS as rates rise leads to reduced basis widening effects, supporting asset valuations.",
    "Probability": 0.20,
    "Rationale": "The Fed's tapering could create buying opportunities for MBS, stabilizing the basis.",
    "ImpactChannels": "MBS basis (narrowing by 20 bps)",
    "Shocks": "mbs_basis: -20",
    "MetricsDelta": "OCI +2%, LCR +2%",
    "TradeList": ["Increase MBS holdings by $500mm", "Adjust portfolio to include more duration"],
    "Assumptions": "Investors seek MBS as safe havens amidst volatility."
  },
  {
    "Scenario": "Curve Bull-Steepener Provides Funding Opportunities",
    "Description": "A bull-steepening of the yield curve leads to lower short-term funding costs and enhances lending margins.",
    "Probability": 0.25,
    "Rationale": "Lower short-term rates support borrowing, while steepening allows for better asset-liability management.",
    "ImpactChannels": "Short-term rates (down 30 bps), long-term rates (up 10 bps)",
    "Shocks": "short_rate: -30 bps, long_rate: +10 bps",
    "MetricsDelta": "NII +6%, LCR +3%",
    "TradeList": ["Rebalance asset mix towards longer-duration bonds", "Reduce reliance on short-term wholesale funding"],
    "Assumptions": "Economic outlook stabilizes; Fed remains accommodative."
  }
]
```

