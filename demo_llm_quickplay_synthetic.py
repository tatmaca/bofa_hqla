#!/usr/bin/env python3
"""
Synthetic quick-play demo (no DB, no snapshots):
- Uses a few sample news items (edit SAMPLE_NEWS to play).
- Calls OpenAI to score 4 key factors with intensity in [-2,2] and confidence in [0,1].
- Aggregates c*s per factor (clip to [-2.5, 2.5]) and applies cold-start coefficients (subset)
  to predict yield deltas (bps) for 2Y/5Y/10Y/30Y.
- Compares to hardcoded real moves (2025-11-20 -> 2025-11-21) and runs one-step update + attribution.

Run from tools/news_ingestion (PowerShell):
  $env:OPENAI_API_KEY="your_key"
  python demo_llm_quickplay_synthetic.py

Outputs: prints factor scores, predictions, actuals, errors, updated coefs; saves JSON to demo_outputs/demo_prediction_synthetic.json
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

TENORS = ["2Y", "5Y", "10Y", "30Y"]

# Hardcoded yields for 2025-11-20 and 2025-11-21 (percentage levels)
YIELDS_2025_11_20 = {"3M": 3.86, "2Y": 3.55, "5Y": 3.68, "10Y": 4.10, "30Y": 4.73}
YIELDS_2025_11_21 = {"3M": 3.84, "2Y": 3.51, "5Y": 3.62, "10Y": 4.06, "30Y": 4.71}

# 4 representative factors (SUPPLY_LONG removed)
FACTORS = {
    "FED_TONE": "Fed tone on rates (hawkish vs dovish) affecting front end",
    "CPI_CORE_SURP": "Core inflation surprise vs expectations",
    "NFP_SURP": "Nonfarm payrolls surprise vs expectations",
    "RISK_OFF": "Risk-off tone (equities down, credit wider)",
}

# Sample news (edit to play)
SAMPLE_NEWS = [
    {
        "title": "NVIDIA posts blowout earnings, raises guidance on AI demand",
        "summary": "Revenue and margins beat estimates; management guides higher on data center and AI chips.",
    },
    {
        "title": "Fed officials signal rate cut again, can't see rates on hold for longer",
        "summary": "Speeches emphasize data dependence and balanced risks; may have rush to cut.",
    },
    {
        "title": "US payrolls miss, unemployment ticks higher",
        "summary": "Jobs report weaker than expected; wage growth cools.",
    },
    {
        "title": "Global risk-off on Middle East escalation; equities sell off",
        "summary": "Flight-to-quality flows push yields lower at the long end.",
    },
]

ROOT = Path(__file__).resolve().parents[1]
NEWS_DIR = Path(__file__).parent
OUT_DIR = NEWS_DIR / "demo_outputs"
OUT_DIR.mkdir(exist_ok=True)


def compute_actual_changes_bps(yesterday: Dict[str, float], today: Dict[str, float]) -> Dict[str, float]:
    """(today - yesterday) * 100 -> bps."""
    out: Dict[str, float] = {}
    for tenor in TENORS:
        if tenor in yesterday and tenor in today:
            out[tenor] = (today[tenor] - yesterday[tenor]) * 100.0
    return out


@dataclass
class OnylParams:
    learning_rate: float = 0.05
    max_daily_coef_change: float = 0.8
    smoothing_gamma: float = 0.2


def get_api_key() -> Optional[str]:
    return os.environ.get("OPENAI_API_KEY")


# Cold-start coefficients in bps per unit factor (subset copied from config)
COLD_START_COEFFICIENTS: Dict[str, Dict[str, float]] = {
    "2Y": {
        "FED_TONE": 8.0,
        "CPI_CORE_SURP": 3.0,
        "NFP_SURP": 4.0,
        "RISK_OFF": -3.0,
    },
    "5Y": {
        "FED_TONE": 7.0,
        "CPI_CORE_SURP": 3.0,
        "NFP_SURP": 4.0,
        "RISK_OFF": -3.0,
    },
    "10Y": {
        "FED_TONE": 5.0,
        "CPI_CORE_SURP": 2.0,
        "NFP_SURP": 3.0,
        "RISK_OFF": -2.0,
    },
    "30Y": {
        "FED_TONE": 3.0,
        "CPI_CORE_SURP": 2.0,
        "NFP_SURP": 2.0,
        "RISK_OFF": -2.0,
    },
}


def call_llm_score(api_key: str, article: Dict) -> Dict[str, Dict]:
    """
    Score each factor with:
    - intensity s in [-2, 2]
    - confidence c in [0, 1]
    We aggregate c * s per factor (then clip).
    """
    if not HAS_OPENAI:
        raise RuntimeError("openai package not installed")

    client = OpenAI(api_key=api_key)
    factor_list = "\n".join([f"  * {k}: {v}" for k, v in FACTORS.items()])
    prompt = f"""Score how this news loads on the four factors. Use:
- intensity s in [-2.0, 2.0] (sign = pushes yields DOWN if negative, UP if positive via that factor)
- confidence c in [0.0, 1.0]
- Keep s conservative (|s| > 1.5 only if very strong/explicit)
- Provide a one-sentence reason per factor, citing the specific content
- We will aggregate c * s per factor (clip later)
- Factors:
{factor_list}

Few-shot examples (guidance):

Example 1
News: "Fed officials signal patience, likely to hold rates steady; balance of risks now more two-sided."
Output:
{{
  "factor_scores": {{
    "FED_TONE": {{"intensity": -0.6, "confidence": 0.6, "reason": "Patience/balanced risks is mildly dovish vs hikes"}},
    "CPI_CORE_SURP": {{"intensity": 0.0, "confidence": 0.2, "reason": "No inflation data"}},
    "NFP_SURP": {{"intensity": 0.0, "confidence": 0.2, "reason": "No labor data"}},
    "RISK_OFF": {{"intensity": 0.0, "confidence": 0.2, "reason": "No risk sentiment shift stated"}}
  }}
}}

Example 2
News: "US payrolls miss; unemployment ticks up; wage growth cools materially."
Output:
{{
  "factor_scores": {{
    "FED_TONE": {{"intensity": -0.6, "confidence": 0.7, "reason": "Weaker labor tilts Fed dovish"}},
    "CPI_CORE_SURP": {{"intensity": -0.3, "confidence": 0.6, "reason": "Cooler wages imply softer core inflation"}},
    "NFP_SURP": {{"intensity": -1.2, "confidence": 0.8, "reason": "Clear labor miss and higher unemployment"}},
    "RISK_OFF": {{"intensity": -0.4, "confidence": 0.6, "reason": "Soft data can trigger mild risk-off"}}
  }}
}}

Example 3
News: "Global risk-off on Middle East escalation; equities sell off."
Output:
{{
  "factor_scores": {{
    "FED_TONE": {{"intensity": 0.0, "confidence": 0.2, "reason": "No policy tone"}},
    "CPI_CORE_SURP": {{"intensity": 0.0, "confidence": 0.2, "reason": "No inflation data"}},
    "NFP_SURP": {{"intensity": 0.0, "confidence": 0.2, "reason": "No labor data"}},
    "RISK_OFF": {{"intensity": -1.2, "confidence": 0.8, "reason": "Explicit risk-off tone from geopolitical tension"}}
  }}
}}

Now score this news:
Title: {article.get('title','')}
Summary: {article.get('summary','')}
Return strict JSON only in the same schema as above.
"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a senior fixed-income strategist. Be concise. Always return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def aggregate_scores(per_article: List[Dict[str, Dict]]) -> Dict[str, float]:
    """
    Sum confidence * intensity per factor across articles, then clip to [-2.5, 2.5].
    """
    agg = {f: 0.0 for f in FACTORS}
    for res in per_article:
        fs = res.get("factor_scores", {})
        for f in FACTORS:
            if f in fs:
                try:
                    s = float(fs[f].get("intensity", 0.0))
                    c = float(fs[f].get("confidence", 0.0))
                    agg[f] += c * s
                except Exception:
                    pass
    for f in FACTORS:
        if agg[f] > 2.5:
            agg[f] = 2.5
        elif agg[f] < -2.5:
            agg[f] = -2.5
    return agg


def predict_yields(factor_scores: Dict[str, float], coefs: Dict[str, Dict[str, float]], intercepts: Dict[str, float]) -> Dict[str, float]:
    preds = {}
    for t in TENORS:
        y_hat = intercepts.get(t, 0.0)
        for f, x in factor_scores.items():
            y_hat += coefs.get(t, {}).get(f, 0.0) * x
        preds[t] = y_hat
    return preds


def compute_update_weights(factor_scores: Dict[str, float]) -> Dict[str, float]:
    weights = {}
    small_sum = 0.0
    large = {}
    for f, x in factor_scores.items():
        ax = abs(x)
        if ax < 0.3:
            weights[f] = 0.3
            small_sum += 0.3 * ax
        else:
            large[f] = ax
    remaining = max(0.0, 3.0 - small_sum)
    if large:
        total_large = sum(large.values())
        scale = remaining / total_large if total_large > 0 else 0.0
        for f, ax in large.items():
            weights[f] = scale
    else:
        for f in factor_scores:
            weights.setdefault(f, 0.3)
    return weights


def smooth_across_maturities(coeffs: Dict[str, Dict[str, float]], gamma: float) -> Dict[str, Dict[str, float]]:
    smoothed = {t: {} for t in TENORS}
    all_factors = set()
    for d in coeffs.values():
        all_factors.update(d.keys())
    ordered = ["2Y", "5Y", "10Y", "30Y"]
    for f in all_factors:
        for i, tenor in enumerate(ordered):
            if i == 0 or i == len(ordered) - 1:
                smoothed[tenor][f] = coeffs.get(tenor, {}).get(f, 0.0)
            else:
                cur = coeffs.get(tenor, {}).get(f, 0.0)
                prev_t = ordered[i - 1]
                next_t = ordered[i + 1]
                prev_val = coeffs.get(prev_t, {}).get(f, 0.0)
                next_val = coeffs.get(next_t, {}).get(f, 0.0)
                smoothed[tenor][f] = (1 - gamma) * cur + (gamma / 2.0) * (prev_val + next_val)
    return smoothed


def update_coefficients(params: OnylParams, coeffs: Dict[str, Dict[str, float]], factor_scores: Dict[str, float], actual_changes: Dict[str, float], preds: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    η = params.learning_rate
    ΔB_max = params.max_daily_coef_change
    errors = {t: actual_changes.get(t, 0.0) - preds.get(t, 0.0) for t in TENORS}
    weights = compute_update_weights(factor_scores)
    new_coeffs = {t: dict(coeffs.get(t, {})) for t in TENORS}
    for tenor in TENORS:
        e = errors[tenor]
        for f, x in factor_scores.items():
            b_old = coeffs.get(tenor, {}).get(f, 0.0)
            w = weights.get(f, 0.3)
            ΔB = η * w * e * x
            if ΔB > ΔB_max:
                ΔB = ΔB_max
            elif ΔB < -ΔB_max:
                ΔB = -ΔB_max
            new_coeffs[tenor][f] = b_old + ΔB
    new_coeffs = smooth_across_maturities(new_coeffs, params.smoothing_gamma)
    return new_coeffs, errors


def update_intercepts(params: OnylParams, intercepts: Dict[str, float], actual_changes: Dict[str, float], preds: Dict[str, float]) -> Dict[str, float]:
    η = params.learning_rate
    new_b = {}
    for tenor in TENORS:
        e = actual_changes.get(tenor, 0.0) - preds.get(tenor, 0.0)
        new_b[tenor] = intercepts.get(tenor, 0.0) + η * e
    return new_b


def attribute_move(coeffs_old: Dict[str, Dict[str, float]], factor_scores: Dict[str, float], intercepts: Dict[str, float], actual_changes: Dict[str, float], preds: Dict[str, float]) -> None:
    print("===== Attribution (pre-update) =====")
    for tenor in TENORS:
        pred = preds[tenor]
        actual = actual_changes.get(tenor, 0.0)
        b0 = intercepts.get(tenor, 0.0)
        contribs = {}
        for f, x in factor_scores.items():
            contribs[f] = coeffs_old.get(tenor, {}).get(f, 0.0) * x
        sum_contribs = sum(contribs.values())
        recon = sum_contribs + b0
        print(f"\nTenor {tenor}:")
        print(f"  Predicted Δy: {pred:+.3f} bps")
        print(f"  Reconstructed (sum contrib + intercept): {recon:+.3f} bps")
        print(f"  Actual Δy: {actual:+.3f} bps")
        print("  Factor contributions to PREDICTION:")
        for f, c in contribs.items():
            share_pred = c / pred if abs(pred) > 1e-6 else 0.0
            print(f"    {f}: {c:+.3f} bps  ({share_pred:+.1%} of pred)")
        if abs(pred) > 1e-6:
            print("  Factor contributions to ACTUAL (allocated by model weights):")
            for f, c in contribs.items():
                weight = c / pred
                c_actual = actual * weight
                print(f"    {f}: {c_actual:+.3f} bps  (weight {weight:+.1%})")
        else:
            print("  Pred ~ 0, skip actual attribution for stability.")


def main():
    api_key = get_api_key()
    if not api_key:
        print("No OPENAI_API_KEY found in env.")
        return

    params = OnylParams()
    coefs = {t: dict(COLD_START_COEFFICIENTS[t]) for t in TENORS}
    intercepts = {t: 0.0 for t in TENORS}
    actual_changes = compute_actual_changes_bps(YIELDS_2025_11_20, YIELDS_2025_11_21)

    print("Actual changes 2025-11-20 -> 2025-11-21 (bps):")
    for t in TENORS:
        print(f"  {t}: {actual_changes.get(t, 0.0):+.2f}")

    scored_articles = []
    print("\nScoring sample news via LLM...")
    for i, art in enumerate(SAMPLE_NEWS, 1):
        print(f"\n[LLM] Article {i}: {art['title']}")
        res = call_llm_score(api_key, art)
        scored_articles.append(res)
        for f in FACTORS:
            fs = res.get("factor_scores", {}).get(f, {})
            if fs:
                print(f"  {f}: intensity={fs.get('intensity')} confidence={fs.get('confidence')} reason={fs.get('reason')}")

    agg = aggregate_scores(scored_articles)
    print("\nAggregated factor scores (sum of c*s, clipped to [-2.5,2.5]):")
    for f, v in agg.items():
        print(f"  {f}: {v:.2f}")

    preds = predict_yields(agg, coefs, intercepts)
    print("\nPredicted Δy (bps) before update:")
    for t in TENORS:
        print(f"  {t}: {preds[t]:+.2f}")

    attribute_move(coefs, agg, intercepts, actual_changes, preds)

    new_coefs, errors = update_coefficients(params, coefs, agg, actual_changes, preds)
    new_intercepts = update_intercepts(params, intercepts, actual_changes, preds)

    print("\nErrors (actual - pred) and updated coefficients:")
    for t in TENORS:
        print(f"  {t}: error={errors.get(t,0.0):+.2f} bps | updated coefs: {new_coefs[t]}")

    print("\nUpdated intercepts:")
    for t in TENORS:
        print(f"  {t}: {new_intercepts[t]:+.4f} bps")

    out = {
        "articles": SAMPLE_NEWS,
        "factor_scores_per_article": scored_articles,
        "factor_scores_aggregated": agg,
        "predicted_delta_bps": preds,
        "actual_delta_bps": actual_changes,
        "errors_bps": errors,
        "updated_coefficients": new_coefs,
        "updated_intercepts": new_intercepts,
        "params": params.__dict__,
    }
    out_file = OUT_DIR / "demo_prediction_synthetic.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to {out_file}")


if __name__ == "__main__":
    main()
