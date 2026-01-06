# Schemas

This doc captures the key data formats used across the repo so handoff is
consistent and discoverable.

## Portfolio upload CSV (agentic)
Location: `demo_csvs/test_portfolio.csv`

Columns:
- `level`: `1`, `2A`, or `2B` (maps to `Level1`, `Level2A`, `Level2B`)
- `type`: `Fixed`, `Floating`, or `Zero` (anything else is treated as zero coupon)
- `name`, `isin`: identifiers
- `issue_date`, `maturity_date`: `YYYY-MM-DD`
- `face_value`: numeric
- `quantity`: numeric
- `coupon`: numeric for fixed, blank for floating/zero
- `rating`: optional; blank or `-` means risk-free in pricing

Notes:
- The loader uses class name `Level{level}{type}`; the values above must match
  the naming in `agentic/src/hqla_instruments.py`.

## Yield curve upload CSV (agentic)
Location: `demo_csvs/test_yc.csv`

Columns:
- `tenor`: QuantLib period strings, e.g. `1M`, `3M`, `1Y`, `10Y`
- `rate`: numeric (decimal, e.g. `0.04` for 4%)

## Scenario list input (agentic `/scenario-rebalance/`)
The API accepts a JSON payload with a `scenarios` array. Each item may use any
of these keys (others are ignored):
- `Scenario` or `name`: scenario name
- `Probability` or `probability` or `p`: probability
- `Description` or `Rationale`: text used for metadata

Optional optimizer controls in the same payload:
`method`, `combine_mode`, `worst_by`, `top_k`, `custom_weights`,
`net_cash_outflow`, `min_lcr`, `max_lcr`, `target_duration`,
`duration_tolerance`, `allocation_buffer`.

## MAD scenario outputs (backend/mad_debate)
Config schema: `backend/mad_debate/config.yaml` defines required scenario keys
under the `schema:` block.

Main outputs:
- `backend/mad_debate/data/scenarios/out.jsonl` (default format)
  - JSON Lines: one scenario object per line.
- `/tmp/mad_scenarios.json` (dashboard expects this when `--format json` is used).
- `backend/mad_debate/data/scenarios/runs/<timestamp>/metadata.json`
  - `run_timestamp`, `run_directory`, `config_file`
  - `runs_requested`, `runs_completed`, `rounds_per_run`
  - `portfolio_name`, `shock_yaml`, `news_context`
  - `output_path`, `offline_sample_dir`
  - `prompts`: `debater_a`, `debater_b`, `judge`
- `backend/mad_debate/data/scenarios/transcript_run_<n>.jsonl`
  - per-message debate transcript for each run

## Scenario probabilities CSV (scenario_gen)
Location: `scenario_gen/combined_probabilities.csv`

Format:
- CSV indexed by `Date` (daily rows).
- Columns: `P30:<risk>/<scenario>` and `P90:<risk>/<scenario>`
  - Example: `P30:credit/mild`, `P90:liquidity/stress`,
    `P90:interest_rate/bear_steepen`
- Values are probabilities in `[0, 1]`.

## Shocks library (shocks)
Sources: `shocks/credit.yaml`, `shocks/liquidity.yaml`,
`shocks/interest_rate.yaml`

YAML format:
```
<scenario_name>:
  <variable_with_unit_suffix>: <numeric_value>
  ...
```

Compiled outputs:
- `shocks/shocks_resolved.json`: flattened map `risk/scenario` -> `{var: value}`
- `shocks/manifest.json`: metadata (`generated_at`, `hash_sha256`, `keys`, etc.)

## UST curve snapshots (tools/ust_curve)
Location: `tools/ust_curve/llm/snapshots/curve_snapshot_<DATE>.json`

Shape:
```
{
  "as_of": "YYYY-MM-DD",
  "prev": "YYYY-MM-DD",
  "today": {"zeros_pct": {...}, "spreads_pct": {...}},
  "prev_day": {"zeros_pct": {...}, "spreads_pct": {...}},
  "delta": {"zeros_pct": {...}, "spreads_pct": {...}}
}
```

## News ingestion database (tools/news_ingestion)
Database: `tools/news_ingestion/news.db`

Core tables (`schema.sql`):
- `articles`: URL, source, published_at, title, bucket, etc.
- `ingestion_runs`: daily ingestion metadata and status
- `yield_curve_daily`: JSON strings for curve levels and deltas
- `news_yield_training`: per-bucket training records

Factor tables (`schema_factors.sql`):
- `article_factors`, `daily_factor_scores`
- `linear_model_coefficients`, `linear_model_predictions`, `linear_model_intercepts`

## Yield impact analysis JSON (tools/news_ingestion)
Location: `tools/news_ingestion/analyses/yield_impact_<DATE>.json`

Shape:
```
{
  "date": "YYYY-MM-DD",
  "analysis": {
    "predictions": { "2y": {...}, "5y": {...}, "10y": {...}, "30y": {...} },
    "spreads": { "2s10s": {...}, "2s30s": {...} },
    "overall_summary": "..."
  },
  "news_summary": { "bucket": count, ... },
  "created_at": "ISO-8601 timestamp"
}
```

## Attribution report JSON (tools/news_ingestion)
Location: `tools/news_ingestion/attribution_analysis/attribution_report_<DATE>.json`

Shape:
```
{
  "date": "YYYY-MM-DD",
  "attribution": {
    "2Y": { "FACTOR": bps, ... },
    "10Y": { "FACTOR": bps, ... }
  },
  "visualizations": {
    "factor_attribution": "<path_to_png>",
    "factor_heatmap": "<path_to_png>"
  }
}
```
