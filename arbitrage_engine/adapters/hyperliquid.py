import aiohttp
import asyncio
from typing import Dict, Any
from arbitrage_engine.core.interfaces import ExchangeAdapter
from arbitrage_engine.core.normalization import StandardizedFunding

class HyperliquidAdapter(ExchangeAdapter):
    def __init__(self):
        self.url = "https://api.hyperliquid.xyz/info"
        self.headers = {'User-Agent': 'ArbitrageEngine/1.0'}

    async def fetch_funding_rates(self) -> Dict[str, Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.url, json={"type": "predictedFundings"}, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        print(f"Hyperliquid Error: Status {response.status}")
                        return {}
                    data = await response.json()

                    rates = {}
                    for item in data:
                        if len(item) > 1:
                            sym = item[0]
                            # item[1] is a list of [exchange, funding_data]
                            # We are looking for 'HlPerp'? The original code checks ex[0] == 'HlPerp'
                            # Wait, let's verify the structure.
                            # The original code:
                            # for ex in item[1]:
                            #    if ex[0] == 'HlPerp': ...

                            for ex in item[1]:
                                if ex[0] == 'HlPerp':
                                    raw_rate = float(ex[1]['fundingRate'])
                                    # Hyperliquid funding is hourly
                                    apr = StandardizedFunding.normalize_apr(raw_rate, interval_hours=1.0)

                                    rates[sym] = {
                                        "rate": raw_rate,
                                        "apr": apr,
                                        "interval": "1h",
                                        "platform": "Hyperliquid"
                                    }
                    return rates
            except Exception as e:
                print(f"Hyperliquid Exception: {e}")
                return {}

    async def get_mark_price(self, symbol: str) -> float:
        # Not implemented for this optimization step as the focus is on funding rates arbitrage
        return 0.0
