# Tools Directory

This directory contains tools for news ingestion, yield curve analysis, and ML model training.

## Structure

```
tools/
├── news_ingestion/          # News ingestion and yield curve prediction system
│   ├── README.md           # Main documentation
│   ├── SETUP.md            # Setup instructions
│   ├── DAILY_AUTOMATION.md # Daily automation guide
│   └── ...
│
└── ust_curve/              # U.S. Treasury yield curve builder
    ├── README.md           # Documentation
    └── llm/                # LLM integration and snapshots
```

## Quick Start

### News Ingestion System

See `news_ingestion/README.md` for full documentation.

**Setup:**
```bash
cd tools/news_ingestion
pip install -r requirements.txt
python3 -c "from db import init_db; init_db()"
```

**Run daily:**
```bash
python3 daily_pipeline.py
```

### Yield Curve Builder

See `ust_curve/README.md` for full documentation.

**Setup:**
```bash
cd tools/ust_curve
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Build snapshot:**
```bash
python3 llm/build_snapshots.py --core-module tools.ust_curve.curves 2025-11-06
```

## Integration

The two systems work together:
1. **Yield Curve Builder** creates daily snapshots of yield curve data
2. **News Ingestion** collects news and maps it to yield curve movements
3. **ML Models** learn the relationship between news and yield changes

## Requirements

- Python 3.7+
- See individual `requirements.txt` files in each subdirectory
- OpenAI API key (optional, for LLM features)

