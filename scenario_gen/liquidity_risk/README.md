2025 University of Chicago MSFM Project Lab  
Bank of America HQLA Risk Optimization

The scenario generation team is responsible for researching novel
risk scenarios and building the foundational ecosystem for the risk
agent. Features include:
- Developing models to forecast novel risk scenarios
- Determining probabilities for risk scenarios
- Identifying transmission channels
- Among other features

This project is led by **Amit Pandey** and **Adam Ashcraft** at Bank of America
and overseen by **Professor Amitabh Chaudhary** at the University of Chicago.

Student collaborators: **Aryaa Gunavante, Charles Benello, Josh Li, Togay Atmaca, Xiangchen Liu**.

---

# Liquidity Risk Scenario Generator

### 📘 Purpose
This module implements **Part 1 – Liquidity Scenario Generation** of the Bank of America HQLA Project Lab.  
Its goal is to use recent **market indicators** (MOVE, yield-curve slope, etc.) to:
1) Estimate the **probability** of near-term liquidity stress (30 / 90 days), and  
2) Feed those probabilities into an **LLM prompt** that produces a structured, human-readable  
   **Scenario Matrix** with five columns:
   ```
   Scenario | Description | Probability | Rationale | Impact Channels
   ```

The resulting table satisfies the brief’s deliverable:

> Use an AI model to generate plausible liquidity scenarios over a six-month horizon with probabilities, rationales, and impact channels (ΔLCR, ΔNSFR, haircuts, Level 1 vs 2A/2B composition, and NII).

---

### 📂 File Layout

```
liquidity_risk/
├── README.md                ← this file
├── __init__.py
├── load_data.py             ← loads MOVE, DGS2/10, (optional SURPRISE, EFFR)
├── features.py              ← builds rolling z-scores & 1-month changes
├── probs.py                 ← computes 30- and 90-day stress probabilities
├── prompt_template.py       ← LLM prompt template (Markdown table rules)
└── run.py                   ← driver script that prints the final prompt
```

Upstream shared code lives in [`scenario_gen/common`](../common):
* `scenario.py` – unified `Scenario` dataclass for Liquidity, IRR, Capital, etc.  
* `formatting.py` / `dump_matrix.py` – helpers to convert scenarios into a matrix.

---

### ⚙️ Data Inputs
Located in `/data/` at the repo root.

| File | Description | Notes |
|------|--------------|-------|
| `moveindex.xlsx` | Bloomberg MOVE Index (Treasury volatility) | Reader auto-detects `Date / PX_LAST`. |
| `DGS2.csv` | 2-year Treasury yield (FRED) | Used for 2s10s slope. |
| `DGS10.csv` | 10-year Treasury yield (FRED) | Used for 2s10s slope. |
| `surpriseindex.xlsx` (optional) | Macro-surprise index | Adds context for probability mapping. |
| `effr.xlsx` (optional) | Effective Fed Funds Rate | Optional funding-stress proxy. |

_All files assume the **first column is Date**. The MOVE reader is Bloomberg-export aware._

---

### 🔄 Workflow Overview

1. **`load_data.py`**  
   * Reads Excel/CSV files.  
   * Handles Bloomberg-style MOVE exports automatically.  
   * Builds a merged DataFrame of indicators + computed 2s10s spread (bps).

2. **`features.py`**  
   * Adds 1-month changes (`chg_21d`) and rolling z-scores (`z_252`).

3. **`probs.py`**  
   * Computes composite stress probabilities:  
     \[
     P_{90d} = \text{BASE} \times e^{(\text{sensitivity} \times \bar{z})}
     \]
     * Base = 25 %, Sensitivity = 0.6, Cap = 80 %.  
     * 30-day probability derived from independence assumption.

4. **`prompt_template.py`**  
   * Creates a clear LLM prompt that includes the indicators and probabilities.  
   * Enforces strict formatting rules so the model returns a clean Markdown table.

5. **`run.py`**  
   * Glue script that builds the prompt and prints it to stdout.  
   * Copy this prompt into ChatGPT (or any LLM) → it outputs the final table.

---

### ▶️ How to Run

From the repo root:

```bash
python3 -m scenario_gen.liquidity_risk.run
```

You’ll see output like: TODO automate this part with API waiting on prof

```
=== COPY THIS PROMPT INTO YOUR LLM === 
...
Indicators snapshot:
- MOVE=98.8 (z=-0.42, 1mΔ=-3.4)
- 2s10s slope=33.0 bps (z=2.2, 1mΔ=+28.0)
Use these probabilities:
- Liquidity Stress: 30d=8.0 %, 90d=20.0 %
...
=== EXPECTED RESULT: a 5-column Scenario Matrix (Markdown) ===
```

Paste that prompt into ChatGPT / Claude / Gemini → you’ll get a table like:

| Scenario | Description | Probability | Rationale | Impact Channels |
|-----------|-------------|--------------|------------|----------------|
| Base Case | Moderate volatility; contained funding spreads | 80.0 % | MOVE &lt; 100, curve stable. | ΔLCR ≈ 0; ΔNSFR ≈ 0; minor L2 haircuts. |
| Treasury Vol Spike | MOVE &gt; 115; auction tails ↑ | 8.0 % | MOVE trending up; term-premium repricing. | ΔLCR −2 pts; haircuts ↑ 10 %; NII ↓ . |

---

### 🧠 How this fits in the project
* **Scenario Generation (Part 1):**  Produces the human-readable matrix + probabilities.  
* **Scenario Impact (Part 2):**  Teams feed these scenarios into `hqla_risk_metrics` to quantify ΔLCR/ΔNSFR/ΔNII.  
* **Portfolio Optimization (Part 3):**  Uses those impacts for recommended HQLA trades.  
* **Daily Monitoring Agent (Part 4):**  The agent reads current MOVE/VIX/etc., recomputes probabilities, and flags scenario triggers.

---

### 🧩 Extending
- Add new indicators (e.g., VIX, OIS–UST spread) → edit `load_data.py` + `features.py`.  
- Tune `BASE_90D`, `SENSITIVITY`, or `CAP` in `probs.py` to recalibrate probabilities.  
- For reproducible runs, save the LLM’s output as  
  `scenario_gen/registry/YYYY-MM-DD/liquidity_matrix.csv`.

---

### ✅ Expected Deliverable
* A 5-column Scenario Matrix (Markdown / CSV) aligned with the brief.  
* Each row includes a probability and all key impact channels.  
* Optional: corresponding `Scenario` objects stored via `scenario_gen/common/scenario.py`.

---

ㅊ 다녀감
---