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

from .hqla_instruments import (
    HQLAInstrument,
    Level1Discount,
    Level1Fixed,
    Level1Floating,
    Level2ADiscount,
    Level2AFixed,
    Level2AFloating,
    Level2BDiscount,
    Level2BFixed,
    Level2BFloating,
)


class Portfolio:
    """Container for HQLA instruments and portfolio-level operations."""

    def __init__(self):
        self.assets: Dict[str, List[HQLAInstrument]] = {
            "L1": [],
            "L2A": [],
            "L2B": [],
        }

    def _category(self, inst: HQLAInstrument) -> str:
        """Infer Basel III level from inheritance."""
        if isinstance(inst, (Level1Fixed, Level1Floating, Level1Discount)):
            return "L1"
        elif isinstance(inst, (Level2AFixed, Level2AFloating, Level2ADiscount)):
            return "L2A"
        elif isinstance(inst, (Level2BFixed, Level2BFloating, Level2BDiscount)):
            return "L2B"
        else:
            raise ValueError(f"Unrecognized instrument type: {type(inst)}")

    def add_instrument(self, inst: HQLAInstrument) -> None:
        cat = self._category(inst)
        self.assets[cat].append(inst)

    def update_prices(self, yield_curve: ql.YieldTermStructure) -> None:
        """Reprice all instruments using QuantLib dirty price."""
        for group in self.assets.values():
            for inst in group:
                inst.price = inst.price_from_curve(yield_curve)

    def total_value(self) -> float:
        """Total market (dirty) value of the portfolio."""
        total = 0.0
        for group in self.assets.values():
            for inst in group:
                if getattr(inst, "price", None) is None:
                    raise ValueError(f"Instrument {inst.name} has no price set.")
                total += inst.price / 100.0 * inst.face_value
        return total

    def adjusted_value(self) -> float:
        """Basel-adjusted HQLA value = dirty price × (1 - haircut) × LCR weight."""
        total = 0.0
        for group in self.assets.values():
            for inst in group:
                if getattr(inst, "price", None) is None:
                    raise ValueError(f"Instrument {inst.name} has no price set.")
                adj_val = (
                    inst.price
                    / 100.0
                    * inst.face_value
                    * (1.0 - inst.haircut)
                    * inst.max_lcr_weight
                )
                total += adj_val
        return total

    def summary(self) -> Dict[str, float]:
        """Return market value totals per category."""
        return {
            cat: sum(inst.price / 100.0 * inst.face_value for inst in group)
            for cat, group in self.assets.items()
            if all(getattr(inst, "price", None) is not None for inst in group)
        }

    def liquidate_all(self) -> float:
        """Assume liquidation at current dirty prices."""
        return self.total_value()


if __name__ == "__main__":
    # Example demo with dummy curve and instruments
    calendar = ql.TARGET()
    day_count = ql.Actual365Fixed()
    today = ql.Date(8, 11, 2025)
    ql.Settings.instance().evaluationDate = today
    curve = ql.FlatForward(today, 0.03, day_count)

    # wrap the curve in a handle
    curve_handle = ql.YieldTermStructureHandle(curve)

    issue = ql.Date(9, 11, 2020)
    maturity = ql.Date(9, 11, 2030)

    l1 = Level1Fixed(
        name="UST10Y",
        face_value=100_000_000,
        issue_date=issue,
        maturity_date=maturity,
        calendar=calendar,
        day_count=day_count,
        business_day_convention=ql.Following,
        coupon_rate=0.025,
    )

    l2a = Level2AFloating(
        name="CoveredBond",
        face_value=50_000_000,
        issue_date=issue,
        maturity_date=maturity,
        calendar=calendar,
        day_count=day_count,
        business_day_convention=ql.Following,
    )

    l2b = Level2BDiscount(
        name="CorpZC",
        face_value=30_000_000,
        issue_date=issue,
        maturity_date=maturity,
        calendar=calendar,
        day_count=day_count,
        business_day_convention=ql.Following,
    )

    p = Portfolio()
    for inst in [l1, l2a, l2b]:
        p.add_instrument(inst)

    # pass the handle, not the raw curve
    p.update_prices(curve_handle)

    print("Total dirty value:", p.total_value())
    print("Adjusted HQLA value:", p.adjusted_value())
    print("Summary by level:", p.summary())
