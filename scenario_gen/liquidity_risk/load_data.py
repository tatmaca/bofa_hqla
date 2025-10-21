import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

def _read_move_bloomberg_xlsx(path: Path) -> pd.Series:
    """
    Read Bloomberg-style MOVE export:
    metadata rows, then a header row containing: Date, PX_LAST, CHG_PCT_1D.
    Returns a pandas Series named 'MOVE' indexed by datetime.
    """
    # 1) Read raw with no header to locate the real header row
    raw = pd.read_excel(path, sheet_name=0, header=None, engine="openpyxl")

    # find the row index where first cell is 'Date' (case-insensitive, strip spaces)
    hdr_idx = None
    for i in range(len(raw)):
        val = str(raw.iat[i, 0]).strip().lower()
        if val == "date":
            hdr_idx = i
            break
    if hdr_idx is None:
        raise ValueError(f"Could not find 'Date' header row in {path}")

    # 2) Re-read using that row as header
    df = pd.read_excel(path, sheet_name=0, header=hdr_idx, engine="openpyxl")

    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]

    # 3) Keep only Date and PX_LAST
    if "Date" not in df.columns or "PX_LAST" not in df.columns:
        raise ValueError(f"'Date' or 'PX_LAST' not found in {path} columns={df.columns}")

    # 4) Parse Date robustly (Bloomberg uses mm/dd/yy by default)
    # try common formats, then fallback
    date = pd.to_datetime(df["Date"], format="%m/%d/%y", errors="coerce")
    if date.isna().all():
        date = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    if date.isna().all():
        date = pd.to_datetime(df["Date"], errors="coerce")
    df = df.loc[~date.isna()].copy()
    df.index = pd.DatetimeIndex(date.loc[~date.isna()])
    df = df.sort_index()

    # 5) Value column as float
    move = pd.to_numeric(df["PX_LAST"], errors="coerce").astype(float)
    move = move.dropna()
    move.name = "MOVE"
    return move

def _read_csv_series(path: Path, value_col_guess: str | None = None) -> pd.Series:
    df = pd.read_csv(path)
    # assume first col is date (your repo convention)
    date_col = df.columns[0]
    date = pd.to_datetime(df[date_col], errors="coerce")
    df = df.loc[~date.isna()].copy()
    df.index = pd.DatetimeIndex(date.loc[~date.isna()])
    df = df.sort_index()

    if value_col_guess and value_col_guess in df.columns:
        col = value_col_guess
        s = pd.to_numeric(df[col], errors="coerce")
    else:
        # pick the first numeric column after date
        num_cols = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            # fallback: coerce each and pick the one with most numeric entries
            numeric_counts, coerced = {}, {}
            for c in df.columns[1:]:
                v = pd.to_numeric(df[c], errors="coerce")
                coerced[c] = v
                numeric_counts[c] = v.notna().sum()
            if not numeric_counts:
                raise ValueError(f"No numeric columns in {path}")
            col = max(numeric_counts, key=numeric_counts.get)
            s = coerced[col]
        else:
            col = num_cols[0]
            s = df[col].astype(float)

    s = s.dropna()
    s.name = path.stem
    return s

def load_indicators():
    # Use the Bloomberg-aware reader for MOVE
    move = _read_move_bloomberg_xlsx(DATA_DIR / "moveindex.xlsx").rename("MOVE")

    # DGS2 / DGS10 CSVs already in your repo; first col is date
    dgs2  = _read_csv_series(DATA_DIR / "DGS2.csv",  value_col_guess="DGS2").rename("DGS2")
    dgs10 = _read_csv_series(DATA_DIR / "DGS10.csv", value_col_guess="DGS10").rename("DGS10")

    # Optional extras if present (first column is date per your convention)
    surprise = (_read_csv_series(DATA_DIR / "surpriseindex.xlsx") if False else None)  # keep Excel for surprise if you want
    effr = (_read_csv_series(DATA_DIR / "effr.xlsx") if False else None)

    # Merge
    parts = [move, dgs2, dgs10]  # add surprise/effr later when standardized
    df = pd.concat(parts, axis=1).dropna().sort_index()

    # Build 2s10s slope (bps)
    df["SLOPE_2s10s_bps"] = (df["DGS10"] - df["DGS2"]) * 100.0
    return df