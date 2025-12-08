# Debate Transcript — Run 3

### **JUDGE** (Judge)

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Credit Spreads",
        "Description": "Yield curve steepens with long-term rates rising faster, increasing credit spreads significantly.",
        "Probability": 0.18,
        "Rationale": "Macroeconomic indicators suggest potential rate hikes due to persistent inflation, leading to a bear steepener scenario.",
        "ImpactChannels": ["Rates (15 bps)", "Credit OAS (IG +15 bps, HY +45 bps)"],
        "Shocks": {"move_index": 110, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -5, "NII": -2},
        "TradeList": ["Add $2bn IG corporates", "Reduce $1bn MBS exposure"],
        "Assumptions": "Inflation persists; yield curve reacts as expected; corporate credit quality remains stable."
    },
    {
        "Scenario": "Consumer Runoff Impact on Deposits",
        "Description": "A 5% runoff in consumer deposits due to inflationary pressures.",
        "Probability": 0.15,
        "Rationale": "Economic pressures are leading to reduced consumer savings, affecting deposit base.",
        "ImpactChannels": ["Deposits/runoff (5%)"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -7, "NII": -3},
        "TradeList": ["Increase short-term funding via repo by $1bn", "Adjust retail deposit rates"],
        "Assumptions": "Inflation continues to impact consumer behavior; deposit base is sensitive to economic shifts."
    },
    {
        "Scenario": "Tighter Credit Spreads with Improved Basis",
        "Description": "Credit spreads tighten, enhancing MBS and corporate bond valuations.",
        "Probability": 0.20,
        "Rationale": "Market stability and strong corporate earnings may lead to reduced spreads.",
        "ImpactChannels": ["Credit Spreads", "MBS Valuations"],
        "Shocks": {"credit_spreads": {"ig_oas": -10, "hy_oas": -25}},
        "MetricsDelta": {"LCR": +5, "NII": +4},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce corporate bond holdings by $500mn"],
        "Assumptions": "Economic fundamentals support credit quality; investor sentiment is favorable."
    },
    {
        "Scenario": "Bull Steepener Opportunities",
        "Description": "A bull steepener in the yield curve allows for effective asset repositioning.",
        "Probability": 0.12,
        "Rationale": "Market dynamics suggest a potential steepening of the curve, offering convexity benefits.",
        "ImpactChannels": ["Yield Curve", "NII Protection"],
        "Shocks": {"curve_steepening": 20},
        "MetricsDelta": {"LCR": +2, "NII": +5},
        "TradeList": ["Add $1.5bn in longer-duration securities", "Reduce reliance on short-term funding"],
        "Assumptions": "Market responds positively to Fed policy; growth outlook improves."
    },
    {
        "Scenario": "Stable Deposit Betas",
        "Description": "Deposit betas remain stable, mitigating funding costs amidst rising rates.",
        "Probability": 0.15,
        "Rationale": "Loyal customer relationships may help maintain deposit betas during rate hikes.",
        "ImpactChannels": ["Funding Costs", "Deposit Stability"],
        "Shocks": {"deposit_betas": 0.02},
        "MetricsDelta": {"LCR": +4, "NII": +3},
        "TradeList": ["Maintain competitive deposit rates", "Optimize funding mix for cost efficiency"],
        "Assumptions": "Customer loyalty persists; competitive landscape remains stable."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital ratios and funding flexibility.",
        "Probability": 0.08,
        "Rationale": "Discussions about easing regulatory burdens could benefit capital management.",
        "ImpactChannels": ["Capital Ratios", "Funding Flexibility"],
        "Shocks": {"regulatory_relief": "TLAC requirements eased"},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Reassess TLAC funding strategies", "Optimize capital structure"],
        "Assumptions": "Regulatory environment evolves favorably; market adapts."
    },
    {
        "Scenario": "Geopolitical Tensions and Flight to Quality",
        "Description": "Increased geopolitical tensions lead to a flight to quality, boosting UST demand.",
        "Probability": 0.12,
        "Rationale": "Recent geopolitical events indicate a potential shift in investor sentiment toward safer assets.",
        "ImpactChannels": ["Rates (UST yields drop by 20 bps)", "Credit spreads (compression)"],
        "Shocks": {"move_index": 90, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": +4, "NII": -2},
        "TradeList": ["Add $1bn USTs", "Reduce riskier asset holdings by $500mn"],
        "Assumptions": "Geopolitical risks remain high; investors prioritize safety over yield."
    }
]
```

## Round 1

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Bear Steepener with Rising Credit Spreads",
        "Description": "Yield curve steepens with long-term rates rising faster, increasing credit spreads significantly.",
        "Probability": 0.25,
        "Rationale": "Macroeconomic indicators suggest potential rate hikes due to persistent inflation, leading to a bear steepener scenario.",
        "ImpactChannels": ["Rates (15 bps)", "Credit OAS (IG +15 bps, HY +45 bps)"],
        "Shocks": {"move_index": 110, "yield_curve": "bear_steepener", "credit_spreads": {"ig_oas": 15, "hy_oas": 45}},
        "MetricsDelta": {"LCR": -5, "NII": -2},
        "TradeList": ["Add $2bn IG corporates", "Reduce $1bn MBS exposure"],
        "Assumptions": "Inflation persists; yield curve reacts as expected; corporate credit quality remains stable."
    },
    {
        "Scenario": "Regulatory Changes Drive Increased TLAC Requirements",
        "Description": "New TLAC requirements increase funding costs, impacting NII and liquidity metrics.",
        "Probability": 0.15,
        "Rationale": "Recent regulatory discussions hint at increased TLAC mandates, affecting funding strategies.",
        "ImpactChannels": ["Reg changes", "Wholesale spreads"],
        "Shocks": {"regulatory": "New TLAC requirements increase funding costs by 20 bps"},
        "MetricsDelta": {"LCR": -3, "NII": -4},
        "TradeList": ["Increase $1bn in long-term debt issuance", "Adjust wholesale funding mix to minimize costs"],
        "Assumptions": "Regulatory environment remains fluid; market reacts to new requirements."
    },
    {
        "Scenario": "Consumer Runoff Impact on Deposits",
        "Description": "A 5% runoff in consumer deposits due to inflationary pressures.",
        "Probability": 0.20,
        "Rationale": "Economic pressures are leading to reduced consumer savings, affecting deposit base.",
        "ImpactChannels": ["Deposits/runoff (5%)"],
        "Shocks": {"deposits": -5},
        "MetricsDelta": {"LCR": -7, "NII": -3},
        "TradeList": ["Increase short-term funding via repo by $1bn", "Adjust retail deposit rates"],
        "Assumptions": "Inflation continues to impact consumer behavior; deposit base is sensitive to economic shifts."
    },
    {
        "Scenario": "Stabilization of Credit Markets",
        "Description": "Credit spreads tighten as economic conditions stabilize, improving market sentiment.",
        "Probability": 0.25,
        "Rationale": "Improving earnings outlooks from corporates suggest a stabilization in credit markets.",
        "ImpactChannels": ["Credit OAS (IG -10 bps, HY -30 bps)", "MBS basis (tightening)"],
        "Shocks": {"credit_spreads": {"ig_oas": -10, "hy_oas": -30}},
        "MetricsDelta": {"LCR": +3, "NII": +5},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce corporate bond exposure by $500mn"],
        "Assumptions": "Economic recovery continues; corporate earnings show resilience."
    },
    {
        "Scenario": "Geopolitical Tensions and Flight to Quality",
        "Description": "Increased geopolitical tensions lead to a flight to quality, boosting UST demand.",
        "Probability": 0.15,
        "Rationale": "Recent geopolitical events indicate a potential shift in investor sentiment toward safer assets.",
        "ImpactChannels": ["Rates (UST yields drop by 20 bps)", "Credit spreads (compression)"],
        "Shocks": {"move_index": 90, "credit_spreads": {"ig_oas": -5, "hy_oas": -10}},
        "MetricsDelta": {"LCR": +4, "NII": -2},
        "TradeList": ["Add $1bn USTs", "Reduce riskier asset holdings by $500mn"],
        "Assumptions": "Geopolitical risks remain high; investors prioritize safety over yield."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation and Resilient Consumers",
        "Description": "Inflation remains controlled while consumers continue to spend, supporting economic growth.",
        "Probability": 0.30,
        "Rationale": "Current indicators suggest consumer spending is strong, leading to sustained economic activity.",
        "ImpactChannels": ["Consumer Spending", "SME Resilience"],
        "Shocks": {"inflation": 2, "consumer_spending": 5},
        "MetricsDelta": {"LCR": +4, "NII": +3},
        "TradeList": ["Increase exposure to consumer credit products by $1bn", "Add $500mn in SME loans"],
        "Assumptions": "Inflation stabilizes; consumer confidence remains high."
    },
    {
        "Scenario": "Stable Deposit Betas",
        "Description": "Deposit betas remain stable, allowing for controlled funding costs amidst rising rates.",
        "Probability": 0.25,
        "Rationale": "A strong customer relationship and brand loyalty can maintain deposit betas during rate hikes.",
        "ImpactChannels": ["Funding Costs", "Deposit Stability"],
        "Shocks": {"deposit_betas": 0.05},
        "MetricsDelta": {"LCR": +3, "NII": +5},
        "TradeList": ["Maintain competitive deposit rates", "Rotate into longer-term funding sources"],
        "Assumptions": "Customer loyalty persists; competitive landscape remains stable."
    },
    {
        "Scenario": "Tighter Credit Spreads with Improved Basis",
        "Description": "Credit spreads tighten, improving the basis for MBS and corporate bonds.",
        "Probability": 0.20,
        "Rationale": "Market stability and strong corporate earnings could lead to a reduction in spreads.",
        "ImpactChannels": ["Credit Spreads", "MBS Valuations"],
        "Shocks": {"credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +5, "NII": +4},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce corporate bond holdings by $500mn"],
        "Assumptions": "Economic fundamentals support credit quality; investor sentiment remains positive."
    },
    {
        "Scenario": "Bull Steepener Benefits",
        "Description": "A bull steepener in the yield curve allows for profitable repositioning of assets.",
        "Probability": 0.15,
        "Rationale": "Market dynamics suggest a potential steepening of the curve, enhancing convexity benefits.",
        "ImpactChannels": ["Yield Curve", "NII Protection"],
        "Shocks": {"curve_steepening": 20},
        "MetricsDelta": {"LCR": +2, "NII": +6},
        "TradeList": ["Add $1bn in longer-duration securities", "Reduce short-term funding exposure"],
        "Assumptions": "Market responds positively to Fed policy; growth outlook improves."
    },
    {
        "Scenario": "Regulatory Relief",
        "Description": "Potential regulatory relief enhances capital ratios and funding flexibility.",
        "Probability": 0.10,
        "Rationale": "Ongoing discussions about easing regulatory burdens could benefit capital management.",
        "ImpactChannels": ["Capital Ratios", "Funding Flexibility"],
        "Shocks": {"regulatory_relief": "TLAC requirements eased"},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Reassess TLAC funding strategies", "Optimize capital structure"],
        "Assumptions": "Regulatory environment evolves favorably; market adapts."
    }
]
```

## Round 2

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation and Resilient Consumers",
        "Description": "Inflation remains controlled while consumers continue to spend, supporting economic growth.",
        "Probability": 0.20,
        "Rationale": "Current indicators suggest moderate consumer spending, but inflationary pressures could dampen growth.",
        "ImpactChannels": ["Consumer Spending", "SME Resilience"],
        "Shocks": {"inflation": 2, "consumer_spending": 3},
        "MetricsDelta": {"LCR": +2, "NII": +1},
        "TradeList": ["Increase exposure to consumer credit products by $500mn", "Add $250mn in SME loans"],
        "Assumptions": "Inflation stabilizes; consumer confidence is mixed."
    },
    {
        "Scenario": "Stable Deposit Betas",
        "Description": "Deposit betas remain stable, allowing for controlled funding costs amidst rising rates.",
        "Probability": 0.15,
        "Rationale": "Customer loyalty could maintain deposit betas, but competition may drive up costs.",
        "ImpactChannels": ["Funding Costs", "Deposit Stability"],
        "Shocks": {"deposit_betas": 0.03},
        "MetricsDelta": {"LCR": +1, "NII": +2},
        "TradeList": ["Maintain competitive deposit rates", "Rotate into longer-term funding sources"],
        "Assumptions": "Customer loyalty persists; competitive landscape remains stable."
    },
    {
        "Scenario": "Tighter Credit Spreads with Improved Basis",
        "Description": "Credit spreads tighten, improving the basis for MBS and corporate bonds.",
        "Probability": 0.20,
        "Rationale": "Market stability and strong corporate earnings may lead to a reduction in spreads, but volatility remains.",
        "ImpactChannels": ["Credit Spreads", "MBS Valuations"],
        "Shocks": {"credit_spreads": {"ig_oas": -5, "hy_oas": -15}},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Increase MBS holdings by $750mn", "Reduce corporate bond holdings by $300mn"],
        "Assumptions": "Economic fundamentals support credit quality; investor sentiment remains cautiously optimistic."
    },
    {
        "Scenario": "Bull Steepener Benefits",
        "Description": "A bull steepener in the yield curve allows for profitable repositioning of assets.",
        "Probability": 0.15,
        "Rationale": "Market dynamics suggest a potential steepening of the curve, but risks remain.",
        "ImpactChannels": ["Yield Curve", "NII Protection"],
        "Shocks": {"curve_steepening": 15},
        "MetricsDelta": {"LCR": +1, "NII": +4},
        "TradeList": ["Add $750mn in longer-duration securities", "Reduce short-term funding exposure"],
        "Assumptions": "Market responds positively to Fed policy; growth outlook improves, but with caution."
    },
    {
        "Scenario": "Regulatory Relief",
        "Description": "Potential regulatory relief enhances capital ratios and funding flexibility.",
        "Probability": 0.10,
        "Rationale": "Ongoing discussions about easing regulatory burdens could benefit capital management, but uncertain.",
        "ImpactChannels": ["Capital Ratios", "Funding Flexibility"],
        "Shocks": {"regulatory_relief": "TLAC requirements eased slightly"},
        "MetricsDelta": {"LCR": +2, "NII": +1},
        "TradeList": ["Reassess TLAC funding strategies", "Optimize capital structure"],
        "Assumptions": "Regulatory environment evolves favorably, but progress is gradual."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation and Resilient Consumers",
        "Description": "Inflation remains controlled while consumers continue to spend, supporting economic growth.",
        "Probability": 0.25,
        "Rationale": "Current indicators suggest moderate consumer spending, indicating resilience despite inflationary pressures.",
        "ImpactChannels": ["Consumer Spending", "SME Growth"],
        "Shocks": {"inflation": 2, "consumer_spending": 4},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Increase exposure to consumer credit products by $1bn", "Add $500mn in SME loans"],
        "Assumptions": "Inflation stabilizes; consumer confidence remains strong."
    },
    {
        "Scenario": "Stable Deposit Betas",
        "Description": "Deposit betas remain stable, mitigating funding costs amidst rising rates.",
        "Probability": 0.20,
        "Rationale": "Loyal customer relationships could help maintain deposit betas during rate hikes.",
        "ImpactChannels": ["Funding Costs", "Deposit Stability"],
        "Shocks": {"deposit_betas": 0.02},
        "MetricsDelta": {"LCR": +4, "NII": +3},
        "TradeList": ["Maintain competitive deposit rates", "Optimize funding mix for cost efficiency"],
        "Assumptions": "Customer loyalty persists; competitive landscape remains stable."
    },
    {
        "Scenario": "Tighter Credit Spreads with Improved Basis",
        "Description": "Credit spreads tighten, enhancing MBS and corporate bond valuations.",
        "Probability": 0.20,
        "Rationale": "Market stability and strong corporate earnings may lead to reduced spreads.",
        "ImpactChannels": ["Credit Spreads", "MBS Valuations"],
        "Shocks": {"credit_spreads": {"ig_oas": -10, "hy_oas": -25}},
        "MetricsDelta": {"LCR": +5, "NII": +4},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce corporate bond holdings by $500mn"],
        "Assumptions": "Economic fundamentals support credit quality; investor sentiment is favorable."
    },
    {
        "Scenario": "Bull Steepener Opportunities",
        "Description": "A bull steepener in the yield curve allows for effective asset repositioning.",
        "Probability": 0.15,
        "Rationale": "Market dynamics suggest a potential steepening of the curve, offering convexity benefits.",
        "ImpactChannels": ["Yield Curve", "NII Protection"],
        "Shocks": {"curve_steepening": 25},
        "MetricsDelta": {"LCR": +2, "NII": +5},
        "TradeList": ["Add $1.5bn in longer-duration securities", "Reduce reliance on short-term funding"],
        "Assumptions": "Market responds positively to Fed policy; growth outlook improves."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital ratios and funding flexibility.",
        "Probability": 0.10,
        "Rationale": "Discussions about easing regulatory burdens could benefit capital management.",
        "ImpactChannels": ["Capital Ratios", "Funding Flexibility"],
        "Shocks": {"regulatory_relief": "TLAC requirements eased"},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Reassess TLAC funding strategies", "Optimize capital structure"],
        "Assumptions": "Regulatory environment evolves favorably; market adapts."
    }
]
```

## Round 3

### **Proponent**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation and Resilient Consumers",
        "Description": "Inflation remains manageable while consumers continue to spend, supporting economic growth.",
        "Probability": 0.15,
        "Rationale": "Consumer spending may weaken under sustained inflationary pressures, impacting overall economic activity.",
        "ImpactChannels": ["Consumer Spending", "SME Resilience"],
        "Shocks": {"inflation": 2, "consumer_spending": 2},
        "MetricsDelta": {"LCR": +2, "NII": +1},
        "TradeList": ["Increase exposure to consumer credit products by $500mn", "Focus on maintaining SME lending relationships"],
        "Assumptions": "Inflationary pressures could dampen consumer confidence."
    },
    {
        "Scenario": "Stable Deposit Betas",
        "Description": "Deposit betas remain stable, allowing for controlled funding costs amidst rising rates.",
        "Probability": 0.15,
        "Rationale": "While customer loyalty may mitigate some risks, competitive pressures could lead to increased deposit betas.",
        "ImpactChannels": ["Funding Costs", "Deposit Stability"],
        "Shocks": {"deposit_betas": 0.05},
        "MetricsDelta": {"LCR": +2, "NII": +1},
        "TradeList": ["Adjust deposit rates to remain competitive", "Enhance digital banking offerings"],
        "Assumptions": "Customer preferences may shift due to market conditions."
    },
    {
        "Scenario": "Tighter Credit Spreads with Improved Basis",
        "Description": "Credit spreads tighten, improving valuations for MBS and corporate bonds.",
        "Probability": 0.20,
        "Rationale": "Market stability can lead to reduced credit spreads, benefiting overall portfolio valuations.",
        "ImpactChannels": ["Credit Spreads", "MBS Valuations"],
        "Shocks": {"credit_spreads": {"ig_oas": -10, "hy_oas": -20}},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Increase MBS holdings by $750mn", "Reduce corporate bond holdings by $300mn"],
        "Assumptions": "Economic fundamentals support credit quality, but volatility remains a risk."
    },
    {
        "Scenario": "Bull Steepener Opportunities",
        "Description": "A bull steepener in the yield curve allows for effective asset repositioning.",
        "Probability": 0.10,
        "Rationale": "Market dynamics suggest a potential steepening of the curve, but broader economic conditions may limit this.",
        "ImpactChannels": ["Yield Curve", "NII Protection"],
        "Shocks": {"curve_steepening": 20},
        "MetricsDelta": {"LCR": +1, "NII": +3},
        "TradeList": ["Add $500mn in longer-duration securities", "Monitor short-term funding exposure closely"],
        "Assumptions": "Market response to Fed policy may vary."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital ratios and funding flexibility.",
        "Probability": 0.05,
        "Rationale": "The regulatory environment remains focused on tighter controls, limiting potential relief.",
        "ImpactChannels": ["Capital Ratios", "Funding Flexibility"],
        "Shocks": {"regulatory_relief": "TLAC requirements adjusted"},
        "MetricsDelta": {"LCR": +2, "NII": +1},
        "TradeList": ["Review TLAC funding strategies", "Adapt capital structure to changing regulations"],
        "Assumptions": "Regulatory pressures may continue to increase."
    }
]
```

### **Devil's advocate**

**JSON**

```json
[
    {
        "Scenario": "Controlled Inflation and Resilient Consumers",
        "Description": "Inflation remains manageable while consumers continue to spend, supporting economic growth.",
        "Probability": 0.20,
        "Rationale": "Consumer spending may show resilience, even under inflationary pressures.",
        "ImpactChannels": ["Consumer Spending", "SME Growth"],
        "Shocks": {"inflation": 2, "consumer_spending": 4},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Increase exposure to consumer credit products by $1bn", "Add $500mn in SME loans"],
        "Assumptions": "Inflation stabilizes; consumer confidence remains strong."
    },
    {
        "Scenario": "Stable Deposit Betas",
        "Description": "Deposit betas remain stable, mitigating funding costs amidst rising rates.",
        "Probability": 0.20,
        "Rationale": "Loyal customer relationships may help maintain deposit betas during rate hikes.",
        "ImpactChannels": ["Funding Costs", "Deposit Stability"],
        "Shocks": {"deposit_betas": 0.02},
        "MetricsDelta": {"LCR": +4, "NII": +3},
        "TradeList": ["Maintain competitive deposit rates", "Optimize funding mix for cost efficiency"],
        "Assumptions": "Customer loyalty persists; competitive landscape remains stable."
    },
    {
        "Scenario": "Tighter Credit Spreads with Improved Basis",
        "Description": "Credit spreads tighten, enhancing MBS and corporate bond valuations.",
        "Probability": 0.25,
        "Rationale": "Market stability and strong corporate earnings may lead to reduced spreads.",
        "ImpactChannels": ["Credit Spreads", "MBS Valuations"],
        "Shocks": {"credit_spreads": {"ig_oas": -10, "hy_oas": -25}},
        "MetricsDelta": {"LCR": +5, "NII": +4},
        "TradeList": ["Increase MBS holdings by $1bn", "Reduce corporate bond holdings by $500mn"],
        "Assumptions": "Economic fundamentals support credit quality; investor sentiment is favorable."
    },
    {
        "Scenario": "Bull Steepener Opportunities",
        "Description": "A bull steepener in the yield curve allows for effective asset repositioning.",
        "Probability": 0.15,
        "Rationale": "Market dynamics suggest a potential steepening of the curve, offering convexity benefits.",
        "ImpactChannels": ["Yield Curve", "NII Protection"],
        "Shocks": {"curve_steepening": 20},
        "MetricsDelta": {"LCR": +2, "NII": +5},
        "TradeList": ["Add $1.5bn in longer-duration securities", "Reduce reliance on short-term funding"],
        "Assumptions": "Market responds positively to Fed policy; growth outlook improves."
    },
    {
        "Scenario": "Potential Regulatory Relief",
        "Description": "Regulatory changes enhance capital ratios and funding flexibility.",
        "Probability": 0.10,
        "Rationale": "Discussions about easing regulatory burdens could benefit capital management.",
        "ImpactChannels": ["Capital Ratios", "Funding Flexibility"],
        "Shocks": {"regulatory_relief": "TLAC requirements eased"},
        "MetricsDelta": {"LCR": +3, "NII": +2},
        "TradeList": ["Reassess TLAC funding strategies", "Optimize capital structure"],
        "Assumptions": "Regulatory environment evolves favorably; market adapts."
    }
]
```

