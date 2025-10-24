from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_yaml_dir(d: Path) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Load all *.yaml files in directory d into a nested dictionary.
    Example output:
        {
            "credit": {"severe": {"IG_OAS_bp": 80, "HY_OAS_bp": 200}},
            "liquidity": {"stress": {"MOVE_pts": 25}},
            "rates": {"bear_steepen": {"DGS2_bp": 10, "DGS10_bp": 30}}
        }
    """
    out: Dict[str, Dict[str, Dict[str, float]]] = {}
    for f in sorted(d.glob("*.yaml")):
        with f.open("r") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{f.name}: top-level must be a mapping of scenarios.")
        out[f.stem] = data
    return out


def flatten_shocks(shocks: Dict[str, Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
    """Flatten nested structure into 'risk/scenario' -> {variable: value}."""
    flat: Dict[str, Dict[str, float]] = {}
    for risk, scenemap in shocks.items():
        for scen, vect in (scenemap or {}).items():
            if not isinstance(vect, dict):
                raise ValueError(f"{risk}.yaml scenario '{scen}' must map to a dict of variables.")
            flat[f"{risk}/{scen}"] = vect
    return flat


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

_ALLOWED_SUFFIXES = ("_bp", "_bps", "_pts", "_pct")

def validate_units(flat: Dict[str, Dict[str, float]]) -> List[str]:
    """Ensure all variable names have valid unit suffixes and numeric values."""
    issues = []
    for key, vect in flat.items():
        for var, val in vect.items():
            if not isinstance(val, (int, float)):
                issues.append(f"{key}: variable '{var}' must have a numeric value.")
            if not any(var.endswith(sfx) for sfx in _ALLOWED_SUFFIXES):
                issues.append(f"{key}: '{var}' missing unit suffix {_ALLOWED_SUFFIXES}.")
    return issues


def validate_against_probs(flat: Dict[str, Dict[str, float]], probs_csv: Path) -> List[str]:
    """Verify that every scenario in probabilities has a matching shock and vice versa."""
    issues = []
    if not probs_csv.exists():
        issues.append(f"Probabilities file not found: {probs_csv}")
        return issues

    df = pd.read_csv(probs_csv)
    prob_cols = [c for c in df.columns if ":" in c]
    prob_keys = set(c.split(":", 1)[1] for c in prob_cols)
    shock_keys = set(flat.keys())

    missing = sorted(prob_keys - shock_keys)
    extra = sorted(shock_keys - prob_keys)

    if missing:
        issues.append(f"Missing shocks for scenarios in probabilities: {missing}")
    if extra:
        issues.append(f"Extra shocks not found in probabilities: {extra}")
    return issues


# ---------------------------------------------------------------------------
# Output Writer
# ---------------------------------------------------------------------------

def write_outputs(flat: Dict[str, Dict[str, float]], out_path: Path, manifest_path: Path, probs_csv: Path) -> None:
    """Write shocks_resolved.json and manifest.json for audit tracking."""
    payload = json.dumps(flat, indent=2, sort_keys=True).encode("utf-8")
    out_path.write_bytes(payload)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hash_sha256": hashlib.sha256(payload).hexdigest(),
        "output_path": str(out_path),
        "probs_csv": str(probs_csv),
        "scenario_count": len(flat),
        "keys": sorted(flat.keys()),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"[OK] wrote {out_path} (scenarios={len(flat)})")
    print(f"[OK] wrote {manifest_path}")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate and compile scenario shocks into JSON.")
    parser.add_argument("--dir", default=str(Path(__file__).resolve().parent),
                        help="Directory containing YAML shock definitions.")
    parser.add_argument("--probs", default=str(Path(__file__).resolve().parents[1] / "scenario_gen" / "combined_probabilities.csv"),
                        help="Path to combined_probabilities.csv for coverage validation.")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "shocks_resolved.json"),
                        help="Output JSON path for flattened shocks.")
    parser.add_argument("--manifest", default=str(Path(__file__).resolve().parent / "manifest.json"),
                        help="Output JSON path for manifest metadata.")
    args = parser.parse_args()

    d = Path(args.dir)
    probs_csv = Path(args.probs)
    out_path = Path(args.out)
    manifest_path = Path(args.manifest)

    shocks = load_yaml_dir(d)
    flat = flatten_shocks(shocks)

    issues = []
    issues += validate_units(flat)
    issues += validate_against_probs(flat, probs_csv)

    if issues:
        print("VALIDATION WARNINGS:")
        for msg in issues:
            print(f" - {msg}")

    write_outputs(flat, out_path, manifest_path, probs_csv)


if __name__ == "__main__":
    main()