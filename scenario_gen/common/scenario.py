from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
import json, hashlib

class ScenarioFamily(str, Enum):
    LIQUIDITY = "Liquidity"
    IRR = "InterestRateRisk"
    CAPITAL = "Capital"
    REGULATORY = "Regulatory" #idk if these are next or what others clases it would be
    MACRO = "Macro"

class ProbKind(str, Enum):
    ABSOLUTE = "absolute"        # standalone 6m-ish probability
    CONDITIONAL = "conditional"  # conditional on another scenario
    SUBJECTIVE = "subjective"    # LLM/human judgment

@dataclass
class Probability:
    value: float                 # 0..1
    kind: ProbKind = ProbKind.ABSOLUTE
    horizon_days: int = 180
    confidence: Optional[float] = None
    notes: Optional[str] = None
    def clamp(self):
        self.value = max(0.0, min(1.0, float(self.value)))
        if self.confidence is not None:
            self.confidence = max(0.0, min(1.0, float(self.confidence)))

@dataclass
class ImpactChannels:
    delta_LCR_bps: Optional[float] = None
    delta_NSFR_bps: Optional[float] = None
    delta_RWA_pct: Optional[float] = None
    delta_NII_bps: Optional[float] = None
    hqla_mix_notes: Optional[str] = None  # e.g., "shift +10% to Level 1; L2 haircuts +25%"

@dataclass
class Trigger:
    indicator: str               # e.g., "MOVE_z_252"
    condition: str               # human readable ("> 1.0 for 3d")
    machine_rule: Optional[Dict] = None   # optional structured rule

@dataclass
class Scenario:
    name: str
    family: ScenarioFamily
    description: str
    rationale: str
    probability: Probability
    impact: ImpactChannels
    triggers: List[Trigger] = field(default_factory=list)
    shock_vector: Dict[str, float] = field(default_factory=dict)
    assumptions: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    as_of: datetime = field(default_factory=datetime.utcnow)
    owner: Optional[str] = None
    reviewer: Optional[str] = None
    version: str = "0.1.0"
    scenario_id: Optional[str] = None

    def __post_init__(self):
        self.probability.clamp()
        if not self.scenario_id:
            base = json.dumps(
                {"name": self.name, "as_of": self.as_of.isoformat(),
                 "family": self.family.value, "version": self.version},
                sort_keys=True
            ).encode("utf-8")
            self.scenario_id = hashlib.sha1(base).hexdigest()[:10]

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["family"] = self.family.value
        d["probability"]["kind"] = self.probability.kind.value
        d["as_of"] = self.as_of.isoformat()
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_matrix_row(self) -> Dict[str, str]:
        prob_pct = f"{round(self.probability.value*100,1)}%"
        return {
            "Scenario": self.name,
            "Description": self.description,
            "Probability": prob_pct,
            "Rationale": self.rationale,
            "Impact Channels": self.impact.hqla_mix_notes or self._impact_summary()
        }

    def _impact_summary(self) -> str:
        bits = []
        if self.impact.delta_LCR_bps is not None: bits.append(f"ΔLCR {self.impact.delta_LCR_bps:+.0f} bps")
        if self.impact.delta_NSFR_bps is not None: bits.append(f"ΔNSFR {self.impact.delta_NSFR_bps:+.0f} bps")
        if self.impact.delta_RWA_pct is not None: bits.append(f"ΔRWA {self.impact.delta_RWA_pct:+.1f}%")
        if self.impact.delta_NII_bps is not None: bits.append(f"ΔNII {self.impact.delta_NII_bps:+.0f} bps")
        return "; ".join(bits) if bits else "See notes"