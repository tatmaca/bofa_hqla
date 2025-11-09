"""
portfolio.py
-------------
Manages collections of HQLA instruments (Fixed, Floating, Discount)
across Basel III liquidity levels.

Author: Togay Atmaca (tatmaca)
Updated: 2025-11-08
"""

from typing import Dict, List

import QuantLib as ql

from . import hqla_instruments as HQLA


class Portfolio:
    """Container for HQLA instruments and portfolio-level operations."""

    def __init__(self):
        self.assets: Dict[str, List[HQLA.HQLA_Asset]] = {
            "L1": [],
            "L2A": [],
            "L2B": [],
        }

    def _category(self, inst: HQLA.HQLA_Asset) -> str:
        """Infer Basel III level from inheritance."""
        if isinstance(inst, HQLA.Level1):
            return "L1"
        elif isinstance(inst, HQLA.Level2A):
            return "L2A"
        elif isinstance(inst, HQLA.Level2B):
            return "L2B"
        else:
            raise ValueError(f"Unrecognized instrument type: {type(inst)}")

    def add_instrument(self, inst: HQLA.HQLA_Asset) -> None:
        cat = self._category(inst)
        self.assets[cat].append(inst)

    def remove_instrument(self, name: str):
        for cat, group in self.assets.items():
            self.assets[cat] = [i for i in group if i.name != name]

    def update_position(self, name: str, quantity: float):
        for group in self.assets.values():
            for i in group:
                if i.name == name:
                    i.quantity = quantity
                    return
        raise KeyError(name)

    def update_prices(
        self,
        yield_curve: ql.YieldTermStructureHandle,
    ) -> None:
        """Reprice all instruments using QuantLib dirty price."""
        for group in self.assets.values():
            for inst in group:
                inst.price_from_curve(yield_curve)

    def total_value(self) -> float:
        """Total market (dirty) value of the portfolio."""
        total = 0.0
        for group in self.assets.values():
            for inst in group:
                if getattr(inst, "dirty_price", None) is None:
                    raise ValueError(f"Instrument {inst.name} has no price set.")
                total += inst.dirty_price * inst.quantity
        return total

    def adjusted_value(self) -> float:
        """Basel-adjusted HQLA value = dirty price × (1 - haircut) × LCR weight."""
        total = 0.0
        for group in self.assets.values():
            for inst in group:
                if getattr(inst, "dirty_price", None) is None:
                    raise ValueError(f"Instrument {inst.name} has no price set.")
                adj_val = (
                    inst.dirty_price
                    * inst.quantity
                    * (1.0 - inst.haircut)
                    * inst.max_lcr_weight
                )
                total += adj_val
        return total

    def summary(self) -> None:
        """Print detailed portfolio summary per category."""
        for cat, group in self.assets.items():
            print(f"\n========== {cat} Assets ==========")
            if not group:
                print("No assets in this category.")
                continue

            for inst in group:
                if getattr(inst, "dirty_price", None) is None:
                    raise ValueError(f"Instrument {inst.name} has no price set.")
                price_str = f"${inst.dirty_price:.2f}"
                print(f"--> {inst.name} ({inst.isin}): {price_str} x {inst.quantity}")

            # Optionally, print subtotal for the category
            subtotal = sum(inst.dirty_price * inst.quantity for inst in group)
            print(f"Subtotal ({cat}): ${subtotal:.2f}")


if __name__ == "__main__":
    from datetime import date

    # --- Dates for instruments ---
    today = ql.Date(8, 11, 2025)
    ql.Settings.instance().evaluationDate = today

    # -- yield curve handle
    flat_rate = ql.SimpleQuote(0.05)
    rate_handle = ql.QuoteHandle(flat_rate)
    day_count = ql.Actual360()
    continuous_comp = ql.Continuous

    flat_yield_curve = ql.FlatForward(today, rate_handle, day_count, continuous_comp)

    discount_curve_handle = ql.YieldTermStructureHandle(flat_yield_curve)

    # -- SOFR index curve
    sofr_rate = 5 * 1e-4
    sofr_term_structure = ql.FlatForward(today, rate_handle, day_count, ql.Continuous)
    sofr_term_structure_handle = ql.YieldTermStructureHandle(sofr_term_structure)
    sofr_index = ql.Sofr(sofr_term_structure_handle)

    # Set SOFR index history
    im = ql.IndexManager.instance()
    sofr_index = ql.Sofr(sofr_term_structure_handle)

    issue = ql.Date(8, 6, 2024)
    maturity_1y = ql.Date(8, 11, 2026)
    maturity_2y = ql.Date(8, 11, 2027)
    maturity_3y = ql.Date(8, 11, 2028)

    # --- Create portfolio ---
    portfolio = Portfolio()

    # 1) Level1 Zero-Coupon Bond
    zero_l1 = HQLA.Level1Discount(
        issue_date=issue,
        maturity_date=maturity_1y,
        face_value=100,
        quantity=10,
        name="L1_Zero_1Y",
        isin="US0000000001",
    )
    zero_l1.build_bond()
    portfolio.add_instrument(zero_l1)

    # 2) Level1 Floating Rate Bond
    floating_l1 = HQLA.Level1Floating(
        issue_date=issue,
        maturity_date=maturity_2y,
        face_value=100,
        quantity=5,
        name="L1_Floating_2Y",
        isin="US0000000002",
    )
    floating_l1.build_bond(index=sofr_index)
    portfolio.add_instrument(floating_l1)

    # 3) Level2A Fixed Rate Bond
    fixed_l2a = HQLA.Level2AFixed(
        issue_date=issue,
        maturity_date=maturity_2y,
        face_value=100,
        coupons=[0.03],  # 3% coupon
        quantity=8,
        name="L2A_Fixed_2Y",
        isin="US0000000003",
    )
    fixed_l2a.build_bond()
    portfolio.add_instrument(fixed_l2a)

    # 4) Level2B Floating Rate Bond
    floating_l2b = HQLA.Level2BFloating(
        issue_date=issue,
        maturity_date=maturity_3y,
        face_value=100,
        quantity=12,
        name="L2B_Floating_3Y",
        isin="US0000000004",
    )
    floating_l2b.build_bond(index=sofr_index)
    portfolio.add_instrument(floating_l2b)

    im.clearHistory(sofr_index.name())
    fixing_dates = list(floating_l2b.schedule)
    calendar = sofr_index.fixingCalendar()
    for date in fixing_dates:
        adjusted_date = calendar.adjust(date, ql.Preceding)
        sofr_index.addFixing(adjusted_date, sofr_rate)

    # --- Update prices using discount curve ---
    portfolio.update_prices(yield_curve=discount_curve_handle)

    # --- Print portfolio summary ---
    print("Portfolio Total Value:", portfolio.total_value())
    print("Portfolio Adjusted Value:", portfolio.adjusted_value())
    print("Portfolio Summary per Level:")
    portfolio.summary()

    flat_rate_update = ql.SimpleQuote(0.25)
    rate_handle_update = ql.QuoteHandle(flat_rate_update)
    flat_yield_curve_update = ql.FlatForward(
        today, rate_handle_update, day_count, continuous_comp
    )

    # --- Print updated position portfolio summary ---
    print(
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    )
    print("...\n...\n...")
    print(
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    )
    print("Changing positions for each instrument...")
    portfolio.update_position("L1_Zero_1Y", 20)
    portfolio.update_position("L1_Floating_2Y", 2)
    portfolio.update_position("L2A_Fixed_2Y", 32)
    portfolio.update_position("L2B_Floating_3Y", 8)
    print("Portfolio Total Value:", portfolio.total_value())
    print("Portfolio Adjusted Value:", portfolio.adjusted_value())
    print("Portfolio Summary per Level:")
    portfolio.summary()

    # --- Print UPDATED yield curve portfolio summary ---
    discount_curve_handle_update = ql.YieldTermStructureHandle(flat_yield_curve_update)

    portfolio.update_prices(yield_curve=discount_curve_handle_update)
    print(
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    )
    print("...\n...\n...")
    print(
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    )
    print("Level shift in yield curve to .25...")
    print("Portfolio Total Value:", portfolio.total_value())
    print("Portfolio Adjusted Value:", portfolio.adjusted_value())
    print("Portfolio Summary per Level:")
    portfolio.summary()
