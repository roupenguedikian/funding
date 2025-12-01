import aiohttp
import asyncio
from typing import Dict, Any
from arbitrage_engine.core.interfaces import ExchangeAdapter
from arbitrage_engine.core.normalization import StandardizedFunding

class AsterAdapter(ExchangeAdapter):
    def __init__(self):
        self.url = "https://fapi.apollox.finance/fapi/v1/premiumIndex"
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    async def fetch_funding_rates(self) -> Dict[str, Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        print(f"Aster Error: Status {response.status}")
                        return {}

                    data = await response.json()
                    rates = {}
                    for item in data:
                        # Aster returns symbols with USDT, e.g., "BTCUSDT"
                        symbol = item.get('symbol', '').replace('USDT', '')
                        if not symbol:
                            continue

                        last_funding_rate = item.get('lastFundingRate')
                        if last_funding_rate:
                            raw_rate = float(last_funding_rate)
                            # Aster returns 8h rate
                            apr = StandardizedFunding.normalize_apr(raw_rate, interval_hours=8.0)

                            rates[symbol] = {
                                "rate": raw_rate,
                                "apr": apr,
                                "interval": "8h",
                                "platform": "Aster"
                            }
                    return rates
            except Exception as e:
                print(f"Aster Exception: {e}")
                return {}

    async def get_mark_price(self, symbol: str) -> float:
        return 0.0
