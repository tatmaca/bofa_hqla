"""
scenario_shocks.py
------------------
Defines interest rate risk scenarios and how they impact HQLA portfolios,
including historical probabilities.

Author: Togay Atmaca
Updated: 2025-10-24
"""

from portfolio import Asset, Portfolio

from scenario_gen.common.scenario import (
    ImpactChannels,
    Probability,
    Scenario,
    ScenarioFamily,
)


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
        self.scenario_type = "interest_rate"

    def apply(self, portfolio: Portfolio) -> Portfolio:
        """
        Apply the scenario to a portfolio.
        Should be overridden by child classes.
        Returns a new Portfolio object with adjusted values.
        """
        raise NotImplementedError("Child classes must implement apply method.")

    def to_scenario_dataclass(
        self, impact: ImpactChannels = None, description: str = "", rationale: str = ""
    ) -> Scenario:
        """
        Convert this YieldCurveScenario into a Scenario dataclass for unified handling.
        """
        if impact is None:
            impact = ImpactChannels()
        return Scenario(
            name=self.name,
            family=ScenarioFamily.IRR,
            description=description or self.name,
            rationale=rationale or "",
            probability=Probability(value=self.probability),
            impact=impact,
        )


class YCSteepening(YieldCurveScenario):
    """Yield curve steepening scenario."""

    def __init__(self, magnitude: float = 0.05, probability: float = 0.285):
        super().__init__(
            name="YC Steepening", magnitude=magnitude, probability=probability
        )

    def apply(self, portfolio: Portfolio) -> Portfolio:
        new_portfolio = Portfolio(
            total_expected_outflows_30d=portfolio.total_expected_outflows_30d,
            required_stable_funding=portfolio.required_stable_funding,
        )
        for cat, assets in portfolio.assets.items():
            for asset in assets:
                new_asset = asset  # shallow copy; deepcopy if needed
                if "UST" in asset.name:
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
            total_expected_outflows_30d=portfolio.total_expected_outflows_30d,
            required_stable_funding=portfolio.required_stable_funding,
        )
        for cat, assets in portfolio.assets.items():
            for asset in assets:
                new_asset = asset
                if "UST" in asset.name:
                    new_asset.market_value *= 1 - self.magnitude / 2
                new_portfolio.add_asset(new_asset)
        return new_portfolio
