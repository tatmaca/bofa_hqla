# Architecture

## System overview
The repo is a multi-component system built around three threads:
data pipelines (UST curve + news ingestion), scenario generation (MAD and
probability models), and portfolio/risk analytics (HQLA optimizer + metrics).
Two UI layers expose these outputs: a Next.js dashboard for scenario and
portfolio workflows, and a Flask dashboard + mobile app for yield curve views.

## Component map
- Data pipelines
  - `tools/ust_curve/`: builds daily UST zero curve snapshots and summaries.
  - `tools/news_ingestion/`: ingests news, buckets it, syncs curves, runs models,
    and produces attribution and prediction artifacts.
- Scenario generation
  - `backend/mad_debate/`: LLM-based debate engine that produces scenario JSON.
  - `scenario_gen/`: probabilistic scenario models producing `combined_probabilities.csv`.
  - `shocks/`: deterministic shock magnitudes compiled into `shocks_resolved.json`.
- Risk analytics
  - `agentic/`: HQLA instruments, portfolio optimizer, and FastAPI service.
  - `hqla_risk_metrics/`: LCR/NSFR/NII prototypes and scenario impact demos.
- Interfaces
  - `dashboard/`: Next.js UI for MAD + portfolio optimization.
  - `web_dashboard/`: Flask UI for yield curve + news analytics.
  - `mobile_app/`: Expo-based mobile UI for the yield curve dashboard.

## Data flow (high level)
```
tools/ust_curve
  -> tools/ust_curve/llm/snapshots/curve_snapshot_YYYY-MM-DD.json
  -> tools/news_ingestion (syncs snapshots into news.db)
  -> tools/news_ingestion/analyses + attribution_analysis
  -> web_dashboard + agentic (scenario curves, attribution views)

scenario_gen/combined_probabilities.csv
  -> shocks/shocks_resolved.json
  -> hqla_risk_metrics (scenario impacts)

backend/mad_debate (config.yaml + prompts)
  -> /tmp/mad_scenarios.json + backend/mad_debate/data/scenarios/*
  -> dashboard (Next.js UI reads outputs)
  -> agentic scenario rebalance endpoint (via dashboard)
```

## Runtime services and ports
- `agentic/src/api_server.py`: FastAPI service, typically on `http://localhost:8000`.
- `dashboard/`: Next.js app, typically on `http://localhost:3000`.
- `web_dashboard/`: Flask app, typically on `http://localhost:8888`.

## Key integrations
- The Next.js dashboard calls the FastAPI service for:
  - portfolio upload, yield curve upload, pricing, and scenario rebalancing.
- The dashboard's MAD routes run `backend/mad_debate/code/debate_scenarios.py`
  and read `/tmp/mad_scenarios.json` + `backend/mad_debate/temp.txt` for logs.
- `agentic` calls `tools/news_ingestion/generate_scenario_predictions.py` to
  combine scenario inputs with daily curve/news signals.
- The Flask dashboard reads snapshots and analyses from:
  - `tools/ust_curve/llm/snapshots/`
  - `tools/news_ingestion/analyses/`
  - `tools/news_ingestion/news.db`
- The mobile app uses the Flask dashboard API as its data source.

## Configuration and secrets
- `backend/mad_debate/config.yaml` controls MAD debate settings and schema.
- `tools/news_ingestion/news_config.yaml` controls feeds, rate limits, and LLM key.
- Set `OPENAI_API_KEY` (or config file) for LLM-based steps in MAD and news ingestion.
- Set `MAD_PYTHON` to override the Python interpreter used by the dashboard's MAD route.
