import pandas as pd

# ㅊ 다녀감

def make_features(df: pd.DataFrame, roll:int=252, d:int=21) -> pd.DataFrame:
    X = df.copy()
    base_cols = [c for c in X.columns if c in ["MOVE","SURPRISE","EFFR","SLOPE_2s10s_bps"]]
    for c in base_cols:
        X[f"{c}_chg_{d}d"] = X[c].diff(d)
        mu = X[c].rolling(roll).mean()
        sd = X[c].rolling(roll).std(ddof=1)
        X[f"{c}_z_{roll}"] = (X[c] - mu) / sd
    return X.dropna()