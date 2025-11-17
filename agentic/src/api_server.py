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
    global portfolio, base_curve_handle, base_curve, base_curve_up, base_curve_down
    global survival_curves, survival_curves_up, survival_curves_down

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
    sofr_index.clearFixings()
    calendar = sofr_index.fixingCalendar()

    # Reset all categories
    for cat in portfolio.assets:
        portfolio.assets[cat] = []

    for _, row in df.iterrows():
        cls = getattr(HQLA, f"Level{row['level']}{row['type']}")
        issue = ql.DateParser.parseISO(row["issue_date"])
        maturity = ql.DateParser.parseISO(row["maturity_date"])
        grade = row.get("rating", "")

        kwargs = {
            "issue_date": issue,
            "maturity_date": maturity,
            "face_value": float(row.get("face_value", 100)),
            "quantity": float(row.get("quantity", 0)),
            "name": row.get("name", ""),
            "isin": row.get("isin", ""),
            "grade": grade,
            "isRisky": False if pd.isna(grade) else True,
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

        #        if base_curve_handle:
        #            inst.price_from_curve(base_curve_handle)

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
    global survival_curves
    global survival_curves_up
    global survival_curves_down

    # Reset all old curve objects before constructing new ones
    base_curve = None
    base_curve_handle = None
    base_curve_up = None
    base_curve_down = None
    survival_curves = {}
    survival_curves_up = {}
    survival_curves_down = {}
    df = pd.read_csv(file.file)

    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today

    dates = [today]
    tenors = []
    rates = [0.0]

    for _, row in df.iterrows():
        tenor = row["tenor"].strip()
        rate = float(row["rate"])
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
    portfolio.update_prices(
        base_curve_handle,
        base_curve_up,
        base_curve_down,
        survival_curves,
        survival_curves_up,
        survival_curves_down,
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

    portfolio.summary()

    return {"assets": summary, "status": "priced"}
