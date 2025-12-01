import aiohttp
import asyncio
from typing import Dict, Any
from arbitrage_engine.core.interfaces import ExchangeAdapter
from arbitrage_engine.core.normalization import StandardizedFunding

class dYdXAdapter(ExchangeAdapter):
    def __init__(self):
        # We are using aiohttp directly for dYdX v4 Indexer API
        pass

    async def fetch_funding_rates(self) -> Dict[str, Dict[str, Any]]:
        try:
            # dYdX V4 Indexer API
            async with aiohttp.ClientSession() as session:
                async with session.get("https://indexer.dydx.trade/v4/perpetualMarkets", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        markets = data.get('markets', {})
                        rates = {}

                        for symbol, info in markets.items():
                            # symbol is like "BTC-USD"
                            rate_str = info.get('nextFundingRate')
                            if rate_str:
                                raw_rate = float(rate_str)
                                # dYdX v4 funding is hourly
                                apr = StandardizedFunding.normalize_apr(raw_rate, interval_hours=1.0)

                                # Normalize Symbol: "BTC-USD" -> "BTC"
                                clean_sym = symbol.split('-')[0]

                                rates[clean_sym] = {
                                    "rate": raw_rate,
                                    "apr": apr,
                                    "interval": "1h",
                                    "platform": "dYdX"
                                }
                        return rates

            return {}

        except Exception as e:
            print(f"dYdX Exception: {e}")
            return {}

    async def get_mark_price(self, symbol: str) -> float:
        return 0.0
