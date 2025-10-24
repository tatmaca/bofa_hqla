# scenarios/base.py
from typing import Protocol, Dict, Any
from portfolio import Portfolio


class Scenario(Protocol):
    """Protocol for scenario objects."""

    name: str
    scenario_type: str
    magnitude: float
    probability: float

    def apply(self, portfolio: Portfolio) -> Portfolio:
        """Return a new Portfolio with scenario applied."""
        ...

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": getattr(self, "name", "Unnamed"),
            "type": getattr(
                self, "scenario_type", getattr(self, "scenario_type", "generic")
            ),
            "magnitude": getattr(self, "magnitude", None),
            "probability": getattr(self, "probability", None),
        }
