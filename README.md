# Bank of America HQLA Risk Optimization (UChicago MSFM Project Lab)

This repository contains the project lab prototype for an AI monitoring agent
and supporting analytics for HQLA risk optimization. It spans data ingestion,
scenario generation, risk metrics, portfolio optimization, and multiple user
interfaces.

Core capabilities include:
- Ingest real-time market, macro, and news data
- Generate portfolio reallocation suggestions
- Simulate risk events and expected portfolio impacts
- Produce dashboards and attribution analytics

## Docs
- docs/ARCHITECTURE.md
- docs/SCHEMAS.md
- docs/RUNBOOK.md

## Repository map
- agentic/                      HQLA portfolio models, optimizer, and FastAPI service
- backend/mad_debate/           Multi-agent debate scenario generator (MAD)
- tools/                        UST curve builder + news ingestion pipeline
- scenario_gen/                 Scenario probability generation
- shocks/                       Scenario shock library and compiler
- hqla_risk_metrics/            Liquidity and profitability metrics prototypes
- dashboard/                    Next.js UI for scenario gen + optimizer
- web_dashboard/                Flask yield curve dashboard
- mobile_app/                   React Native/Expo mobile app
- irr_data/, new_credit_data/   Data sources and feature inputs
- demo_csvs/                    Example portfolio and curve CSVs

## Quick start (local)
1) Data pipelines (required for dashboards and analytics):
   - `cd tools/ust_curve`
   - `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
   - `./llm/daily.sh YYYY-MM-DD`
   - `cd ../news_ingestion`
   - `pip install -r requirements.txt`
   - `python3 -c "from db import init_db; init_db()"` (once)
   - `python3 daily_pipeline.py --date YYYY-MM-DD`

2) Agentic API (FastAPI, required for Next.js dashboard optimizer):
   - `pip install fastapi uvicorn pandas numpy QuantLib openai`
   - `uvicorn agentic.src.api_server:app --reload --port 8000`

3) Next.js dashboard:
   - `cd dashboard && npm install && npm run dev`
   - Open `http://localhost:3000`

4) Yield curve web dashboard:
   - `cd web_dashboard && pip install -r requirements.txt && python app.py`
   - Open `http://localhost:8888`

5) Mobile app (optional):
   - `cd mobile_app && npm install && npm start`

6) MAD scenario generation (optional):
   - `cd backend/mad_debate && pip install -r requirements.txt`
   - `python code/debate_scenarios.py --config config.yaml --runs 5 --format json --out /tmp/mad_scenarios.json`

See `docs/RUNBOOK.md` for full procedures, environment variables, and troubleshooting.

## Key outputs
- `tools/ust_curve/llm/snapshots/curve_snapshot_YYYY-MM-DD.json`
- `tools/news_ingestion/news.db`
- `tools/news_ingestion/analyses/yield_impact_YYYY-MM-DD.json`
- `scenario_gen/combined_probabilities.csv`
- `shocks/shocks_resolved.json`
- `backend/mad_debate/data/scenarios/` and `/tmp/mad_scenarios.json`

## Project context
This project is led by Amit Pandey and Adam Ashcraft at Bank of America
and overseen by Professor Amitabh Chaudhary at the University of Chicago.

The student collaborators on this project are Aryaa Gunavante, Charles
Benello, Josh Li, Togay Atmaca, and Xiangchen Liu.
