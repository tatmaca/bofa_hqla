# Debate Transcript — Run 4

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening & Rising Credit Spreads",
        "Description": "A bear steepening of the yield curve occurs alongside a widening of credit spreads, leading to lower valuations of longer-duration assets.",
        "Probability": 0.18,
        "Rationale": "Current inflation expectations could lead to a steeper curve and wider credit spreads, impacting BoA's longer-duration HQLA.",
        "ImpactChannels": ["Rates (bps)", "Credit OAS (bps)"],
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3, "OCI": -200},
        "TradeList": ["Reduce $2bn in agency MBS", "Add $1bn in USTs via repo"],
        "Assumptions": "Inflation remains elevated; market volatility increases."
    },
    {
        "Scenario": "Deposit Runoff & Increased Funding Costs",
        "Description": "A 5% runoff in retail deposits occurs as deposit betas rise, leading to increased funding costs.",
        "Probability": 0.16,
        "Rationale": "As interest rates rise, competitive pressures may lead to increased deposit betas, causing runoff.",
        "ImpactChannels": ["Deposits (%)", "Funding Costs (%)"],
        "Shocks": {"deposits": -5, "wholesale_spreads": 25},
        "MetricsDelta": {"LCR": -8, "NSFR": -4, "NII": -150},
        "TradeList": ["Issue $3bn in term debt", "Increase repo funding by $1bn"],
        "Assumptions": "Competitive landscape shifts; rates rise."
    },
    {
        "Scenario": "Widening Credit Spreads and Risk Aversion",
        "Description": "Credit spreads widen by 50 bps due to increased risk aversion in the market, negatively impacting bond valuations.",
        "Probability": 0.13,
        "Rationale": "Market uncertainty leads to a flight to quality, increasing spreads for lower-rated assets and impacting HQLA valuations.",
        "ImpactChannels": ["Credit Spreads (bps)", "Bond Valuations"],
        "Shocks": {"credit_spreads": 50},
        "MetricsDelta": {"LCR": -5, "NSFR": -4, "OCI": -300},
        "TradeList": ["Sell $2bn in lower-rated bonds", "Increase UST holdings by $1bn"],
        "Assumptions": "Market volatility increases; investor risk appetite decreases."
    },
    {
        "Scenario": "Regulatory Changes Leading to Increased Capital Requirements",
        "Description": "Unexpected regulatory changes increase capital requirements by 50 bps, impacting operational flexibility.",
        "Probability": 0.13,
        "Rationale": "Regulatory bodies may impose stricter capital requirements in response to perceived systemic risks.",
        "ImpactChannels": ["Regulatory Capital Ratios (%)"],
        "Shocks": {"capital_requirements": 50},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Reallocate $2bn from equities to HQLA", "Adjust dividend payouts"],
        "Assumptions": "Regulatory environment tightens unexpectedly; market confidence wanes."
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "The MBS basis widens by 50 bps due to rising mortgage rates, impacting the valuation of agency MBS.",
        "Probability": 0.12,
        "Rationale": "Increased mortgage rates and reduced refinancing activity could lead to a wider MBS basis.",
        "ImpactChannels": ["MBS basis (bps)"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -6, "OCI": -250},
        "TradeList": ["Sell $1bn in underperforming MBS", "Purchase $500mn in cash equivalents"],
        "Assumptions": "Mortgage rates rise; housing market cools."
    },
    {
        "Scenario": "Resilient Growth & Controlled Inflation",
        "Description": "Economic growth continues at a steady pace with inflation remaining in check, supporting consumer and SME spending.",
        "Probability": 0.15,
        "Rationale": "Controlled inflation and a resilient labor market create a favorable environment for lending and investment.",
        "ImpactChannels": ["Consumer Spending Growth (%)", "Inflation Rate (%)"],
        "Shocks": {"gdp_growth": 2.5, "inflation": 2.0},
        "MetricsDelta": {"LCR": +5, "NSFR": +4, "NII": +200},
        "TradeList": ["Increase lending portfolio by $3bn", "Add $1bn in agency MBS"],
        "Assumptions": "Stable economic conditions; no major geopolitical disruptions."
    },
    {
        "Scenario": "Geopolitical Tensions Leading to Flight to Quality",
        "Description": "Increased geopolitical tensions lead to a flight to quality, decreasing credit spreads and increasing UST demand.",
        "Probability": 0.13,
        "Rationale": "Historical patterns suggest that geopolitical tensions often result in a flight to safety, benefiting USTs.",
        "ImpactChannels": ["Credit OAS (bps)", "Rates (bps)"],
        "Shocks": {"credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +5, "NSFR": +3, "NII": -100},
        "TradeList": ["Increase UST holdings by $2bn", "Reduce risk-weighted assets by $1bn"],
        "Assumptions": "Geopolitical situation escalates; market participants flee to quality."
    }
]
```

## Round 1

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepening & Rising Credit Spreads",
        "Description": "A bear steepening of the yield curve occurs alongside a widening of credit spreads, leading to lower valuations of longer-duration assets.",
        "Probability": 0.25,
        "Rationale": "Current inflation expectations could lead to a steeper curve and wider credit spreads, impacting BoA's longer-duration HQLA.",
        "ImpactChannels": ["Rates (bps)", "Credit OAS (bps)"],
        "Shocks": {"move_index": 120, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -5, "NSFR": -3, "OCI": -200},
        "TradeList": ["Reduce $2bn in agency MBS", "Add $1bn in USTs via repo"],
        "Assumptions": "Inflation remains elevated; market volatility increases."
    },
    {
        "Scenario": "Deposit Runoff & Increased Funding Costs",
        "Description": "A 5% runoff in retail deposits occurs as deposit betas rise, leading to increased funding costs.",
        "Probability": 0.20,
        "Rationale": "As interest rates rise, competitive pressures may lead to increased deposit betas, causing runoff.",
        "ImpactChannels": ["Deposits (%)", "Funding Costs (%)"],
        "Shocks": {"deposits": -5, "wholesale_spreads": 25},
        "MetricsDelta": {"LCR": -8, "NSFR": -4, "NII": -150},
        "TradeList": ["Issue $3bn in term debt", "Increase repo funding by $1bn"],
        "Assumptions": "Competitive landscape shifts; rates rise."
    },
    {
        "Scenario": "Regulatory Headwinds and TLAC Adjustments",
        "Description": "Stricter capital requirements increase TLAC by 50 bps, impacting capital ratios and asset allocation.",
        "Probability": 0.15,
        "Rationale": "Ongoing discussions around Basel Endgame indicate potential for increased regulatory burden.",
        "ImpactChannels": ["Reg changes", "Capital Ratios"],
        "Shocks": {"TLAC": 50},
        "MetricsDelta": {"LCR": -4, "NSFR": -2},
        "TradeList": ["Reallocate $2bn from equities to HQLA", "Reduce dividend payouts"],
        "Assumptions": "Regulatory environment tightens; capital markets remain stable."
    },
    {
        "Scenario": "MBS Basis Widening",
        "Description": "The MBS basis widens by 50 bps due to rising mortgage rates, impacting the valuation of agency MBS.",
        "Probability": 0.20,
        "Rationale": "Increased mortgage rates and reduced refinancing activity could lead to a wider MBS basis.",
        "ImpactChannels": ["MBS basis (bps)"],
        "Shocks": {"mbs_basis": 50},
        "MetricsDelta": {"LCR": -6, "OCI": -250},
        "TradeList": ["Sell $1bn in underperforming MBS", "Purchase $500mn in cash equivalents"],
        "Assumptions": "Mortgage rates rise; housing market cools."
    },
    {
        "Scenario": "Geopolitical Tensions Leading to Flight to Quality",
        "Description": "Increased geopolitical tensions lead to a flight to quality, decreasing credit spreads and increasing UST demand.",
        "Probability": 0.20,
        "Rationale": "Historical patterns suggest that geopolitical tensions often result in a flight to safety, benefiting USTs.",
        "ImpactChannels": ["Credit OAS (bps)", "Rates (bps)"],
        "Shocks": {"credit_spreads": {"ig_oas": -20, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +5, "NSFR": +3, "NII": -100},
        "TradeList": ["Increase UST holdings by $2bn", "Reduce risk-weighted assets by $1bn"],
        "Assumptions": "Geopolitical situation escalates; market participants flee to quality."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Resilient Growth & Controlled Inflation",
        "Description": "Economic growth continues at a steady pace with inflation remaining in check, supporting consumer and SME spending.",
        "Probability": 0.30,
        "Rationale": "Controlled inflation and a resilient labor market create a favorable environment for lending and investment.",
        "ImpactChannels": ["Consumer Spending Growth (%)", "Inflation Rate (%)"],
        "Shocks": {"gdp_growth": 2.5, "inflation": 2.0},
        "MetricsDelta": {"LCR": +5, "NSFR": +4, "NII": +200},
        "TradeList": ["Increase lending portfolio by $3bn", "Add $1bn in agency MBS"],
        "Assumptions": "Stable economic conditions; no major geopolitical disruptions."
    },
    {
        "Scenario": "Stable Deposit Base & Competitive Environment",
        "Description": "Bank of America maintains its competitive edge, leading to stable deposit growth despite rising interest rates.",
        "Probability": 0.25,
        "Rationale": "Strong customer relationships and innovative product offerings help retain deposits even in a rising rate environment.",
        "ImpactChannels": ["Deposits Growth (%)", "Funding Costs (%)"],
        "Shocks": {"deposits": +2, "funding_costs": 10},
        "MetricsDelta": {"LCR": +4, "NSFR": +3, "NII": +150},
        "TradeList": ["Launch new deposit products", "Reduce reliance on wholesale funding"],
        "Assumptions": "Customer loyalty remains high; competition does not intensify drastically."
    },
    {
        "Scenario": "Bull Steepener Benefits",
        "Description": "The yield curve steepens with long-term rates rising more than short-term rates, benefiting the bank's asset-liability management.",
        "Probability": 0.20,
        "Rationale": "A bull steepener creates opportunities for improved NII as the bank can manage its liabilities more effectively.",
        "ImpactChannels": ["Long-term Rates (bps)", "Short-term Rates (bps)"],
        "Shocks": {"long_term_rates": 50, "short_term_rates": 10},
        "MetricsDelta": {"LCR": +3, "NSFR": +2, "NII": +250},
        "TradeList": ["Extend duration of asset portfolio", "Adjust hedging strategies"],
        "Assumptions": "Economic growth drives long-term rates higher; inflation expectations stabilize."
    },
    {
        "Scenario": "MBS Rotation & Portfolio Optimization",
        "Description": "Bank of America rotates into more stable municipal and sovereign bonds, optimizing its HQLA portfolio.",
        "Probability": 0.15,
        "Rationale": "The bank can enhance its capital ratios and reduce OCI risk by diversifying into less volatile assets.",
        "ImpactChannels": ["Muni Yields (bps)", "Sovereign Yields (bps)"],
        "Shocks": {"muni_yields": -30, "sovereign_yields": -20},
        "MetricsDelta": {"LCR": +6, "OCI": +150},
        "TradeList": ["Purchase $2bn in munis", "Sell $1bn in volatile assets"],
        "Assumptions": "Market conditions favor municipal and sovereign bonds; interest rates remain stable."
    },
    {
        "Scenario": "Regulatory Relief & Capital Efficiency",
        "Description": "Potential regulatory adjustments provide relief on capital requirements, enhancing the bank's operational flexibility.",
        "Probability": 0.10,
        "Rationale": "Regulatory bodies may recognize the need for more favorable capital treatment in light of economic conditions.",
        "ImpactChannels": ["Capital Ratios (%)", "TLAC Requirements (bps)"],
        "Shocks": {"TLAC": -50},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Reallocate $2bn into growth-oriented assets", "Enhance capital efficiency strategies"],
        "Assumptions": "Regulatory environment shifts positively; economic stability is maintained."
    }
]
```

## Round 2

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Resilient Growth & Controlled Inflation",
        "Description": "Economic growth continues at a steady pace with inflation remaining in check, supporting consumer and SME spending.",
        "Probability": 0.20,
        "Rationale": "Controlled inflation and a resilient labor market create a favorable environment for lending and investment.",
        "ImpactChannels": ["Consumer Spending Growth (%)", "Inflation Rate (%)"],
        "Shocks": {"gdp_growth": 2.5, "inflation": 2.0},
        "MetricsDelta": {"LCR": +5, "NSFR": +4, "NII": +200},
        "TradeList": ["Increase lending portfolio by $3bn", "Add $1bn in agency MBS"],
        "Assumptions": "Stable economic conditions; no major geopolitical disruptions."
    },
    {
        "Scenario": "Stable Deposit Base & Competitive Environment",
        "Description": "Bank of America maintains its competitive edge, leading to stable deposit growth despite rising interest rates.",
        "Probability": 0.15,
        "Rationale": "Strong customer relationships and innovative product offerings help retain deposits even in a rising rate environment.",
        "ImpactChannels": ["Deposits Growth (%)", "Funding Costs (%)"],
        "Shocks": {"deposits": +2, "funding_costs": 10},
        "MetricsDelta": {"LCR": +4, "NSFR": +3, "NII": +150},
        "TradeList": ["Launch new deposit products", "Reduce reliance on wholesale funding"],
        "Assumptions": "Customer loyalty remains high; competition does not intensify drastically."
    },
    {
        "Scenario": "Bull Steepener Benefits",
        "Description": "The yield curve steepens with long-term rates rising more than short-term rates, benefiting the bank's asset-liability management.",
        "Probability": 0.20,
        "Rationale": "A bull steepener creates opportunities for improved NII as the bank can manage its liabilities more effectively.",
        "ImpactChannels": ["Long-term Rates (bps)", "Short-term Rates (bps)"],
        "Shocks": {"long_term_rates": 50, "short_term_rates": 10},
        "MetricsDelta": {"LCR": +3, "NSFR": +2, "NII": +250},
        "TradeList": ["Extend duration of asset portfolio", "Adjust hedging strategies"],
        "Assumptions": "Economic growth drives long-term rates higher; inflation expectations stabilize."
    },
    {
        "Scenario": "MBS Rotation & Portfolio Optimization",
        "Description": "Bank of America rotates into more stable municipal and sovereign bonds, optimizing its HQLA portfolio.",
        "Probability": 0.15,
        "Rationale": "The bank can enhance its capital ratios and reduce OCI risk by diversifying into less volatile assets.",
        "ImpactChannels": ["Muni Yields (bps)", "Sovereign Yields (bps)"],
        "Shocks": {"muni_yields": -30, "sovereign_yields": -20},
        "MetricsDelta": {"LCR": +6, "OCI": +150},
        "TradeList": ["Purchase $2bn in munis", "Sell $1bn in volatile assets"],
        "Assumptions": "Market conditions favor municipal and sovereign bonds; interest rates remain stable."
    },
    {
        "Scenario": "Regulatory Relief & Capital Efficiency",
        "Description": "Potential regulatory adjustments provide relief on capital requirements, enhancing the bank's operational flexibility.",
        "Probability": 0.10,
        "Rationale": "Regulatory bodies may recognize the need for more favorable capital treatment in light of economic conditions.",
        "ImpactChannels": ["Capital Ratios (%)", "TLAC Requirements (bps)"],
        "Shocks": {"TLAC": -50},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Reallocate $2bn into growth-oriented assets", "Enhance capital efficiency strategies"],
        "Assumptions": "Regulatory environment shifts positively; economic stability is maintained."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Resilient Growth & Controlled Inflation",
        "Description": "Economic growth continues at a steady pace with inflation remaining in check, supporting consumer and SME spending.",
        "Probability": 0.20,
        "Rationale": "Controlled inflation and a resilient labor market create a favorable environment for lending and investment.",
        "ImpactChannels": ["Consumer Spending Growth (%)", "Inflation Rate (%)"],
        "Shocks": {"gdp_growth": 2.5, "inflation": 2.0},
        "MetricsDelta": {"LCR": +5, "NSFR": +4, "NII": +200},
        "TradeList": ["Increase lending portfolio by $3bn", "Add $1bn in agency MBS"],
        "Assumptions": "Stable economic conditions; no major geopolitical disruptions."
    },
    {
        "Scenario": "Stable Deposit Base & Competitive Environment",
        "Description": "Bank of America maintains its competitive edge, leading to stable deposit growth despite rising interest rates.",
        "Probability": 0.15,
        "Rationale": "Strong customer relationships and innovative product offerings help retain deposits even in a rising rate environment.",
        "ImpactChannels": ["Deposits Growth (%)", "Funding Costs (%)"],
        "Shocks": {"deposits": +2, "funding_costs": 10},
        "MetricsDelta": {"LCR": +4, "NSFR": +3, "NII": +150},
        "TradeList": ["Launch new deposit products", "Reduce reliance on wholesale funding"],
        "Assumptions": "Customer loyalty remains high; competition does not intensify drastically."
    },
    {
        "Scenario": "Bull Steepener Benefits",
        "Description": "The yield curve steepens with long-term rates rising more than short-term rates, benefiting the bank's asset-liability management.",
        "Probability": 0.20,
        "Rationale": "A bull steepener creates opportunities for improved NII as the bank can manage its liabilities more effectively.",
        "ImpactChannels": ["Long-term Rates (bps)", "Short-term Rates (bps)"],
        "Shocks": {"long_term_rates": 50, "short_term_rates": 10},
        "MetricsDelta": {"LCR": +3, "NSFR": +2, "NII": +250},
        "TradeList": ["Extend duration of asset portfolio", "Adjust hedging strategies"],
        "Assumptions": "Economic growth drives long-term rates higher; inflation expectations stabilize."
    },
    {
        "Scenario": "MBS Rotation & Portfolio Optimization",
        "Description": "Bank of America rotates into more stable municipal and sovereign bonds, optimizing its HQLA portfolio.",
        "Probability": 0.15,
        "Rationale": "The bank can enhance its capital ratios and reduce OCI risk by diversifying into less volatile assets.",
        "ImpactChannels": ["Muni Yields (bps)", "Sovereign Yields (bps)"],
        "Shocks": {"muni_yields": -30, "sovereign_yields": -20},
        "MetricsDelta": {"LCR": +6, "OCI": +150},
        "TradeList": ["Purchase $2bn in munis", "Sell $1bn in volatile assets"],
        "Assumptions": "Market conditions favor municipal and sovereign bonds; interest rates remain stable."
    },
    {
        "Scenario": "Regulatory Relief & Capital Efficiency",
        "Description": "Potential regulatory adjustments provide relief on capital requirements, enhancing the bank's operational flexibility.",
        "Probability": 0.10,
        "Rationale": "Regulatory bodies may recognize the need for more favorable capital treatment in light of economic conditions.",
        "ImpactChannels": ["Capital Ratios (%)", "TLAC Requirements (bps)"],
        "Shocks": {"TLAC": -50},
        "MetricsDelta": {"LCR": +5, "NSFR": +3},
        "TradeList": ["Reallocate $2bn into growth-oriented assets", "Enhance capital efficiency strategies"],
        "Assumptions": "Regulatory environment shifts positively; economic stability is maintained."
    }
]
```

## Round 3

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Moderate Economic Growth with Inflationary Pressures",
        "Description": "Economic growth slows to 1.5% with inflation rising to 3%, impacting consumer spending and credit demand.",
        "Probability": 0.25,
        "Rationale": "Economic indicators show signs of slowing growth, and inflation remains above target, affecting lending volumes.",
        "ImpactChannels": ["GDP Growth (%)", "Inflation Rate (%)"],
        "Shocks": {"gdp_growth": 1.5, "inflation": 3.0},
        "MetricsDelta": {"LCR": -4, "NSFR": -3, "NII": -150},
        "TradeList": ["Reduce exposure to high-risk loans", "Increase cash reserves by $2bn"],
        "Assumptions": "Economic environment deteriorates; inflation persists."
    },
    {
        "Scenario": "Increased Deposit Competition and Outflows",
        "Description": "Aggressive competition results in a 5% runoff of retail deposits as customers seek higher yields elsewhere.",
        "Probability": 0.20,
        "Rationale": "The rise of fintech and alternative banking options creates significant pressure on traditional deposit bases.",
        "ImpactChannels": ["Deposit Growth (%)", "Funding Costs (%)"],
        "Shocks": {"deposits": -5, "funding_costs": 30},
        "MetricsDelta": {"LCR": -6, "NSFR": -5, "NII": -200},
        "TradeList": ["Increase term debt issuance by $3bn", "Enhance digital banking offerings"],
        "Assumptions": "Competitive landscape shifts rapidly; customer behavior changes."
    },
    {
        "Scenario": "Widening Credit Spreads and Risk Aversion",
        "Description": "Credit spreads widen by 50 bps due to increased risk aversion in the market, negatively impacting bond valuations.",
        "Probability": 0.20,
        "Rationale": "Market uncertainty leads to a flight to quality, increasing spreads for lower-rated assets and impacting HQLA valuations.",
        "ImpactChannels": ["Credit Spreads (bps)", "Bond Valuations"],
        "Shocks": {"credit_spreads": 50},
        "MetricsDelta": {"LCR": -5, "NSFR": -4, "OCI": -300},
        "TradeList": ["Sell $2bn in lower-rated bonds", "Increase UST holdings by $1bn"],
        "Assumptions": "Market volatility increases; investor risk appetite decreases."
    },
    {
        "Scenario": "Regulatory Changes Leading to Increased Capital Requirements",
        "Description": "Unexpected regulatory changes increase capital requirements by 50 bps, impacting operational flexibility.",
        "Probability": 0.20,
        "Rationale": "Regulatory bodies may impose stricter capital requirements in response to perceived systemic risks.",
        "ImpactChannels": ["Regulatory Capital Ratios (%)"],
        "Shocks": {"capital_requirements": 50},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Reallocate $2bn from equities to HQLA", "Adjust dividend payouts"],
        "Assumptions": "Regulatory environment tightens unexpectedly; market confidence wanes."
    },
    {
        "Scenario": "Interest Rate Flattening Impact",
        "Description": "The yield curve flattens unexpectedly, leading to a compression of net interest margins and lower NII.",
        "Probability": 0.15,
        "Rationale": "Economic indicators suggest a potential shift in monetary policy that could flatten the yield curve.",
        "ImpactChannels": ["Interest Rate Levels (bps)", "NIM (%)"],
        "Shocks": {"short_term_rates": 10, "long_term_rates": -20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2, "NII": -250},
        "TradeList": ["Adjust asset-liability management strategies", "Increase focus on fee-based revenue"],
        "Assumptions": "Market conditions shift rapidly; monetary policy changes occur."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Moderate Economic Growth with Inflationary Pressures",
        "Description": "Economic growth slows to 1.5% with inflation rising to 3%, impacting consumer spending and credit demand.",
        "Probability": 0.25,
        "Rationale": "Economic indicators show signs of slowing growth, and inflation remains above target, affecting lending volumes.",
        "ImpactChannels": ["GDP Growth (%)", "Inflation Rate (%)"],
        "Shocks": {"gdp_growth": 1.5, "inflation": 3.0},
        "MetricsDelta": {"LCR": -4, "NSFR": -3, "NII": -150},
        "TradeList": ["Reduce exposure to high-risk loans", "Increase cash reserves by $2bn"],
        "Assumptions": "Economic environment deteriorates; inflation persists."
    },
    {
        "Scenario": "Increased Deposit Competition and Outflows",
        "Description": "Aggressive competition results in a 5% runoff of retail deposits as customers seek higher yields elsewhere.",
        "Probability": 0.20,
        "Rationale": "The rise of fintech and alternative banking options creates significant pressure on traditional deposit bases.",
        "ImpactChannels": ["Deposit Growth (%)", "Funding Costs (%)"],
        "Shocks": {"deposits": -5, "funding_costs": 30},
        "MetricsDelta": {"LCR": -6, "NSFR": -5, "NII": -200},
        "TradeList": ["Increase term debt issuance by $3bn", "Enhance digital banking offerings"],
        "Assumptions": "Competitive landscape shifts rapidly; customer behavior changes."
    },
    {
        "Scenario": "Widening Credit Spreads and Risk Aversion",
        "Description": "Credit spreads widen by 50 bps due to increased risk aversion in the market, negatively impacting bond valuations.",
        "Probability": 0.20,
        "Rationale": "Market uncertainty leads to a flight to quality, increasing spreads for lower-rated assets and impacting HQLA valuations.",
        "ImpactChannels": ["Credit Spreads (bps)", "Bond Valuations"],
        "Shocks": {"credit_spreads": 50},
        "MetricsDelta": {"LCR": -5, "NSFR": -4, "OCI": -300},
        "TradeList": ["Sell $2bn in lower-rated bonds", "Increase UST holdings by $1bn"],
        "Assumptions": "Market volatility increases; investor risk appetite decreases."
    },
    {
        "Scenario": "Regulatory Changes Leading to Increased Capital Requirements",
        "Description": "Unexpected regulatory changes increase capital requirements by 50 bps, impacting operational flexibility.",
        "Probability": 0.20,
        "Rationale": "Regulatory bodies may impose stricter capital requirements in response to perceived systemic risks.",
        "ImpactChannels": ["Regulatory Capital Ratios (%)"],
        "Shocks": {"capital_requirements": 50},
        "MetricsDelta": {"LCR": -5, "NSFR": -3},
        "TradeList": ["Reallocate $2bn from equities to HQLA", "Adjust dividend payouts"],
        "Assumptions": "Regulatory environment tightens unexpectedly; market confidence wanes."
    },
    {
        "Scenario": "Interest Rate Flattening Impact",
        "Description": "The yield curve flattens unexpectedly, leading to a compression of net interest margins and lower NII.",
        "Probability": 0.15,
        "Rationale": "Economic indicators suggest a potential shift in monetary policy that could flatten the yield curve.",
        "ImpactChannels": ["Interest Rate Levels (bps)", "NIM (%)"],
        "Shocks": {"short_term_rates": 10, "long_term_rates": -20},
        "MetricsDelta": {"LCR": -3, "NSFR": -2, "NII": -250},
        "TradeList": ["Adjust asset-liability management strategies", "Increase focus on fee-based revenue"],
        "Assumptions": "Market conditions shift rapidly; monetary policy changes occur."
    }
]
```

