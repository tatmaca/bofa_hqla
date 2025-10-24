# scenario_gen/common/probs_api.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Mapping, Protocol, Tuple
import pandas as pd
import numpy as np

HORIZONS = ("P30", "P90")  # canonical horizons

@dataclass(frozen=True)
class ScenarioSpec:
    risk_type: str        # "credit" | "liquidity" | "interest_rate"
    scenario_id: str      # e.g., "mild", "severe", "compress", "liq_stress", "bear_steepen"
    description: str      # short machine-readable label

@dataclass
class ProbsFrame:
    """
    probabilities indexed by Date. Columns use a stable naming:
    <HORIZON>:<risk_type>/<scenario_id>  e.g., 'P90:credit/mild'
    """
    df: pd.DataFrame                      # float in [0,1]
    scenarios: List[ScenarioSpec]         # catalog for metadata

    def latest_row(self) -> pd.Series:
        return self.df.iloc[-1]

class ProbProvider(Protocol):
    """Every risk module implements this."""
    def name(self) -> str: ...
    def required_columns(self) -> List[str]: ...
    def compute_probs(self, features: pd.DataFrame) -> ProbsFrame: ...

def _columns(h: str, specs: List[ScenarioSpec]) -> List[str]:
    return [f"{h}:{s.risk_type}/{s.scenario_id}" for s in specs]

def merge_probs(frames: List[ProbsFrame]) -> ProbsFrame:
    """Outer-join by index, align columns, keep scenario catalogs."""
    if not frames:
        raise ValueError("No ProbsFrame objects to merge.")
    catalog: List[ScenarioSpec] = []
    parts = []
    for fr in frames:
        catalog.extend(fr.scenarios)
        parts.append(fr.df)
    out = pd.concat(parts, axis=1).sort_index()
    # Reorder columns deterministically by (HORIZON, risk_type, scenario_id)
    def _key(c):
        h, rest = c.split(":", 1)
        rtype, sid = rest.split("/", 1)
        return (h, rtype, sid)
    out = out.reindex(sorted(out.columns, key=_key), axis=1)
    return ProbsFrame(df=out, scenarios=catalog)