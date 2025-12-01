import aiohttp
import asyncio
from typing import Dict, Any
from arbitrage_engine.core.interfaces import ExchangeAdapter
from arbitrage_engine.core.normalization import StandardizedFunding

class LighterAdapter(ExchangeAdapter):
    def __init__(self):
        # Lighter API V1
        self.url = "https://mainnet.zklighter.elliot.ai/api/v1/funding-rates"
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    async def fetch_funding_rates(self) -> Dict[str, Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        print(f"Lighter Error: Status {response.status}")
                        return {}

                    data = await response.json()
                    # Response format expectation:
                    # {
                    #   "success": true,
                    #   "result": [
                    #     {
                    #       "symbol": "BTC-USDC",
                    #       "rate": "0.0001", ...
                    #     }
                    #   ]
                    # }
                    # OR list of rates directly?
                    # The docs show `funding-rates` GET.
                    # Assuming standard list or wrapped in result.

                    # If it's a list directly
                    items = data if isinstance(data, list) else data.get('result', [])
                    if not items and isinstance(data, dict):
                         # Maybe it's just the dict itself if one item? Unlikely.
                         pass

                    rates = {}
                    for item in items:
                        # item example: {"symbol": "BTC-USDC", "rate": "0.000034"}
                        # Lighter symbols often have "-USDC" suffix
                        sym = item.get('symbol', '').replace('-USDC', '').replace('_USDC', '')

                        # Check rate key
                        rate_str = item.get('rate') or item.get('fundingRate')
                        if rate_str:
                            raw_rate = float(rate_str)
                            # Lighter funding interval is typically 1h or 8h.
                            # The original funding.py assumed 1h: `apr = raw_rate * 24 * 365`
                            apr = StandardizedFunding.normalize_apr(raw_rate, interval_hours=1.0)

                            rates[sym] = {
                                "rate": raw_rate,
                                "apr": apr,
                                "interval": "1h",
                                "platform": "Lighter"
                            }
                    return rates
            except Exception as e:
                print(f"Lighter Exception: {e}")
                return {}

    async def get_mark_price(self, symbol: str) -> float:
        return 0.0
