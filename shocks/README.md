# Shocks Library

Deterministic shock magnitudes for each risk scenario, maintained in YAML and compiled into a single machine-readable JSON for downstream use.  
This library complements the probability outputs in `scenario_gen/combined_probabilities.csv`.

---

## Purpose

- Provide a version-controlled, auditable source of **scenario shocks** (“what moves by how much if the scenario occurs”).
- Keep probability estimation (in `scenario_gen/`) separate from policy choices about shock magnitudes.
- Enable downstream modules (e.g., `hqla_risk_metrics`) to compute ΔLCR, ΔNSFR, ΔNII using a validated, consistent input.

---

## Directory Layout

```
shocks/
├── README.md                 ← this file
├── credit.yaml               ← credit spread shocks
├── liquidity.yaml            ← liquidity market/funding shocks
├── rates.yaml                ← interest-rate curve shocks
├── schema.py                 ← loader + validator + compiler
├── shocks_resolved.json      ← compiled flattened shocks (generated)
└── manifest.json             ← metadata for audits (generated)
```

---

## Naming & Units

- Scenario keys follow `<risk>/<scenario>` identifiers from `scenario_gen/combined_probabilities.csv`  
  (e.g., `credit/severe`, `liquidity/stress`, `interest_rate/bear_steepen`).

- Variable naming uses explicit unit suffixes:
  - `*_bp`, `*_bps` → basis points (e.g., `IG_OAS_bp`, `DGS10_bp`)
  - `*_pts` → index points (e.g., `MOVE_pts`)
  - `*_pct` → percent change (optional)

- By convention, positive values represent adverse shocks for that risk type.

---

## Usage

```
python shocks/schema.py \
  --probs scenario_gen/combined_probabilities.csv \
  --out shocks/shocks_resolved.json
```

Outputs:
- `shocks_resolved.json` → flattened, machine-readable shock dictionary  
- `manifest.json` → metadata (timestamp, hash, scenario list)

---

## Integration

Downstream modules such as `hqla_risk_metrics` combine:
- `scenario_gen/combined_probabilities.csv` → scenario probabilities  
- `shocks/shocks_resolved.json` → scenario magnitudes  

to produce portfolio impacts under consistent scenario definitions.

ㅊ 다녀감