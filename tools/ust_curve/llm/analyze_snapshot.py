import json
import sys

def summarize_curve(snapshot_path):
    with open(snapshot_path, 'r') as f:
        data = json.load(f)

    as_of = data["as_of"]
    prev = data["prev"]
    delta = data["delta"]["zeros_pct"]
    spreads = data["today"]["spreads_pct"]
    d_spreads = data["delta"]["spreads_pct"]

    bullets = []
    bullets.append(f"**UST Yield Curve Summary — {as_of} vs {prev}**")

    # 1⃣ Curve movement
    long_move = max(delta.items(), key=lambda x: x[1])
    bullets.append(f"- Largest yield increase: {long_move[0]} (+{long_move[1]:.2f}%) → Bear-steepening bias.")

    # 2⃣ Slope summary
    slope_msg = "steepened" if d_spreads["2s10s"] > 0 else "flattened"
    bullets.append(f"- 2s10s spread = {spreads['2s10s']:.3f}% ({slope_msg} by {d_spreads['2s10s']*100:.1f} bps).")

    # 3⃣ General move
    avg_move = sum(delta.values()) / len(delta)
    if avg_move > 0:
        bullets.append(f"- Average shift: yields rose by {avg_move*100:.1f} bps (bearish tone).")
    elif avg_move < 0:
        bullets.append(f"- Average shift: yields fell by {abs(avg_move*100):.1f} bps (bullish tone).")
    else:
        bullets.append("- Average shift: unchanged day.")

    # 4⃣ Risk commentary
    risks = []
    if spreads["2s10s"] < 0:
        risks.append("Inversion risk (2s10s negative)")
    if long_move[0] in ["20y", "30y"]:
        risks.append("Long-end duration volatility")
    if not risks:
        risks.append("No immediate structural risks detected.")
    bullets.append(f"- Risks: {', '.join(risks)}")

    return "\n".join(bullets)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "tools/ust_curve/llm/snapshots/curve_snapshot_2025-10-30.json"
    print(summarize_curve(path))
