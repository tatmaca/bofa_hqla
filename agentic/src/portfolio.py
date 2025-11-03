"""
portfolio.py
-------------
Manages collections of HQLA assets, enabling updates,
liquidations, and portfolio-level metrics.

Author: Togay Atmaca (tatmaca)
Created: 2025-10-19
"""

from typing import Dict, List

from assets import Asset


class Portfolio:
    """Container for HQLA assets and portfolio-level operations."""

    def __init__(
        self, total_expected_outflows_30d: float, required_stable_funding: float
    ):
        self.assets: Dict[str, List[Asset]] = {"L1": [], "L2A": [], "L2B": []}

        self.total_expected_outflows_30d = total_expected_outflows_30d
        self.required_stable_funding = required_stable_funding

    def add_asset(self, asset: Asset) -> None:
        cat = asset.category()
        if cat not in self.assets:
            self.assets[cat] = []
        self.assets[cat].append(asset)

    def total_value(self) -> float:
        return sum(a.market_value for group in self.assets.values() for a in group)

    def adjusted_value(self) -> float:
        return sum(a.adjusted_value() for group in self.assets.values() for a in group)

    def update_prices(self, price_map: Dict[str, float]) -> None:
        """Update assets using external price data."""
        for group in self.assets.values():
            for a in group:
                if a.name in price_map:
                    a.update_price(price_map[a.name])

    def liquidate_all(self) -> float:
        """Liquidate portfolio and return total proceeds."""
        return sum(a.liquidate() for group in self.assets.values() for a in group)

    def get_asset(self, name: str):
        for group in self.assets.values():
            for a in group:
                if a.name == name:
                    return a
        return None

    def summary(self) -> Dict[str, float]:
        """Return aggregate values per asset class."""
        return {
            cat: sum(a.market_value for a in group)
            for cat, group in self.assets.items()
        }


if __name__ == "__main__":
    from .assets import Level1Asset, Level2AAsset, Level2BAsset

    p = Portfolio()
    p.add_asset(Level1Asset("US_Treasury", 100_000_000))
    p.add_asset(Level2AAsset("Covered_Bond", 50_000_000))
    p.add_asset(Level2BAsset("Corporate_Bond", 30_000_000))

    print("Total:", p.total_value())
    print("Adjusted:", p.adjusted_value())
