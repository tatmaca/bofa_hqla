"""
hqla_portfolio_opt.py
-------------
Optimizes a portfolio of HQLA instruments (Fixed, Floating, Discount)
across Basel III liquidity levels by maxmizing expect returns given bounds.

Author: Aryaa Gunavante (agunavante)
Updated: 2025-11-09
"""

# Have to add Total Net Cashflows 


import numpy as np
import pandas as pd
from scipy.optimize import minimize
import QuantLib as ql
from hqla_portfolio import Portfolio
from hqla_scenarios import ScenarioGenerator


class HQLA_Portfolio_Opt:
    """
    Optimizes a portfolio of HQLA instruments (Fixed, Floating, Discount)
    across Basel III liquidity levels by maxmizing expect returns given bounds.
    """

    def __init__(self, portfolio: Portfolio, net_cash_outflow: float, max_lcr: float):
        self.portfolio = portfolio
        self.assets = portfolio.assets
        self.net_cash_outflow = net_cash_outflow
        self.max_lcr = max_lcr

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

    def _lcr_adjusted_value(self, weights):
        """Compute total HQLA-adjusted value given weights"""
        df = self.assets_summary
        return np.sum(weights * self.net_cash_outflow * 1 - df["Haircut"].values)


    def mean_optimize(self):
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
            return -np.dot(weights, mu) 

        # simple constraints on weights
        eq_cons = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
        bounds = [(0.0, 1.0) for _ in range(self.n_assets)]
        levels = df["Level"].values

        # Basel III composition constraints
        levels = df["Level"].values

        constraints = [
            eq_cons,
            {"type": "ineq", "fun": lambda w: np.sum(w[levels == "L1"]) - 0.6},
            {"type": "ineq", "fun": lambda w: 0.4 - np.sum(w[levels != "L1"])},
            {"type": "ineq", "fun": lambda w: 0.15 - np.sum(w[levels == "L2B"])},
            # HQLA liquidity constraint: adjusted value / NCF ≥ 1 and ≤ max_lcr
            {"type": "ineq", "fun": lambda w: self._lcr_adjusted_value(w) / self.net_cash_outflow - 1.0},
            {"type": "ineq", "fun": lambda w: self.max_lcr - self._lcr_adjusted_value(w) / self.net_cash_outflow},
        ]

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

         # Compute allocated amount
        df["Allocated_Amount"] = np.round(df["Opt_Weight"] * self.net_cash_outflow, 3)

        # Compute total portfolio value and expected return
        total_value = df["Allocated_Amount"].sum()
        expected_return = float(np.dot(df["Allocated_Amount"], df["YTM"].values) / total_value)

        # Select only requested columns for output
        output_df = df[["Name", "Level", "Price", "YTM", "Allocated_Amount"]]

        return output_df, result, total_value, expected_return

    def mean_variance_optimize(self, lam: float = 0.5,
                               base_curve_handle: ql.YieldTermStructureHandle = None,
                               n_random: int = 500, bp_std: float = 0.01,
                               use_mu: str = "ytm"):
        if base_curve_handle is None:
            raise ValueError("base_curve_handle required for scenario repricing.")

        sg = ScenarioGenerator(self.portfolio)
        scenarios = sg.generate_parallel_scenarios(n_random=n_random, bp_std=bp_std)
        R, base_prices, inst_list = sg.compute_returns_matrix(base_curve_handle, scenarios)
        Omega = sg.make_psd_cov(R)

        if use_mu == "ytm":
            mu = np.array(self.assets_summary["YTM"].values, dtype=float)
        else:
            mu = R.mean(axis=0)

        N = len(mu)

        def obj(w):
            return -lam * float(w @ mu) + (1.0 - lam) * float(w @ (Omega @ w))

        eq_cons = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
        bounds = [(0.0, 1.0) for _ in range(N)]
        levels = self.assets_summary["Level"].values

        constraints = [
            eq_cons,
            {"type": "ineq", "fun": lambda w: np.sum(w[levels == "L1"]) - 0.6},
            {"type": "ineq", "fun": lambda w: 0.4 - np.sum(w[levels != "L1"])},
            {"type": "ineq", "fun": lambda w: 0.15 - np.sum(w[levels == "L2B"])},
            {"type": "ineq", "fun": lambda w: self._lcr_adjusted_value(w) / self.net_cash_outflow - 1.0},
            {"type": "ineq", "fun": lambda w: self.max_lcr - self._lcr_adjusted_value(w) / self.net_cash_outflow},
        ]

        x0 = np.ones(N) / N
        res = minimize(obj, x0=x0, bounds=bounds, constraints=constraints, method="SLSQP", options={"maxiter": 1000, "ftol": 1e-9, "disp": False})

        df = self.assets_summary.copy()
        if not res.success:
            print("Warning: mean-variance optimizer did not converge:", res.message)

        df["Opt_Weight_MV"] = res.x
        df["Allocated_Amount_MV"] = res.x * self.net_cash_outflow

        port_return = float(res.x @ mu)
        port_var = float(res.x @ (Omega @ res.x))

        # Compute allocated amount
        df["Allocated_Amount"] = np.round(df["Opt_Weight_MV"] * self.net_cash_outflow, 3)
        
        # Compute total portfolio value and expected return
        total_value = df["Allocated_Amount"].sum()
        expected_return = float(np.dot(df["Allocated_Amount"], df["YTM"].values) / total_value)
        
        # Select only requested columns for output
        output_df = df[["Name", "Level", "Price", "YTM", "Allocated_Amount"]]
        
        return output_df, res, total_value, expected_return

