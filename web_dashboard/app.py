#!/usr/bin/env python3
"""
Web Dashboard for UST Yield Curve Pipeline
Displays yield curves, predictions, news articles, and analytics
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from flask import Flask, render_template, jsonify, request
import sqlite3

# Add parent directories to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "news_ingestion"))

app = Flask(__name__)

# Paths
UST_CURVE_DIR = ROOT / "tools" / "ust_curve" / "llm"
NEWS_DIR = ROOT / "tools" / "news_ingestion"
SNAPSHOTS_DIR = UST_CURVE_DIR / "snapshots"
ANALYSES_DIR = NEWS_DIR / "analyses"
NEWS_DB = NEWS_DIR / "news.db"

def get_latest_snapshot_date():
    """Get the most recent snapshot date."""
    if not SNAPSHOTS_DIR.exists():
        return None
    snapshots = sorted(SNAPSHOTS_DIR.glob("curve_snapshot_*.json"), reverse=True)
    if snapshots:
        date_str = snapshots[0].stem.replace("curve_snapshot_", "")
        return date_str
    return None

def load_snapshot(date_str):
    """Load yield curve snapshot for a date."""
    snapshot_path = SNAPSHOTS_DIR / f"curve_snapshot_{date_str}.json"
    if snapshot_path.exists():
        with open(snapshot_path) as f:
            return json.load(f)
    return None

def load_analysis(date_str):
    """Load LLM analysis for a date."""
    analysis_path = ANALYSES_DIR / f"yield_impact_{date_str}.json"
    if analysis_path.exists():
        with open(analysis_path) as f:
            return json.load(f)
    return None

def get_top_news_articles(date_str, limit=5):
    """Get top news articles for a date, ranked by impact."""
    if not NEWS_DB.exists():
        return []
    
    conn = sqlite3.connect(NEWS_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get articles for the date, ordered by bucket confidence
    articles = c.execute("""
        SELECT title, summary, source, url, bucket, bucket_confidence, published_at
        FROM articles
        WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
        AND title IS NOT NULL
        AND title != ''
        AND bucket IS NOT NULL
        ORDER BY bucket_confidence DESC, published_at DESC
        LIMIT ?
    """, (date_str, limit)).fetchall()
    
    conn.close()
    
    return [dict(row) for row in articles]

def get_news_by_bucket(date_str):
    """Get news articles grouped by bucket."""
    if not NEWS_DB.exists():
        return {}
    
    conn = sqlite3.connect(NEWS_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    articles = c.execute("""
        SELECT title, summary, source, url, bucket, bucket_confidence, published_at
        FROM articles
        WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
        AND title IS NOT NULL
        AND title != ''
        AND bucket IS NOT NULL
        ORDER BY bucket_confidence DESC
    """, (date_str,)).fetchall()
    
    conn.close()
    
    buckets = {}
    for row in articles:
        bucket = row["bucket"]
        if bucket not in buckets:
            buckets[bucket] = []
        buckets[bucket].append(dict(row))
    
    return buckets

@app.route('/')
def index():
    """Main dashboard page."""
    latest_date = get_latest_snapshot_date()
    if not latest_date:
        latest_date = date.today().isoformat()
    
    return render_template('index.html', latest_date=latest_date)

@app.route('/api/curve/<date_str>')
def api_curve(date_str):
    """Get yield curve data for a date."""
    snapshot = load_snapshot(date_str)
    if not snapshot:
        return jsonify({"error": "Snapshot not found"}), 404
    
    return jsonify(snapshot)

@app.route('/api/analysis/<date_str>')
def api_analysis(date_str):
    """Get LLM analysis for a date."""
    analysis = load_analysis(date_str)
    if not analysis:
        return jsonify({"error": "Analysis not found"}), 404
    
    return jsonify(analysis)

@app.route('/api/news/top/<date_str>')
def api_news_top(date_str):
    """Get top news articles for a date."""
    limit = request.args.get('limit', 5, type=int)
    articles = get_top_news_articles(date_str, limit)
    return jsonify({"articles": articles})

@app.route('/api/news/buckets/<date_str>')
def api_news_buckets(date_str):
    """Get news articles grouped by bucket."""
    buckets = get_news_by_bucket(date_str)
    return jsonify(buckets)

@app.route('/api/dates')
def api_dates():
    """Get list of available dates."""
    if not SNAPSHOTS_DIR.exists():
        return jsonify({"dates": []})
    
    snapshots = sorted(SNAPSHOTS_DIR.glob("curve_snapshot_*.json"), reverse=True)
    dates = [s.stem.replace("curve_snapshot_", "") for s in snapshots]
    return jsonify({"dates": dates})

@app.route('/api/prediction/<date_str>')
def api_prediction(date_str):
    """Get prediction vs actual comparison."""
    snapshot = load_snapshot(date_str)
    analysis = load_analysis(date_str)
    
    if not snapshot:
        return jsonify({"error": "Snapshot not found"}), 404
    
    if not analysis:
        return jsonify({"error": "Analysis not found"}), 404
    
    # Get actual changes from snapshot
    actual_deltas = snapshot.get("delta", {}).get("zeros_pct", {})
    
    # Get predictions from analysis
    predictions = analysis.get("analysis", {}).get("predictions", {})
    
    # Build comparison
    comparison = {}
    for tenor in ["2y", "5y", "10y", "30y"]:
        actual_key = tenor
        if actual_key in actual_deltas:
            actual_bps = actual_deltas[actual_key] * 100  # Convert to bps
            pred = predictions.get(tenor, {})
            pred_bps = pred.get("magnitude_bps", 0)
            pred_dir = pred.get("direction", "flat")
            
            # Adjust prediction sign based on direction
            if pred_dir == "down":
                pred_bps = -abs(pred_bps)
            elif pred_dir == "up":
                pred_bps = abs(pred_bps)
            else:
                pred_bps = 0
            
            comparison[tenor] = {
                "actual_bps": round(actual_bps, 2),
                "predicted_bps": round(pred_bps, 2),
                "error_bps": round(actual_bps - pred_bps, 2),
                "direction": pred_dir,
                "reasoning": pred.get("reasoning", "")
            }
    
    return jsonify(comparison)

@app.route('/api/stats/<date_str>')
def api_stats(date_str):
    """Get summary statistics for a date."""
    snapshot = load_snapshot(date_str)
    analysis = load_analysis(date_str)
    
    if not snapshot:
        return jsonify({"error": "Snapshot not found"}), 404
    
    today = snapshot.get("today", {})
    zeros = today.get("zeros_pct", {})
    spreads = today.get("spreads_pct", {})
    delta = snapshot.get("delta", {})
    delta_zeros = delta.get("zeros_pct", {})
    
    # Calculate key metrics
    stats = {
        "date": date_str,
        "yields": {
            "2y": zeros.get("2y", 0),
            "10y": zeros.get("10y", 0),
            "30y": zeros.get("30y", 0)
        },
        "spreads": {
            "2s10s": spreads.get("2s10s", 0),
            "2s30s": spreads.get("2s30s", 0)
        },
        "changes_bps": {
            "2y": round(delta_zeros.get("2y", 0) * 100, 2),
            "10y": round(delta_zeros.get("10y", 0) * 100, 2),
            "30y": round(delta_zeros.get("30y", 0) * 100, 2)
        },
        "risks": snapshot.get("risks", []),
        "has_prediction": analysis is not None
    }
    
    if analysis:
        stats["prediction_summary"] = analysis.get("analysis", {}).get("overall_summary", "")
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)

