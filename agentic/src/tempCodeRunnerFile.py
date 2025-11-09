"""
hqla_portfolio_opt.py
-------------
Optimizes a portfolio of HQLA instruments (Fixed, Floating, Discount)
across Basel III liquidity levels by maxmizing expect returns given bounds.

Author: Aryaa Gunavante (agunavante)
Updated: 2025-11-09
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import QuantLib as ql
from hqla_portfolio import Portfolio


class HQLA_Portfolio_Opt:
    """
    Optimizes a portfolio of HQLA instruments (Fixed, Floating, Discount)
    across Basel III liquidity levels by maxmizing expect returns given bounds.
    """

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.assets = portfolio.assets

        # --- Build summary table of portfolio instruments ---
        rows = []
        mus = []  # expected returns (YTM)

        for level, group in self.assets.items():
            for inst in group:
                if inst.bond is None:
                    raise ValueError(f"Instrument {inst.name} has no QuantLib bond built yet.")

                # Extract clean price 
                clean_price_float = inst.clean_price or inst.bond.cleanPrice()
                clean_price = ql.BondPrice(clean_price_float, ql.BondPrice.Clean)

                # Compute YTM (proxy for expected return)
                ytm = inst.bond.bondYield(
                    clean_price,
                    inst.day_count,
                    ql.Compounded,
                    ql.Semiannual
                )


                # Store row
                rows.append({
                    "Name": inst.name,
                    "Level": level,
                    "Quantity": inst.quantity,
                    "Price": inst.dirty_price,
                    "Haircut": inst.haircut,
                    "LCR_Weight": inst.max_lcr_weight,
                    "YTM": ytm
                })
                
        self.assets_summary = pd.DataFrame(rows)
        self.n_assets = len(self.assets_summary)


    def optimize(self):
        """
        Maximizes expected return subject to:
          - sum(w_i) = 1
          - LCR composition limits
          - non-negative weights
        """

        df = self.assets_summary
        mu = df["YTM"].values
        prices = df["Price"].values

        # Objective: maximize sum(mu_i * price_i * w_i)
        def objective(weights):
            return -np.dot(weights, mu * prices)  # negative for maximization

        # Constraint: sum(weights) = 1
        constraints = ({
            "type": "eq",
            "fun": lambda w: np.sum(w) - 1
        })

        # Non-negative bounds
        bounds = [(0, 1) for _ in range(self.n_assets)]

        # Basel III composition constraints
        levels = df["Level"].values

        def l1_min(weights):  # Level 1 ≥ 60%
            return np.sum(weights[levels == "L1"]) - 0.6

        def l2a_b_max(weights):  # Level 2A + 2B ≤ 40%
            return 0.4 - np.sum(weights[levels != "L1"])

        def l2b_max(w):  # Level 2B ≤ 15%
            return 0.15 - np.sumweightsw[levels == "L2B"]

        constraints = (
            constraints,
            {"type": "ineq", "fun": l1_min},
            {"type": "ineq", "fun": l2a_b_max},
            {"type": "ineq", "fun": l2b_max},
        )

        # Initial guess
        x0 = np.ones(self.n_assets) / self.n_assets

        # Run optimization
        result = minimize(
            objective,
            x0=x0,
            bounds=bounds,
            constraints=constraints,
            method="SLSQP",
            options={"disp": True, "maxiter": 500}
        )

        df["Opt_Weight"] = result.x
        df["Weighted_Return"] = df["YTM"] * df["Price"] * df["Opt_Weight"]

        self.opt_result = result
        self.optimized_portfolio = df

        return df, result


if __name__ == "__main__":
    import QuantLib as ql
    from datetime import date
    from hqla_assets import (
        Level1Discount, Level1Floating, Level2AFixed, Level2BFloating
    )
    from hqla_portfolio import Portfolio
    from hqla_portfolio_opt import HQLA_Portfolio_Opt  # your optimizer class

    # --- Set evaluation date ---
    today = ql.Date(8, 11, 2025)
    ql.Settings.instance().evaluationDate = today

    # --- Define base yield curve ---
    flat_rate = ql.SimpleQuote(0.05)
    rate_handle = ql.QuoteHandle(flat_rate)
    day_count = ql.Actual360()
    continuous_comp = ql.Continuous
    flat_yield_curve = ql.FlatForward(today, rate_handle, day_count, continuous_comp)
    discount_curve_handle = ql.YieldTermStructureHandle(flat_yield_curve)

    # --- Define SOFR curve (for floating bonds) ---
    sofr_rate = 5 * 1e-4
    sofr_term_structure = ql.FlatForward(today, rate_handle, day_count, ql.Continuous)
    sofr_term_structure_handle = ql.YieldTermStructureHandle(sofr_term_structure)
    sofr_index = ql.Sofr(sofr_term_structure_handle)

    # --- Dates ---
    issue = ql.Date(8, 6, 2024)
    maturity_1y = ql.Date(8, 11, 2026)
    maturity_2y = ql.Date(8, 11, 2027)
    maturity_3y = ql.Date(8, 11, 2028)

    # --- Create a test portfolio ---
    portfolio = Portfolio()

    zero_l1 = Level1Discount(
        issue_date=issue, maturity_date=maturity_1y,
        face_value=100, quantity=10,
        name="L1_Zero_1Y", isin="US0000000001"
    )
    zero_l1.build_bond()
    portfolio.add_instrument(zero_l1)

    floating_l1 = Level1Floating(
        issue_date=issue, maturity_date=maturity_2y,
        face_value=100, quantity=5,
        name="L1_Floating_2Y", isin="US0000000002"
    )
    floating_l1.build_bond(index=sofr_index)
    portfolio.add_instrument(floating_l1)

    fixed_l2a = Level2AFixed(
        issue_date=issue, maturity_date=maturity_2y,
        face_value=100, coupons=[0.03], quantity=8,
        name="L2A_Fixed_2Y", isin="US0000000003"
    )
    fixed_l2a.build_bond()
    portfolio.add_instrument(fixed_l2a)

    floating_l2b = Level2BFloating(
        issue_date=issue, maturity_date=maturity_3y,
        face_value=100, quantity=12,
        name="L2B_Floating_3Y", isin="US0000000004"
    )
    floating_l2b.build_bond(index=sofr_index)
    portfolio.add_instrument(floating_l2b)

    # --- Update SOFR fixings ---
    im = ql.IndexManager.instance()
    im.clearHistory(sofr_index.name())
    fixing_dates = list(floating_l2b.schedule)
    calendar = sofr_index.fixingCalendar()
    for d in fixing_dates:
        sofr_index.addFixing(calendar.adjust(d, ql.Preceding), sofr_rate)

    # --- Price portfolio under base yield curve ---
    portfolio.update_prices(yield_curve=discount_curve_handle)

    print("\n====== INITIAL PORTFOLIO ======")
    portfolio.summary()
    print(f"\nTotal Value: {portfolio.total_value():.2f}")
    print(f"Adjusted HQLA Value: {portfolio.adjusted_value():.2f}")

    # --- Optimize portfolio weights ---
    print("\n====== RUNNING OPTIMIZATION ======")
    optimizer = HQLA_Portfolio_Opt(portfolio)
    opt_df, result = optimizer.optimize()

    print("\n====== OPTIMIZED PORTFOLIO ======")
    print(opt_df[["Name", "Level", "YTM", "Price", "Opt_Weight", "Weighted_Return"]])
    print(f"\nOptimized Objective (Expected Return): {-result.fun:.6f}")

    # --- Simulate new scenario: upward shift in yield curve ---
    print("\n====== YIELD CURVE SHIFT SCENARIO ======")
    flat_rate.setValue(0.07)  # 200 bp increase
    portfolio.update_prices(yield_curve=discount_curve_handle)

    print("Repricing portfolio after 200bp upward shift...")
    portfolio.summary()
    print(f"New Total Value: {portfolio.total_value():.2f}")
    print(f"New Adjusted Value: {portfolio.adjusted_value():.2f}")
    




    