# UST Yield Curve Dashboard

A modern web dashboard for visualizing the UST yield curve pipeline outputs, including:
- Today's yield curve vs yesterday
- Day-over-day changes
- Predicted vs actual yield movements
- Top news articles with impact analysis
- Risk flags and spread analysis

## Quick Start

### 1. Install Dependencies

```bash
cd web_dashboard
pip install -r requirements.txt
```

### 2. Run the Dashboard

```bash
python app.py
```

The dashboard will be available at `http://localhost:8888`

## Features

### Visualizations
- **Yield Curve Comparison**: Today vs yesterday's curve
- **Delta Chart**: Day-over-day changes by tenor
- **Prediction vs Actual**: Compare LLM predictions with actual movements
- **Key Spreads**: 2s10s, 2s30s, 5s30s spreads

### Data Display
- **Top 5 News Articles**: Most impactful articles ranked by confidence
- **Prediction Summary**: LLM-generated summary of expected curve movements
- **Risk Flags**: Inversion risks, flattening, belly humps, etc.

### Statistics
- Real-time yield levels (2y, 10y, 30y)
- Spread values (2s10s)
- Day-over-day changes in basis points

## API Endpoints

- `GET /api/curve/<date>` - Get yield curve snapshot
- `GET /api/analysis/<date>` - Get LLM analysis
- `GET /api/news/top/<date>` - Get top news articles
- `GET /api/stats/<date>` - Get summary statistics
- `GET /api/prediction/<date>` - Get prediction vs actual comparison
- `GET /api/dates` - Get list of available dates

## Architecture

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript with Chart.js
- **Data Sources**:
  - Yield curve snapshots: `tools/ust_curve/llm/snapshots/`
  - LLM analyses: `tools/news_ingestion/analyses/`
  - News database: `tools/news_ingestion/news.db`

## Customization

The dashboard can be customized by:
- Modifying `templates/index.html` for layout
- Updating `static/css/style.css` for styling
- Extending `static/js/dashboard.js` for functionality
- Adding new API endpoints in `app.py`

