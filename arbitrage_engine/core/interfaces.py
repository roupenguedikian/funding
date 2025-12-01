from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ExchangeAdapter(ABC):
    @abstractmethod
    async def fetch_funding_rates(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of funding rates for all available symbols.
        Format:
        {
            "BTC-USD": {
                "rate": 0.0001,           # Raw rate
                "apr": 0.0876,            # Annualized rate (decimal, e.g., 0.10 for 10%)
                "interval": "1h",         # Funding interval
                "next_funding_time": ...  # Timestamp of next funding
            },
            ...
        }
        """
        pass

    @abstractmethod
    async def get_mark_price(self, symbol: str) -> float:
        """Returns current mark price"""
        pass
