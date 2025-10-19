"""
assets.py
----------
Defines base Asset class and subclasses for HQLA categories.

Author: Togay Atmaca (tatmaca)
Created: 2025-10-19
"""

from abc import ABC, abstractmethod


class Asset(ABC):
    """Abstract base class for all HQLA assets."""

    def __init__(self, name: str, market_value: float, haircut: float):
        self.name = name
        self.market_value = market_value
        self.haircut = haircut

    @abstractmethod
    def category(self) -> str:
        """Return asset category identifier."""
        pass

    def adjusted_value(self) -> float:
        """Market value after applying haircut."""
        return self.market_value * (1 - self.haircut)

    def update_price(self, new_value: float) -> None:
        """Update market value to reflect new price."""
        self.market_value = new_value

    def liquidate(self) -> float:
        """Simulate liquidation; return full market value."""
        return self.market_value


class Level1Asset(Asset):
    def __init__(self, name: str, market_value: float):
        super().__init__(name, market_value, haircut=0.00)

    def category(self) -> str:
        return "L1"


class Level2AAsset(Asset):
    def __init__(self, name: str, market_value: float):
        super().__init__(name, market_value, haircut=0.15)

    def category(self) -> str:
        return "L2A"


class Level2BAsset(Asset):
    def __init__(self, name: str, market_value: float):
        super().__init__(name, market_value, haircut=0.25)

    def category(self) -> str:
        return "L2B"
