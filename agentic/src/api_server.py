# api_server.py
import base64
import datetime as dt
import datetime as _dt
import io
import json
import os
import sys
import tempfile
from pathlib import Path

import hqla_instruments as HQLA
import numpy as np
import pandas as pd
import QuantLib as ql
from fastapi import Body, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from hqla_portfolio import Portfolio

sys.path.append(str(Path(__file__).resolve().parents[2] / "tools" / "news_ingestion"))

from typing import List, Optional

from bucket_news import get_bucket_counts
from db import get_conn
from generate_scenario_predictions import generate_all_scenario_curves
from pydantic import BaseModel
from scenario_rebalancing import Scenario as RebalanceScenario
from scenario_rebalancing import ScenarioRebalancingEngine


# module-level globals
portfolio = None
base_curve_handle = None
base_curve = None
base_curve_up = None
base_curve_down = None
survival_curves = {}
survival_curves_up = {}
survival_curves_down = {}
base_curve_tenor_strs = []
realized_portfolio_summary = None


class NewsArticle(BaseModel):
    title: str
    bucket: str
    bucketLabel: str
    summary: Optional[str]
    source: Optional[str]
    url: Optional[str]


class NewsBucket(BaseModel):
    name: str
    label: str
    count: int
    uncovered: bool
    description: str
    coverage: list[str]
    topHeadlines: list[dict]


class NewsSummary(BaseModel):
    headline: str
    detail: str
    reason: Optional[str]
    date: str
    shouldUpdate: bool


class NewsMonitorResponse(BaseModel):
    summary: NewsSummary
    buckets: List[NewsBucket]
    articles: List[NewsArticle]
    metadata: dict


app = FastAPI()
portfolio = Portfolio()
_last_portfolio_df = None

# Global placeholder for the base curve
base_curve_tenor_strs = None
realized_portfolio_summary = None
_last_rebalance = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve attribution PNG/JSON as static for convenience
_repo_root = Path(__file__).resolve().parents[2]
_attr_dir = _repo_root / "tools" / "news_ingestion" / "attribution_analysis"
_news_db_path = _repo_root / "news.db"
if _attr_dir.exists():
    app.mount(
        "/attribution-static",
        StaticFiles(directory=_attr_dir),
        name="attribution-static",
    )

ALLOWED_IMAGE_MODES = {"report", "heatmap", "all", "none"}


def _classify_image(p: Path) -> str:
    name = p.name.lower()
    if "heatmap" in name:
        return "heatmap"
    if "attribution" in name:
        return "report"
    return "other"


def _filter_images(pngs: list[Path], image_mode: str) -> list[Path]:
    if image_mode == "all":
        return pngs
    if image_mode == "none":
        return []
    return [p for p in pngs if _classify_image(p) == image_mode]


def _ensure_news_db_env() -> Path:
    """Ensure NEWS_DB_PATH points to the repo-level news.db and return the path."""
    os.environ.setdefault("NEWS_DB_PATH", str(_news_db_path))
    return _news_db_path


def _current_net_cash_outflow(default: float = 1_000_000_000.0) -> float:
    """Return net cash outflow if set on portfolio; fallback to default."""
    try:
        return float(getattr(portfolio, "net_cash_outflow", default))
    except Exception:
        return default


def _hydrate_portfolio_from_df(df: pd.DataFrame):
    """Construct Portfolio from a DataFrame (shared by upload + rehydrate)."""
    global portfolio
    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today
    soft_rate = 5 * 1e-2
    day_count_floater = ql.Actual360()
    rate_handle = ql.QuoteHandle(ql.SimpleQuote(soft_rate))
    sofr_term_structure = ql.FlatForward(
        today, rate_handle, day_count_floater, ql.Continuous
    )
    sofr_term_structure_handle = ql.YieldTermStructureHandle(sofr_term_structure)
    sofr_index = ql.Sofr(sofr_term_structure_handle)
    sofr_index.clearFixings()
    calendar = sofr_index.fixingCalendar()

    # Reset all categories
    for cat in portfolio.assets:
        portfolio.assets[cat] = []

    for _, row in df.iterrows():
        cls = getattr(HQLA, f"Level{row['level']}{row['type']}")
        issue = ql.DateParser.parseISO(row["issue_date"])
        maturity = ql.DateParser.parseISO(row["maturity_date"])
        grade = row.get("rating", "-")
        grade = "-" if pd.isna(grade) else grade

        kwargs = {
            "issue_date": issue,
            "maturity_date": maturity,
            "face_value": float(row.get("face_value", 100)),
            "quantity": float(row.get("quantity", 0)),
            "name": row.get("name", ""),
            "isin": row.get("isin", ""),
            "grade": grade,
            "isRisky": False if grade == "-" else True,
        }

        if row["type"] == "Fixed":
            kwargs["coupons"] = [float(row["coupon"])]
            inst = cls(**kwargs)
            inst.build_bond()
        elif row["type"] == "Floating":
            inst = cls(**kwargs)
            inst.build_bond(index=sofr_index)
            for dt in inst.schedule:
                adj_date = calendar.adjust(dt, ql.Preceding)
                sofr_index.addFixing(adj_date, soft_rate)
        else:  # Zero coupon
            inst = cls(**kwargs)
            inst.build_bond()

        portfolio.add_instrument(inst)


def _load_analysis_for_today():
    import datetime as dt
    from pathlib import Path
    db_path = _ensure_news_db_env()

    from db import get_conn

    today = dt.date.today().isoformat()

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM articles
            WHERE DATE(fetched_at) = DATE(?)
            """,
            (today,),
        ).fetchall()

    return [dict(row) for row in rows] if rows else None


def _top_factors_with_articles(
    date: str, top_factors: int = 3, top_articles: int = 3
) -> list[dict]:
    """Return top factors by absolute daily score with their top articles."""
    _ensure_news_db_env()
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT factor_name, factor_score, total_articles
            FROM daily_factor_scores
            WHERE date = ?
            ORDER BY ABS(factor_score) DESC
            LIMIT ?
            """,
            (date, top_factors),
        ).fetchall()

        factors = []
        for r in rows:
            factor_name = r["factor_name"]
            articles = conn.execute(
                """
                SELECT
                    a.title,
                    a.source,
                    a.url,
                    a.published_at,
                    af.intensity,
                    af.confidence,
                    (af.intensity * af.confidence) AS score
                FROM article_factors af
                JOIN articles a ON af.article_id = a.id
                WHERE af.date = ?
                  AND af.factor_name = ?
                ORDER BY ABS(score) DESC
                LIMIT ?
                """,
                (date, factor_name, top_articles),
            ).fetchall()

            factors.append(
                {
                    "name": factor_name,
                    "score": r["factor_score"],
                    "total_articles": r["total_articles"],
                    "articles": [dict(a) for a in articles],
                }
            )
    return factors


def _load_attribution_payload(
    target_date: str, image_mode: str, embed_images: bool, request: Request
):
    """Load attribution JSON and attach chart links/base64 per options."""
    report_path = (
        _repo_root
        / "tools"
        / "news_ingestion"
        / "attribution_analysis"
        / f"attribution_report_{target_date}.json"
    )

    if not report_path.exists():
        return None, JSONResponse(
            status_code=404,
            content={
                "error": f"No attribution report found for {target_date}",
                "path": str(report_path),
                "hint": "Run daily_pipeline.py or generate the report first.",
            },
        )

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pngs = (
            sorted(_attr_dir.glob(f"*{target_date}*.png")) if _attr_dir.exists() else []
        )
        pngs = _filter_images(pngs, image_mode)

        base_url = str(request.base_url).rstrip("/")
        data["chart_files"] = [f"/attribution-static/{p.name}" for p in pngs]
        data["chart_urls"] = [f"{base_url}/attribution-static/{p.name}" for p in pngs]

        if pngs:
            images = []
            for p in pngs:
                item = {
                    "name": p.name,
                    "type": _classify_image(p),
                    "url": f"/attribution-static/{p.name}",
                    "abs_url": f"{base_url}/attribution-static/{p.name}",
                }
                if embed_images:
                    try:
                        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
                        item["data_uri"] = f"data:image/png;base64,{b64}"
                    except Exception as e:
                        item["error"] = str(e)
                images.append(item)
            data["chart_images"] = images
        return data, None
    except Exception as e:
        return None, JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to read attribution report: {e}",
                "path": str(report_path),
            },
        )


@app.post("/upload-portfolio/")
async def upload_portfolio(file: UploadFile):
    """Upload portfolio CSV and build instrument objects."""
    global portfolio, base_curve_handle, base_curve, base_curve_up, base_curve_down
    global survival_curves, survival_curves_up, survival_curves_down, _last_portfolio_df

    # Full reset
    portfolio = Portfolio()
    base_curve = None
    base_curve_handle = None
    base_curve_up = None
    base_curve_down = None
    survival_curves = {}
    survival_curves_up = {}
    survival_curves_down = {}

    df = pd.read_csv(file.file)
    _hydrate_portfolio_from_df(df)
    _last_portfolio_df = df.copy()

    return {"status": "Portfolio created", "count": len(df)}


@app.post("/upload-yield-curve/")
async def upload_yield_curve(file: UploadFile = None, request: Request = None):
    """
    Upload a yield curve CSV.
    Expected columns: 'tenor' (e.g., '1Y'), 'rate' (decimal or %)
    """
    global base_curve
    global base_curve_handle
    global base_curve_up
    global base_curve_down
    global survival_curves
    global survival_curves_up
    global survival_curves_down
    global base_curve_tenor_strs
    base_curve_tenor_strs = []

    # Reset all old curve objects before constructing new ones
    base_curve = None
    base_curve_handle = None
    base_curve_up = None
    base_curve_down = None
    survival_curves = {}
    survival_curves_up = {}
    survival_curves_down = {}

    if file:
        df = pd.read_csv(file.file)
    else:
        try:
            payload = await request.json()
            df = pd.DataFrame(payload)
            print(df)
        except Exception as e:
            return JSONResponse(
                status_code=400, content={"error": f"Invalid input: {e}"}
            )

    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today

    dates = [today]
    tenors = []
    rates = [0.0]

    for _, row in df.iterrows():
        tenor = row["tenor"].strip()
        rate = float(row["rate"])
        # Store tenor strings for plotting purposes
        base_curve_tenor_strs.append(tenor)
        # Convert tenor string to QuantLib period
        ql_period = ql.PeriodParser.parse(tenor)
        tenors.append(ql_period)
        dt = today + ql_period
        dates.append(dt)
        rates.append(rate)

    # Build zero curve
    base_curve = ql.CubicZeroCurve(dates, rates, ql.Actual360(), ql.TARGET())
    base_curve_handle = ql.YieldTermStructureHandle(base_curve)

    bump = 0.0001
    interest_rate_bump_up = ql.QuoteHandle(ql.SimpleQuote(bump))
    interest_rate_bump_down = ql.QuoteHandle(ql.SimpleQuote(-bump))

    base_curve_up_handle = ql.ZeroSpreadedTermStructure(
        base_curve_handle, interest_rate_bump_up
    )
    base_curve_up = ql.YieldTermStructureHandle(base_curve_up_handle)
    base_curve_down_handle = ql.ZeroSpreadedTermStructure(
        base_curve_handle, interest_rate_bump_down
    )
    base_curve_down = ql.YieldTermStructureHandle(base_curve_down_handle)

    # Build corresponding hazard rate curves
    tenors = [ql.Period(y, ql.Years) for y in [1, 2, 3, 5, 7, 10]]
    cds_spreads = {
        "AAA": [10, 12, 13, 17, 18, 22],
        "AA": [15, 17, 18, 25, 28, 35],
        "A": [25, 28, 30, 45, 50, 65],
        "BBB": [50, 55, 58, 85, 95, 110],
    }

    recovery_rates = {
        "AAA": 0.741,
        "AA": 0.621,
        "A": 0.457,
        "BBB": 0.381,
    }

    survival_curves = {}
    survival_curves_up = {}
    survival_curves_down = {}
    crv_dicts = [survival_curves, survival_curves_up, survival_curves_down]
    changes = [0, bump, -bump]
    for rating in recovery_rates.keys():
        for change, crv_dict in zip(changes, crv_dicts):
            rr = recovery_rates[rating]
            cds_spread = cds_spreads[rating]
            cds_helpers = [
                ql.SpreadCdsHelper(
                    (cds / 1000.0) + change,
                    tenor,
                    1,
                    ql.TARGET(),
                    ql.Quarterly,
                    ql.Following,
                    ql.DateGeneration.TwentiethIMM,
                    ql.Actual360(),
                    rr,
                    base_curve_handle,
                )
                for (cds, tenor) in zip(cds_spread, tenors)
            ]
            hazard_rate_curve = ql.PiecewiseFlatHazardRate(
                today, cds_helpers, ql.Actual360()
            )
            hazard_rate_curve.enableExtrapolation()
            crv_dict[rating] = ql.DefaultProbabilityTermStructureHandle(
                hazard_rate_curve
            )

    return {"status": "Yield curve uploaded", "points": len(dates)}


@app.get("/yield-curve/current")
async def get_current_curve():
    if base_curve is None:
        return JSONResponse(
            status_code=400, content={"error": "No yield curve uploaded"}
        )

    if base_curve_tenor_strs is None:
        return JSONResponse(status_code=500, content={"error": "Tenor list missing"})

    today = ql.Date.todaysDate()
    dc = base_curve.dayCounter()

    points = []

    for tenor_str in base_curve_tenor_strs:
        ql_period = ql.PeriodParser.parse(tenor_str)
        dt = today + ql_period

        z = base_curve.zeroRate(dt, dc, ql.Continuous).rate()
        z = np.round(z, 4)

        points.append({"tenor": tenor_str, "rate": z})
    print(points)

    return {"curve": points}


@app.get("/price-portfolio/")
async def price_portfolio(is_scenario: bool = False):
    """Return current portfolio prices using base curve."""
    if not any(portfolio.assets.values()):
        return JSONResponse(
            status_code=400, content={"error": "No instruments in portfolio"}
        )

    if not base_curve_handle:
        return JSONResponse(
            status_code=400, content={"error": "No yield curve uploaded"}
        )

    global realized_portfolio_summary

    try:
        # --- Reprice all instruments using the portfolio method ---
        portfolio.update_prices(
            base_curve_handle,
            base_curve_up,
            base_curve_down,
            survival_curves,
            survival_curves_up,
            survival_curves_down,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Pricing failed: {exc.__class__.__name__}: {exc}"},
        )

    # --- Build summary for API response ---
    summary = []
    for group in portfolio.assets.values():
        for inst in group:
            summary.append(
                {
                    "name": inst.name,
                    "isin": inst.isin,
                    "coupon": getattr(inst, "coupons", "Floating"),
                    "rating": inst.grade,
                    "category": portfolio._category(inst),
                    "class": inst.__class__.__name__,
                    "dirty_price": inst.dirty_price,
                    "clean_price": inst.clean_price,
                    "ytm": inst.ytm,
                    "quantity": inst.quantity,
                    "dv01": inst.dv01,
                    "cs01": inst.cs01 if inst.cs01 != None else "-",
                    "duration": inst.duration,
                    "convexity": inst.convexity,
                }
            )

    if not is_scenario:
        realized_portfolio_summary = summary
        return {"assets": summary, "status": "priced"}
    else:
        return {
            "realized": realized_portfolio_summary,
            "scenario": summary,
            "status": "scenario_priced",
        }


# ------------------------
# Scenario rebalancing endpoint
# ------------------------
@app.post("/scenario-rebalance/")
async def scenario_rebalance(request: Request):
    """Run full scenario rebalancing using uploaded portfolio + current curve."""
    global portfolio
    if not any(portfolio.assets.values()):
        # Try to rehydrate from last uploaded CSV to survive dev reloads
        global _last_portfolio_df
        if _last_portfolio_df is not None:
            _hydrate_portfolio_from_df(_last_portfolio_df)
        if not any(portfolio.assets.values()):
            counts = {k: len(v) for k, v in portfolio.assets.items()}
            return JSONResponse(
                status_code=400,
                content={
                    "error": "No instruments in portfolio",
                    "detail": {
                        "counts": counts,
                        "hint": "Upload a portfolio CSV via /upload-portfolio before running the optimizer.",
                    },
                },
            )
    if not base_curve_handle:
        return JSONResponse(
            status_code=400, content={"error": "No yield curve uploaded"}
        )

    payload = await request.json()
    scenarios = payload.get("scenarios") or []
    if not isinstance(scenarios, list) or not scenarios:
        return JSONResponse(status_code=400, content={"error": "No scenarios provided"})

    # Params
    net_cash_outflow = float(
        payload.get("net_cash_outflow") or _current_net_cash_outflow()
    )
    min_lcr = float(payload.get("min_lcr") or 1.0)
    max_lcr = float(payload.get("max_lcr") or 1.5)
    target_duration = payload.get("target_duration")
    duration_tolerance = float(payload.get("duration_tolerance") or 0.5)
    allocation_buffer = float(payload.get("allocation_buffer") or 0.02)
    method = payload.get("method") or "mean_lexicographic"
    combine_mode = payload.get("combine_mode") or "probability_weighted"
    worst_by = payload.get("worst_by") or "expected_return"
    top_k = int(payload.get("top_k") or 2)
    custom_weights = payload.get("custom_weights") or None

    engine = ScenarioRebalancingEngine(
        base_portfolio=portfolio,
        net_cash_outflow=net_cash_outflow,
        min_lcr=min_lcr,
        max_lcr=max_lcr,
        target_duration=target_duration,
        duration_tolerance=duration_tolerance,
        allocation_buffer=allocation_buffer,
    )

    # Add scenarios
    for sc in scenarios:
        try:
            name = sc.get("Scenario") or sc.get("name") or "Scenario"
            prob = float(
                sc.get("Probability") or sc.get("probability") or sc.get("p") or 0.0
            )
            if prob > 1:
                prob = prob / 100.0
            desc = sc.get("Description") or sc.get("Rationale") or ""
            scen = RebalanceScenario(
                name=name,
                yield_curve_handle=base_curve_handle,
                sofr_handle=None,
                probability=prob,
                metadata={"description": desc},
            )
            engine.add_scenario(scen)
        except Exception as exc:
            return JSONResponse(
                status_code=400, content={"error": f"Bad scenario: {exc}"}
            )

    # Run rebalancing
    try:
        engine.run_rebalancing(method=method)
        engine.combine_portfolios(
            mode=combine_mode,
            worst_by=worst_by,
            top_k=top_k,
            custom_weights=custom_weights,
        )
        combined_df = engine.build_combined_dataframe().to_dict(orient="records")
    except Exception as exc:
        return JSONResponse(
            status_code=500, content={"error": f"Rebalance failed: {exc}"}
        )

    # Collect outputs
    scenario_results = {}
    for name, info in engine.results.items():
        scenario_results[name] = {
            "probability": info["scenario"].probability,
            "metrics": info["metrics"],
            "weights": info["weights"].tolist(),
            "per_asset": info["df"].to_dict(orient="records"),
            "description": info["scenario"].metadata.get("description", ""),
        }

    return {
        "method": method,
        "combine_mode": combine_mode,
        "net_cash_outflow": net_cash_outflow,
        "scenario_count": len(engine.results),
        "scenario_results": scenario_results,
        "combined_portfolio": combined_df,
        "final_weights": (
            engine.final_portfolio_weights.tolist()
            if engine.final_portfolio_weights is not None
            else []
        ),
    }


@app.get("/attribution/html")
async def get_attribution_html(
    request: Request,
    date: str | None = None,
    image_mode: str = "all",
    embed_images: bool = False,
):
    """Return attribution HTML as a downloadable file (helps Swagger show an open button)."""
    try:
        target_date = date or _dt.date.today().isoformat()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid date format, expected YYYY-MM-DD"},
        )

    image_mode = (image_mode or "all").lower()
    if image_mode not in ALLOWED_IMAGE_MODES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"image_mode must be one of {sorted(ALLOWED_IMAGE_MODES)}"
            },
        )

    data, err = _load_attribution_payload(
        target_date=target_date,
        image_mode=image_mode,
        embed_images=embed_images,
        request=request,
    )
    if err:
        return err

    rows = []
    rows.append("<h2>Attribution Report</h2>")
    rows.append(f"<p>Date: {target_date}</p>")
    rows.append("<h3>Charts</h3>")
    charts = data.get("chart_images") or []
    if charts:
        rows.append("<ul>")
        for item in charts:
            link = item.get("abs_url") or item.get("url")
            name = item.get("name", link)
            rows.append(
                f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">Open {name}</a></li>'
            )
        rows.append("</ul>")
    else:
        rows.append("<p>No charts found for this date.</p>")
    rows.append("<h3>Numbers (JSON)</h3>")
    rows.append("<pre>")
    rows.append(json.dumps(data, indent=2))
    rows.append("</pre>")
    html = "\n".join(rows)

    headers = {
        "Content-Disposition": f'attachment; filename="attribution_{target_date}.html"'
    }
    return HTMLResponse(content=html, media_type="text/html", headers=headers)


@app.get("/attribution/json")
async def get_attribution_json(
    request: Request,
    date: str | None = None,
    image_mode: str = "all",
    embed_images: bool = False,
):
    """Return attribution payload as JSON (with chart urls / optional base64)."""
    try:
        target_date = date or _dt.date.today().isoformat()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid date format, expected YYYY-MM-DD"},
        )

    image_mode = (image_mode or "all").lower()
    if image_mode not in ALLOWED_IMAGE_MODES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"image_mode must be one of {sorted(ALLOWED_IMAGE_MODES)}"
            },
        )

    data, err = _load_attribution_payload(
        target_date=target_date,
        image_mode=image_mode,
        embed_images=embed_images,
        request=request,
    )
    if err:
        return err

    return JSONResponse(content={"date": target_date, **data})


@app.post("/generate-scenario-curves/")
async def generate_scenario_curves_endpoint(
    jsonl_input: str = Body(..., description="Scenario JSONL content"),
    combine_with_news: bool = Body(
        False, description="Combine scenario factors with news"
    ),
    date: str = Body(None, description="Date string YYYY-MM-DD, defaults to today"),
):
    """
    Receives JSONL input for scenarios from the frontend and generates predicted curves.
    """
    print("ENTERING CURVE GENERATOR")

    target_date = date if date else dt.date.today().isoformat()

    # Write the JSONL content to a temporary file
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".jsonl", delete=False
        ) as tmp_file:
            tmp_file.write(jsonl_input)
            tmp_file_path = tmp_file.name
    except Exception as e:
        return {"status": "error", "message": f"Failed to write temp file: {e}"}

    # Run the generator
    try:
        curves = generate_all_scenario_curves(
            target_date,
            scenarios_path=tmp_file_path,
            combine_with_news=combine_with_news,
        )
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate curves: {e}"}

    if not curves:
        return {"status": "error", "message": "No curves generated"}

    return {"status": "success", "curves": curves}


@app.get("/news-top-factors")
async def get_news_top_factors(
    date: str | None = None, top_factors: int = 3, top_articles: int = 3
):
    """Return top factors by absolute score with their top news articles."""
    target_date = date or _dt.date.today().isoformat()

    if top_factors <= 0 or top_articles <= 0:
        raise HTTPException(
            status_code=400, detail="top_factors and top_articles must be > 0"
        )

    db_path = _ensure_news_db_env()
    if (not db_path.exists()) or db_path.stat().st_size == 0:
        raise HTTPException(
            status_code=404, detail="news.db not found or empty; run ingestion first"
        )

    factors = _top_factors_with_articles(
        target_date, top_factors=top_factors, top_articles=top_articles
    )
    if not factors:
        raise HTTPException(
            status_code=404,
            detail=f"No factor scores found for {target_date}. Run factor extraction/aggregation first.",
        )

    return {
        "date": target_date,
        "top_factors": top_factors,
        "top_articles": top_articles,
        "factors": factors,
    }


@app.get("/news-monitor")
def get_news_monitor(date: str | None = None):

    print("[news-monitor] called")

    # --- Load analysis (optional) ---
    analysis = _load_analysis_for_today()
    print(
        "[news-monitor] analysis loaded:",
        "FOUND" if analysis else "NOT FOUND",
        f"type={type(analysis)}",
    )
    if not analysis:
        print("[news-monitor] ERROR: no analysis available")
        raise HTTPException(status_code=405, detail="No news analysis available")

    return {
        "message": f"Returned {len(analysis)} article rows for inspection",
        "articles": analysis,  # optional: return full article data
    }

@app.post("/optimize-scenarios/")
async def optimize_scenarios(request: Request):
    """
    Run scenario-based portfolio optimization.
    
    Expected JSON payload:
    {
        "scenarioMatrix": [...],  // Scenario metadata
        "scenarioCurves": {...},  // Dict: scenario_name -> [{tenor, rate}, ...]
        "combineMode": "probability_weighted",
        "optimizationMethod": "mean_lexicographic",
        "netCashOutflow": 1_000_000_000
    }
    """
    global portfolio, base_curve_handle
    openai_key = os.getenv("OPENAI_API_KEY")
    
    
    # Validate prerequisites
    if not any(portfolio.assets.values()):
        return JSONResponse(
            status_code=400,
            content={"error": "No portfolio loaded. Upload portfolio via /upload-portfolio/"}
        )
        
    try:
        payload = await request.json()
        scenario_matrix = payload.get("scenarioMatrix", [])
        scenario_curves = payload.get("scenarioCurves", {})  # NEW!
        combine_mode = payload.get("combineMode", "probability_weighted")
        optimization_method = payload.get("optimizationMethod", "mean_lexicographic")
        net_cash_outflow = payload.get("netCashOutflow", 1_000_000_000)
        custom_weights = payload.get("customWeights", None)
        
        if not scenario_matrix:
            return JSONResponse(
                status_code=400,
                content={"error": "scenarioMatrix is required"}
            )
        
        if not scenario_curves:
            return JSONResponse(
                status_code=400,
                content={"error": "scenarioCurves is required"}
            )
                
        # Convert scenarios WITH their corresponding curves
        scenarios = convert_frontend_scenarios_with_curves(
            scenario_matrix,
            scenario_curves,
            net_cash_outflow
        )
        
        # Create engine
        engine = ScenarioRebalancingEngine(
            base_portfolio=portfolio,
            net_cash_outflow=net_cash_outflow,
            min_lcr=1.0,
            max_lcr=1.3,
            target_duration=None,
            duration_tolerance=0.5,
            allocation_buffer=0.02,
        )
        
        # Add all scenarios
        for scenario in scenarios:
            engine.add_scenario(scenario)
        
        # Run optimization
        engine.run_rebalancing(
            method=optimization_method,
            verbose=False,
            max_position_size=0.40
        )
        
        # Combine portfolios
        if combine_mode == "custom" and custom_weights:
            final_weights = engine.combine_portfolios(
                mode="custom",
                custom_weights=custom_weights
            )
        else:
            final_weights = engine.combine_portfolios(mode=combine_mode)
        
        # Build response
        final_df = engine.build_combined_dataframe()
        
        # Generate AI report
        ai_report = None
        
        if openai_key:
            try:
                
                scenario_descriptions = {
                    name: result["scenario"].metadata.get("description", "")
                    for name, result in engine.results.items()
                }
                print("Scen descriptions:", scenario_descriptions)
                ai_report = engine.generate_report_llm(
                    scenario_descriptions=scenario_descriptions,
                    openai_api_key=openai_key,
                    model="gpt-4"
                )
            except Exception as e:
                print(f"AI report generation failed: {e}")
                ai_report = None
        
        # Build response
        scenario_results = {}
        for name, result in engine.results.items():
            scenario_results[name] = {
                "scenario_name": name,
                "probability": result["scenario"].probability,
                "description": result["scenario"].metadata.get("description", ""),
                "metrics": result["metrics"],
                "top_allocations": result["df"].nlargest(5, "Allocated_Amount")[
                    ["Name", "Level", "Allocated_Amount", "YTM"]
                ].to_dict(orient="records")
            }
        
        total_allocated = float(final_df["Allocated_Amount"].sum())
        
        return {
            "status": "success",
            "final_portfolio": final_df.to_dict(orient="records"),
            "scenario_results": scenario_results,
            "ai_report": ai_report,
            "combination_mode": combine_mode,
            "optimization_method": optimization_method,
            "summary_metrics": {
                "total_allocated": total_allocated,
                "allocation_pct_of_nco": total_allocated / net_cash_outflow,
                "net_cash_outflow": net_cash_outflow
            }
        }
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Optimization failed: {str(e)}",
                "traceback": traceback.format_exc()
            }
        )


def convert_frontend_scenarios_with_curves(
    scenario_matrix: list,
    scenario_curves: dict,
    net_cash_outflow: float
) -> list:
    """
    Convert frontend scenarios to Scenario objects with their yield curves.
    
    Args:
        scenario_matrix: List of scenario metadata dicts
        scenario_curves: Dict mapping scenario_name -> curve data [{tenor, rate}, ...]
        net_cash_outflow: Base NCO
    
    Returns:
        List of Scenario objects with proper QuantLib curve handles
    """    
    scenarios = []
    today = ql.Date.todaysDate()
    
    for s in scenario_matrix:
        # Extract scenario info
        name = s.get('Scenario', 'Unnamed Scenario')
        description = s.get('Description', '')
        probability = float(s.get('Probability', 0.0))
        rationale = s.get('Rationale', '')
        impact_channels = s.get('ImpactChannels', '')
        trade_list = s.get('TradeList', [])
        
        # Extract shock info
        shocks = s.get('Shocks', {})
        move_bp = shocks.get('move', 0)
        curve_type = shocks.get('yield_curve', 'parallel_shift')
        credit_spreads = shocks.get('credit_spreads', {})
        
        # Adjust NCO based on LCR delta
        metrics_delta = s.get('MetricsDelta', {})
        lcr_delta = metrics_delta.get('LCR', 0)
        nco_multiplier = 1.0 - (lcr_delta / 100.0)
        scenario_nco = net_cash_outflow * nco_multiplier
        
        # Try to find curve by scenario name
        curve_data = scenario_curves.get(name)
        
        # Fallback: if not found by name, try first available curve
        if curve_data is None and scenario_curves:
            print(f"Warning: No curve found for scenario '{name}', using first available")
            curve_data = list(scenario_curves.values())[0]
        
        # Build QuantLib yield curve from curve_data
        if not curve_data:
            raise ValueError(f"No yield curve data available for scenario '{name}'")
        
        yield_curve_handle = build_ql_curve_from_data(curve_data, today)
        
        # Build all curves (up/down and survival curves) for this scenario
        all_curves = build_all_curves_for_scenario(yield_curve_handle, today)
        
        # Build metadata (store all curves in metadata for use in scenario_rebalancing)
        metadata = {
            "description": description,
            "rationale": rationale,
            "impact_channels": impact_channels,
            "trade_list": trade_list,
            "metrics_delta": metrics_delta,
            "credit_spreads": credit_spreads,
            "shock_type": curve_type,
            "shock_magnitude_bp": move_bp,
            "net_cash_outflow": scenario_nco,
            # Store all curves for update_prices call
            "up_curve": all_curves["up_curve"],
            "down_curve": all_curves["down_curve"],
            "survival_curves": all_curves["survival_curves"],
            "survival_curves_up": all_curves["survival_curves_up"],
            "survival_curves_down": all_curves["survival_curves_down"],
        }
        
        # Create Scenario
        scenario = RebalanceScenario(
            name=name,
            yield_curve_handle=yield_curve_handle,
            probability=probability,
            metadata=metadata, 
            sofr_handle=None
        )

        scenario.build_sofr_handle()


        
        scenarios.append(scenario)
    
    return scenarios


def build_ql_curve_from_data(curve_data: list, today: ql.Date) -> ql.YieldTermStructureHandle:
    """
    Build QuantLib yield curve from frontend curve data.
    
    Args:
        curve_data: List of dicts [{tenor: "1Y", rate: 0.045}, ...]
        today: QuantLib Date
    
    Returns:
        ql.YieldTermStructureHandle
    """
    # curve_data format: [{"tenor": "1Y", "rate": 0.045}, ...]
    dates = [today]
    rates = [0.0]  
    
    for point in curve_data:
        tenor_str = point["tenor"]
        rate = float(point["rate"])
        
        # Parse tenor
        ql_period = ql.PeriodParser.parse(tenor_str)
        dt = today + ql_period
        
        dates.append(dt)
        rates.append(rate)
    
    # Build zero curve
    curve = ql.CubicZeroCurve(dates, rates, ql.Actual360(), ql.TARGET())
    curve.enableExtrapolation()
    
    return ql.YieldTermStructureHandle(curve)

    
    return sofr_index

def build_all_curves_for_scenario(
    yield_curve_handle: ql.YieldTermStructureHandle,
    today: ql.Date
) -> dict:
    """
    Build up/down curves and survival curves for a scenario yield curve.
    Mirrors the logic from /upload-yield-curve/ endpoint.
    
    Returns:
        dict with keys: 'up_curve', 'down_curve', 'survival_curves', 
        'survival_curves_up', 'survival_curves_down'
    """
    bump = 0.0001
    interest_rate_bump_up = ql.QuoteHandle(ql.SimpleQuote(bump))
    interest_rate_bump_down = ql.QuoteHandle(ql.SimpleQuote(-bump))
    
    # Build up/down curves
    up_curve_handle = ql.ZeroSpreadedTermStructure(
        yield_curve_handle, interest_rate_bump_up
    )
    up_curve = ql.YieldTermStructureHandle(up_curve_handle)
    
    down_curve_handle = ql.ZeroSpreadedTermStructure(
        yield_curve_handle, interest_rate_bump_down
    )
    down_curve = ql.YieldTermStructureHandle(down_curve_handle)
    
    # Build survival curves (same CDS spreads as base curve)
    tenors = [ql.Period(y, ql.Years) for y in [1, 2, 3, 5, 7, 10]]
    cds_spreads = {
        "AAA": [10, 12, 13, 17, 18, 22],
        "AA": [15, 17, 18, 25, 28, 35],
        "A": [25, 28, 30, 45, 50, 65],
        "BBB": [50, 55, 58, 85, 95, 110],
    }
    
    recovery_rates = {
        "AAA": 0.741,
        "AA": 0.621,
        "A": 0.457,
        "BBB": 0.381,
    }
    
    survival_curves = {}
    survival_curves_up = {}
    survival_curves_down = {}
    crv_dicts = [survival_curves, survival_curves_up, survival_curves_down]
    changes = [0, bump, -bump]
    
    for rating in recovery_rates.keys():
        for change, crv_dict in zip(changes, crv_dicts):
            rr = recovery_rates[rating]
            cds_spread = cds_spreads[rating]
            cds_helpers = [
                ql.SpreadCdsHelper(
                    (cds / 1000.0) + change,
                    tenor,
                    1,
                    ql.TARGET(),
                    ql.Quarterly,
                    ql.Following,
                    ql.DateGeneration.TwentiethIMM,
                    ql.Actual360(),
                    rr,
                    yield_curve_handle,
                )
                for (cds, tenor) in zip(cds_spread, tenors)
            ]
            hazard_rate_curve = ql.PiecewiseFlatHazardRate(
                today, cds_helpers, ql.Actual360()
            )
            hazard_rate_curve.enableExtrapolation()
            crv_dict[rating] = ql.DefaultProbabilityTermStructureHandle(
                hazard_rate_curve
            )
    
    return {
        "up_curve": up_curve,
        "down_curve": down_curve,
        "survival_curves": survival_curves,
        "survival_curves_up": survival_curves_up,
        "survival_curves_down": survival_curves_down,
    }