from .load_data import load_indicators
from .features import make_features
from .probs import composite_probs
from .prompt_template import SCENARIO_PROMPT

# ㅊ 다녀감


def _format_prompt(latest_X, latest_P):
    opt_sur = ""
    if "SURPRISE" in latest_X.index:
        opt_sur = f"- Macro surprise={latest_X['SURPRISE']:.2f} (z={latest_X['SURPRISE_z_252']:.2f}, 1mΔ={latest_X['SURPRISE_chg_21d']:.2f})"
    opt_effr = ""
    if "EFFR" in latest_X.index:
        opt_effr = f"- EFFR={latest_X['EFFR']:.2f} (z={latest_X['EFFR_z_252']:.2f}, 1mΔ={latest_X['EFFR_chg_21d']:.2f})"
    return SCENARIO_PROMPT.format(
        MOVE=latest_X["MOVE"],
        MOVE_z=latest_X["MOVE_z_252"],
        MOVE_chg=latest_X["MOVE_chg_21d"],
        SLOPE=latest_X["SLOPE_2s10s_bps"],
        SLOPE_z=latest_X["SLOPE_2s10s_bps_z_252"],
        SLOPE_chg=latest_X["SLOPE_2s10s_bps_chg_21d"],
        OPT_SURPRISE=opt_sur,
        OPT_EFFR=opt_effr,
        P30=latest_P["P30_liq_stress"],
        P90=latest_P["P90_liq_stress"],
    )

def main():
    df = load_indicators()
    X  = make_features(df)
    P  = composite_probs(X)
    latest_X, latest_P = X.iloc[-1], P.iloc[-1]
    prompt = _format_prompt(latest_X, latest_P)

    print("\n=== COPY THIS PROMPT INTO YOUR LLM ===\n")
    print(prompt)
    print("\n=== EXPECTED RESULT: a 5-column Scenario Matrix (Markdown) ===\n")

if __name__ == "__main__":
    main()