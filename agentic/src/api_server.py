# api_server.py
import pandas as pd
import QuantLib as ql
from fastapi import FastAPI, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import hqla_instruments as HQLA
from .hqla_portfolio import Portfolio

app = FastAPI()
portfolio = Portfolio()

# Global placeholder for the base curve
base_curve = None
base_curve_handle = None
base_curve_up = None
base_curve_down = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload-portfolio/")
async def upload_portfolio(file: UploadFile):
    """Upload portfolio CSV and build instrument objects."""
    global base_curve_handle
    df = pd.read_csv(file.file)
    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today
    soft_rate = 5 * 1e-2
    day_count_floater = ql.Actual360()
    rate_handle = ql.QuoteHandle(ql.SimpleQuote(soft_rate))
    sofr_term_structure = ql.FlatForward(
        today, rate_handle, day_count_floater, ql.Continuous
    )
    sofr_term_structure_handle = ql.YieldTermStructureHandle(sofr_term_structure)
    # Set SOFR index history
    sofr_index = ql.Sofr(sofr_term_structure_handle)
    calendar = sofr_index.fixingCalendar()

    # Reset all categories
    for cat in portfolio.assets:
        portfolio.assets[cat] = []

    for _, row in df.iterrows():
        cls = getattr(HQLA, f"Level{row['level']}{row['type']}")
        issue = ql.DateParser.parseISO(row["issue_date"])
        maturity = ql.DateParser.parseISO(row["maturity_date"])

        kwargs = {
            "issue_date": issue,
            "maturity_date": maturity,
            "face_value": float(row.get("face_value", 100)),
            "quantity": float(row.get("quantity", 0)),
            "name": row.get("name", ""),
            "isin": row.get("isin", ""),
        }

        if row["type"] == "Fixed":
            kwargs["coupons"] = [float(row["coupon"])]
            inst = cls(**kwargs)
            inst.build_bond()
        elif row["type"] == "Floating":
            inst = cls(**kwargs)
            inst.build_bond(index=sofr_index)
            # Add SOFR fixings for each scheduled date
            for dt in inst.schedule:
                adj_date = calendar.adjust(dt, ql.Preceding)
                sofr_index.addFixing(adj_date, soft_rate)
        else:  # Zero coupon
            inst = cls(**kwargs)
            inst.build_bond()

        if base_curve_handle:
            inst.price_from_curve(base_curve_handle)

        portfolio.add_instrument(inst)

    return {"status": "Portfolio created", "count": len(df)}


@app.post("/upload-yield-curve/")
async def upload_yield_curve(file: UploadFile):
    """
    Upload a yield curve CSV.
    Expected columns: 'tenor' (e.g., '1Y'), 'rate' (decimal or %)
    """
    global base_curve
    global base_curve_handle
    global base_curve_up
    global base_curve_down
    df = pd.read_csv(file.file)

    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today

    dates = [today]
    rates = [0.0]

    for _, row in df.iterrows():
        tenor = row["tenor"].strip()
        rate = float(row["rate"])
        # Convert tenor string to QuantLib period
        ql_period = ql.PeriodParser.parse(tenor)
        dt = today + ql_period
        dates.append(dt)
        rates.append(rate)

    # Build zero curve
    base_curve = ql.CubicZeroCurve(dates, rates, ql.Actual360(), ql.TARGET())
    base_curve_handle = ql.YieldTermStructureHandle(base_curve)

    interest_rate_bump_up = ql.QuoteHandle(ql.SimpleQuote(0.0001))
    interest_rate_bump_down = ql.QuoteHandle(ql.SimpleQuote(-0.0001))

    base_curve_up = ql.YieldTermStructureHandle(
        ql.ZeroSpreadedTermStructure(base_curve_handle, interest_rate_bump_up)
    )
    base_curve_down = ql.YieldTermStructureHandle(
        ql.ZeroSpreadedTermStructure(base_curve_handle, interest_rate_bump_down)
    )

    return {"status": "Yield curve uploaded", "points": len(dates)}


@app.get("/price-portfolio/")
async def price_portfolio():
    """Return current portfolio prices using base curve."""
    if not any(portfolio.assets.values()):
        return JSONResponse(
            status_code=400, content={"error": "No instruments in portfolio"}
        )

    if not base_curve_handle:
        return JSONResponse(
            status_code=400, content={"error": "No yield curve uploaded"}
        )

    # --- Reprice all instruments using the portfolio method ---
    portfolio.update_prices(base_curve_handle, base_curve_up, base_curve_down)

    # --- Build summary for API response ---
    summary = []
    for group in portfolio.assets.values():
        for inst in group:
            summary.append(
                {
                    "name": inst.name,
                    "isin": inst.isin,
                    "category": portfolio._category(inst),
                    "class": inst.__class__.__name__,
                    "dirty_price": inst.dirty_price,
                    "clean_price": inst.clean_price,
                    "quantity": inst.quantity,
                    "dv01": inst.dv01,
                    "duration": inst.duration,
                    "convexity": inst.convexity,
                }
            )

    portfolio.summary()

    return {"assets": summary, "status": "priced"}
