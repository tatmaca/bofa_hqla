import numpy as np
import pandas as pd

# ㅊ 다녀감

BASE_90D = 0.25 #TODO make a config file
SENSITIVITY = 0.6
CAP = 0.80

# TODO this is basic update to use some regression or smth
def composite_probs(X: pd.DataFrame) -> pd.DataFrame:
    zcols = [c for c in X.columns if c.endswith("_z_252") and any(k in c for k in ["MOVE","SURPRISE","EFFR"])]
    if not zcols:
        zcols = [c for c in X.columns if c.endswith("_z_252") and "MOVE" in c]
    zbar = X[zcols].mean(axis=1)
    p90 = np.clip(BASE_90D * np.exp(SENSITIVITY * zbar), 0.0, CAP)
    p30 = 1 - (1 - p90)**(1/3)
    out = pd.DataFrame({"P30_liq_stress": p30, "P90_liq_stress": p90}, index=X.index)
    out.attrs["zcols_used"] = zcols
    return out