#!/usr/bin/env python3
"""
Lightweight scenario probability normalizer / aggregator for the UI optimizer.
No QuantLib dependency.
"""

from __future__ import annotations
import argparse, json, sys, copy
from typing import Any, Dict, List
import numpy as np


def _extract_probability(sc: Dict[str, Any]) -> float:
    val = sc.get("Probability", sc.get("probability", sc.get("p", 0.0)))
    try:
        v = float(val)
        return v / 100.0 if v > 1 else v
    except Exception:
        return 0.0


def normalize_probabilities(scenarios: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[float], str]:
    probs = np.array([_extract_probability(sc) for sc in scenarios], dtype=float)
    total = float(probs.sum())
    note: str
    if total <= 0:
        probs = np.ones_like(probs) / max(len(probs), 1)
        note = "Input probabilities missing/zero; used uniform weights."
    else:
        probs = probs / total
        note = f"Renormalized probabilities to 1.0 (original sum={total:.4f})."
    normalized = []
    for sc, p in zip(scenarios, probs):
        dup = copy.deepcopy(sc)
        dup["Probability"] = float(round(p, 6))
        normalized.append(dup)
    return normalized, probs.tolist(), note


def _num(d: Dict[str, Any], keys: List[str]) -> float:
    for k in keys:
        if k in d:
            try:
                return float(d[k])
            except Exception:
                continue
    return 0.0


def aggregate_metrics(scenarios: List[Dict[str, Any]], probs: List[float]) -> Dict[str, float]:
    fields = {
        "dLCR_pct": ["dLCR_pct", "LCR", "lcr", "delta_lcr"],
        "dNSFR_pct": ["dNSFR_pct", "NSFR", "nsfr", "delta_nsfr"],
        "dNII_bps": ["dNII_bps", "NII", "nii_bps", "delta_nii_bps"],
        "dur_change_years": ["dur_change_years", "Duration", "duration"],
    }
    agg: Dict[str, float] = {k: 0.0 for k in fields}
    for sc, p in zip(scenarios, probs):
        md = sc.get("MetricsDelta") or sc.get("metrics") or {}
        for field, keys in fields.items():
            agg[field] += p * _num(md, keys)
    return {k: float(round(v, 6)) for k, v in agg.items()}


def aggregate_trades(scenarios: List[Dict[str, Any]], probs: List[float], top_n: int = 8) -> List[Dict[str, Any]]:
    score: Dict[str, float] = {}
    contrib: Dict[str, List[str]] = {}
    for sc, p in zip(scenarios, probs):
        trades = sc.get("TradeList") or sc.get("trades") or []
        scen_name = sc.get("Scenario") or sc.get("name") or ""
        for t in trades:
            if not isinstance(t, str):
                continue
            score[t] = score.get(t, 0.0) + float(p)
            contrib.setdefault(t, []).append(scen_name)
    ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    out = []
    for trade, weight in ranked[:top_n]:
        out.append(
            {
                "trade": trade,
                "weight": float(round(weight, 6)),
                "scenarios": sorted(list({c for c in contrib.get(trade, []) if c})),
            }
        )
    return out


def aggregate_signals(scenarios: List[Dict[str, Any]], probs: List[float], top_n: int = 8) -> List[Dict[str, Any]]:
    score: Dict[str, float] = {}
    contrib: Dict[str, List[str]] = {}
    for sc, p in zip(scenarios, probs):
        signals = sc.get("Signals") or sc.get("signals") or []
        scen_name = sc.get("Scenario") or sc.get("name") or ""
        for sig in signals:
            if not isinstance(sig, str):
                continue
            score[sig] = score.get(sig, 0.0) + float(p)
            contrib.setdefault(sig, []).append(scen_name)
    ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    out = []
    for sig, weight in ranked[:top_n]:
        out.append(
            {
                "signal": sig,
                "weight": float(round(weight, 6)),
                "scenarios": sorted(list({c for c in contrib.get(sig, []) if c})),
            }
        )
    return out


def main():
    parser = argparse.ArgumentParser(description="Probability normalizer + aggregator.")
    parser.add_argument("--scenarios", required=True, help="Path to scenario JSON array.")
    parser.add_argument("--mode", default="probability_weighted", choices=["probability_weighted"])
    parser.add_argument("--top-trades", type=int, default=8)
    parser.add_argument("--top-signals", type=int, default=8)
    args = parser.parse_args()

    print(f"[scenario_prob_cli] Loading scenarios from {args.scenarios}")
    with open(args.scenarios, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Scenario input must be a JSON array.")

    print(f"[scenario_prob_cli] Loaded {len(data)} scenarios; normalizing probabilities…")
    normalized, probs, note = normalize_probabilities(data)
    print(
        f"[scenario_prob_cli] Probability sum before={sum([_extract_probability(sc) for sc in data]):.4f} "
        f"after={sum(probs):.4f}"
    )
    metrics = aggregate_metrics(normalized, probs)
    trades = aggregate_trades(normalized, probs, top_n=args.top_trades)
    signals = aggregate_signals(normalized, probs, top_n=args.top_signals)
    print(
        f"[scenario_prob_cli] Aggregated metrics: {metrics} | trades={len(trades)} | signals={len(signals)}"
    )
    out = {
        "mode": args.mode,
        "probability_sum": float(round(float(sum(probs)), 6)),
        "probability_note": note,
        "normalized_scenarios": normalized,
        "expected_metrics": metrics,
        "trade_recommendations": trades,
        "signal_watchlist": signals,
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)
