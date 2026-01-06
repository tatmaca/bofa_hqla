# Runbook

## Prerequisites
- Python 3.x and pip
- Node.js (for `dashboard/` and `mobile_app/`)
- Optional: `OPENAI_API_KEY` for LLM features in MAD and news ingestion
- Ports: `3000` (Next.js), `8000` (FastAPI), `8888` (Flask)
- QuantLib for Python (used by `agentic/`)

## One-time setup
1) UST curve environment
```
cd tools/ust_curve
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2) News ingestion database
```
cd tools/news_ingestion
pip install -r requirements.txt
python3 -c "from db import init_db; init_db()"
```

3) Node dependencies
```
cd dashboard && npm install
cd ../mobile_app && npm install
```

## Daily data pipeline
1) Build UST curve snapshot
```
cd tools/ust_curve
./llm/daily.sh YYYY-MM-DD
```

2) Run news ingestion + model updates
```
cd tools/news_ingestion
python3 daily_pipeline.py --date YYYY-MM-DD
```

Outputs to verify:
- `tools/ust_curve/llm/snapshots/curve_snapshot_YYYY-MM-DD.json`
- `tools/news_ingestion/news.db`
- `tools/news_ingestion/analyses/yield_impact_YYYY-MM-DD.json`
- `tools/news_ingestion/attribution_analysis/attribution_report_YYYY-MM-DD.json`

## Scenario probability + shocks pipeline
1) Generate probabilities
```
python -m scenario_gen.run_all_probs
```

2) Compile shocks (validates against probabilities)
```
python shocks/schema.py --probs scenario_gen/combined_probabilities.csv --out shocks/shocks_resolved.json
```

## MAD scenario generation (debate)
```
cd backend/mad_debate
pip install -r requirements.txt
export OPENAI_API_KEY=...   # required for live runs
python code/debate_scenarios.py --config config.yaml --runs 5 --format json --out /tmp/mad_scenarios.json
```

Notes:
- The Next.js dashboard expects `/tmp/mad_scenarios.json`.
- Offline runs can use `--offline-sample <dir>` or `MAD_OFFLINE_SAMPLE_DIR`.
- Prompts can be overridden via `MAD_PROMPT_DEBATER_A`, `MAD_PROMPT_DEBATER_B`,
  and `MAD_PROMPT_JUDGE`.

## Start services (local)
1) Agentic FastAPI service (from repo root)
```
pip install fastapi uvicorn pandas numpy QuantLib openai
uvicorn agentic.src.api_server:app --reload --port 8000
```

2) Next.js dashboard
```
cd dashboard
npm run dev
```
Open `http://localhost:3000`

3) Yield curve web dashboard
```
cd web_dashboard
pip install -r requirements.txt
python app.py
```
Open `http://localhost:8888`

4) Mobile app (optional)
```
cd mobile_app
npm start
```
Update `API_BASE` in `mobile_app/App.js` when testing on a device.

## Operational checks
- FastAPI health: upload a portfolio + yield curve, then call `/price-portfolio/`.
- Dashboard: load `http://localhost:3000` and run a scenario generation or optimizer flow.
- Web dashboard: select a date and verify charts render (requires data in snapshots/analyses).

## Common issues
- Missing LLM key: set `OPENAI_API_KEY` or add to `tools/news_ingestion/news_config.yaml`.
- No data in dashboards: run the daily pipelines first; confirm snapshot/analysis files exist.
- `/tmp/mad_scenarios.json` missing: run the MAD script or set `--out` path to match.
- QuantLib import errors: install the Python bindings for QuantLib on your OS.
- Port already in use: adjust ports in `uvicorn`, `dashboard`, or `web_dashboard/app.py`.

## Logs and artifacts
- `tools/news_ingestion/logs/`: daily pipeline logs
- `tools/ust_curve/llm/curve_daily_log.md`: daily curve summaries
- `backend/mad_debate/logs/`: MAD run logs
- `backend/mad_debate/data/scenarios/runs/<timestamp>/`: per-run artifacts and metadata

## Known gaps
- `hqla_risk_metrics/demo.py` and `demo_scenarios.py` import modules (`assets`, `portfolio`)
  that are not present in `agentic/src`. Update imports or add missing modules before use.
