# Quick Start Guide

## Installation

```bash
cd web_dashboard
pip install -r requirements.txt
```

## Running the Dashboard

```bash
# Option 1: Direct Python
python app.py

# Option 2: Using the script
./run.sh
```

Then open your browser to: **http://localhost:8888**

## What You'll See

### Main Dashboard Features

1. **Statistics Cards** (Top Row)
   - 2-Year, 10-Year, 30-Year yields
   - 2s10s spread
   - Day-over-day changes in basis points

2. **Interactive Charts**
   - **Yield Curve Comparison**: Today vs yesterday's curve
   - **Delta Chart**: Day-over-day changes by tenor (green = down, red = up)
   - **Prediction vs Actual**: Compare LLM predictions with actual movements
   - **Key Spreads**: Visual representation of 2s10s, 2s30s, 5s30s

3. **Content Sections**
   - **Top 5 News Articles**: Most impactful articles with summaries
   - **Prediction Summary**: LLM-generated analysis of expected curve movements
   - **Risk Flags**: Inversion risks, flattening warnings, etc.

### Date Selection

Use the date dropdown in the header to view data for different dates. The dashboard automatically loads the most recent available date.

## Troubleshooting

### No Data Showing

1. Make sure the pipeline has been run:
   ```bash
   # Run UST curve pipeline
   cd tools/ust_curve/llm
   ./daily.sh 2025-11-19
   
   # Run news ingestion pipeline
   cd tools/news_ingestion
   python daily_pipeline.py --date 2025-11-19
   ```

2. Check that data files exist:
   - `tools/ust_curve/llm/snapshots/curve_snapshot_YYYY-MM-DD.json`
   - `tools/news_ingestion/analyses/yield_impact_YYYY-MM-DD.json`
   - `tools/news_ingestion/news.db`

### Charts Not Loading

- Check browser console for JavaScript errors
- Ensure Chart.js is loading (check network tab)
- Verify API endpoints are returning data (check Network tab in browser dev tools)

### Port Already in Use

If port 8888 is busy, modify `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8889)  # Change port
```

## Customization

### Change Colors

Edit `static/css/style.css`:
- Primary color: `#667eea` (purple gradient)
- Success: `#27ae60` (green)
- Danger: `#e74c3c` (red)

### Add More Charts

1. Add canvas element to `templates/index.html`
2. Create chart function in `static/js/dashboard.js`
3. Call it from `loadData()` function

### Add New API Endpoints

Add routes to `app.py`:
```python
@app.route('/api/your-endpoint')
def your_endpoint():
    return jsonify({"data": "value"})
```

## Features Overview

✅ Real-time yield curve visualization
✅ Today vs yesterday comparison
✅ Prediction accuracy tracking
✅ Top news articles with impact
✅ Risk flag detection
✅ Responsive design (works on mobile)
✅ Interactive charts with Chart.js
✅ Date selection for historical data

Enjoy exploring your yield curve data! 📈

