"""
hqla_portfolio.py
-------------
Manages collections of HQLA instruments (Fixed, Floating, Discount)
across Basel III liquidity levels.

Author: Togay Atmaca (tatmaca), Aryaa Gunavante
Updated: 2025-11-17
"""

from typing import Dict, List
import copy
import pandas as pd

import hqla_instruments as HQLA
import QuantLib as ql


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

    def clone(self) -> "Portfolio":
        """
        Return a deep copy of the portfolio (used by scenario_rebalancing).
        """
        dup = Portfolio()
        # shallow copy instrument references; avoids pickling QuantLib objects
        dup.assets = {k: list(v) for k, v in self.assets.items()}
        return dup

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
        up_curve: ql.YieldTermStructureHandle | None = None,
        down_curve: ql.YieldTermStructureHandle | None = None,
        survival_curves: Dict[str, ql.DefaultProbabilityTermStructureHandle] | None = None,
        survival_curves_up: Dict[str, ql.DefaultProbabilityTermStructureHandle] | None = None,
        survival_curves_down: Dict[str, ql.DefaultProbabilityTermStructureHandle] | None = None,
    ) -> None:
        """Reprice all instruments using QuantLib dirty price."""
        up_curve = up_curve or yield_curve
        down_curve = down_curve or yield_curve
        survival_curves = survival_curves or {}
        survival_curves_up = survival_curves_up or {}
        survival_curves_down = survival_curves_down or {}

        for group in self.assets.values():
            for inst in group:
                surv = None
                surv_up = None
                surv_down = None
                if inst.isRisky and inst.grade in survival_curves:
                    candidate = survival_curves.get(inst.grade)
                    if candidate is not None:
                        surv = candidate
                        surv_up = survival_curves_up.get(inst.grade, surv)
                        surv_down = survival_curves_down.get(inst.grade, surv)

                if surv is not None:
                    inst.price_from_curve(yield_curve, surv)
                    inst.bond_greeks(
                        yield_curve,
                        up_curve,
                        down_curve,
                        surv,
                        surv_up or surv,
                        surv_down or surv,
                    )
                else:
                    # fallback to plain discounting when no survival curves
                    inst.price_from_curve(yield_curve)
                    inst.bond_greeks(yield_curve, up_curve, down_curve)

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

    def build_assets_summary(self) -> pd.DataFrame:
        """
        Build a pandas DataFrame summarizing current holdings.
        Includes columns expected by scenario rebalancer.
        """
        rows = []
        for level, group in self.assets.items():
            for inst in group:
                rows.append(
                    {
                        "Name": inst.name,
                        "Level": level,
                        "DirtyPrice": getattr(inst, "dirty_price", None),
                        "YTM": getattr(inst, "ytm", None),
                        "ModDuration": getattr(inst, "duration", None),
                        "Quantity": getattr(inst, "quantity", None),
                        "Haircut": getattr(inst, "haircut", None),
                        "LCRWeight": getattr(inst, "max_lcr_weight", None),
                    }
                )
        return pd.DataFrame(rows)

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
