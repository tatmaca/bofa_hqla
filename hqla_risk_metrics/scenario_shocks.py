"""
scenario_shocks.py
------------------
Defines interest rate risk scenarios and how they impact HQLA portfolios,
including historical probabilities.

Author: Togay Atmaca
Created: 2025-10-19
"""

from portfolio import Asset, Portfolio


class YieldCurveScenario:
    """Base class for yield curve scenarios."""

    def __init__(self, name: str, magnitude: float, probability: float):
        """
        name: descriptive name
        magnitude: fraction or basis points to shift yields
        probability: historical probability of scenario occurring in next 6 months
        """
        self.name = name
        self.magnitude = magnitude
        self.probability = probability

    def apply(self, portfolio: Portfolio) -> Portfolio:
        """
        Apply the scenario to a portfolio.
        Should be overridden by child classes.
        Returns a new Portfolio object with adjusted values.
        """
        raise NotImplementedError("Child classes must implement apply method.")


class YCSteepening(YieldCurveScenario):
    """Yield curve steepening scenario."""

    def __init__(self, magnitude: float = 0.05, probability: float = 0.285):
        super().__init__(
            name="YC Steepening", magnitude=magnitude, probability=probability
        )

    def apply(self, portfolio: Portfolio) -> Portfolio:
        new_portfolio = Portfolio(
            total_expected_outflows_30d=120_000_000, required_stable_funding=150_000_000
        )
        for cat, assets in portfolio.assets.items():
            for asset in assets:
                new_asset = asset  # shallow copy; deepcopy if needed
                if "UST" in asset.name:
                    # reduce market value proportional to magnitude
                    new_asset.market_value *= 1 - self.magnitude
                new_portfolio.add_asset(new_asset)
        return new_portfolio


class YCFlattening(YieldCurveScenario):
    """Yield curve flattening scenario."""

    def __init__(self, magnitude: float = 0.05, probability: float = 0.326):
        super().__init__(
            name="YC Flattening", magnitude=magnitude, probability=probability
        )

    def apply(self, portfolio: Portfolio) -> Portfolio:
        new_portfolio = Portfolio(
            total_expected_outflows_30d=120_000_000, required_stable_funding=150_000_000
        )
        for cat, assets in portfolio.assets.items():
            for asset in assets:
                new_asset = asset
                if "UST" in asset.name:
                    # flattening may reduce long-dated treasuries less
                    new_asset.market_value *= 1 - self.magnitude / 2
                new_portfolio.add_asset(new_asset)
        return new_portfolio
