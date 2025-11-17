"""
hqla_scenarios.py
-------------
Generate interest rate scenarios (parallel shifts) and reprice a portfolio of 
HQLA assets under those scenarios.

Author: Aryaa Gunavante (agunavante)
Updated: 2025-11-17
"""

from hqla_portfolio import Portfolio
import numpy as np
import QuantLib as ql
import scipy.linalg as la


class ScenarioGenerator:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def generate_parallel_scenarios(self, n_random=500, bp_std=1):

        """
        Return array of scenario shifts (decimal). Mix of deterministic small bumps
        and random parallel shocks (normal(0, bp_std)).
        bp_std is in decimal (0.01 = 100bp). Realistic: 0.01 ~ 100bp.
        """

        scen = []

        # deterministic bumps (±5bp, ±10bp, ±25bp)
        for bp in [0.0005, 0.001, 0.0025]:
            scen.extend([bp, -bp])

        # random shocks
        rng = np.random.default_rng(12345)
        scen.extend(rng.normal(0, bp_std, n_random).tolist())
        return np.array(scen)  # shape (S,)

    def reprice_under_parallel_shift(self, inst, base_curve_handle, shift):
        """
        shift: decimal (e.g., 0.01 = +100bp)
        returns (bumped_clean_price, coupon_cash_in_1yr)
        """

        # create spreaded curve: ZeroSpreadedTermStructure expects a QuoteHandle
        quote = ql.SimpleQuote(shift)
        spread_handle = ql.QuoteHandle(quote)
        bumped_ts = ql.ZeroSpreadedTermStructure(base_curve_handle, spread_handle)

        engine = ql.DiscountingBondEngine(ql.YieldTermStructureHandle(bumped_ts))
        inst.bond.setPricingEngine(engine)

        bumped_clean = float(inst.bond.cleanPrice())

        # coupon cash within 1y
        coupon_in_next_year = 0.0
        eval_date = ql.Settings.instance().evaluationDate
        one_year_later = eval_date + ql.Period(1, ql.Years)


        for cf in inst.bond.cashflows():
            # count only positive cashflows that occur <= one year ahead
            try:
                cf_date = cf.date()
            except Exception:
                continue
            if eval_date < cf_date <= one_year_later:
                amt = cf.amount()
                if amt is not None and amt > 0:
                    coupon_in_next_year += float(amt)
        return bumped_clean, coupon_in_next_year

    def compute_returns_matrix(self, base_curve_handle, scenarios):
        """
        Scenarios: 1D array of parallel shifts (decimal).
        Returns R matrix shape (S, N) where each entry is total return over 1yr:
          r = (P_s + coupons_in_1yr - P0) / P0
        and also returns base_prices vector.
        """
        # ensure portfolio base prices are set
        self.portfolio.update_prices(yield_curve=base_curve_handle)

        # flatten instruments into list (order must match assets_summary)
        inst_list = []
        for level, group in self.portfolio.assets.items():
            for inst in group:
                inst_list.append(inst)
        N = len(inst_list)
        S = len(scenarios)

        base_prices = np.zeros(N, dtype=float)
        for i, inst in enumerate(inst_list):
            # prefer stored clean_price if set; fallback to bond.cleanPrice()
            p0 = float(getattr(inst, "clean_price", None) or inst.bond.cleanPrice())
            base_prices[i] = p0

        R = np.zeros((S, N), dtype=float)

        for s_idx, shift in enumerate(scenarios):
            for i, inst in enumerate(inst_list):
                bumped_p, coupons = self.reprice_under_parallel_shift(inst, base_curve_handle, shift)
                r = (bumped_p + coupons - base_prices[i]) / base_prices[i]
                R[s_idx, i] = r

        return R, base_prices, inst_list

    def make_psd_cov(self, R):
        # R: scenarios × assets
        Omega_star = np.cov(R, rowvar=False, ddof=1)  # shape N×N
        # symmetric eigh
        eigvals, eigvecs = la.eigh(Omega_star)
        eigvals_clipped = np.clip(eigvals, a_min=0.0, a_max=None)
        Omega_psd = (eigvecs * eigvals_clipped) @ eigvecs.T
        # numeric stabilization
        eps = 1e-12
        Omega_psd += eps * np.eye(Omega_psd.shape[0])
        #print(Omega_psd)
        return Omega_psd
    