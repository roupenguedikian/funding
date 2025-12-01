import asyncio
import pandas as pd
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from arbitrage_engine.adapters.hyperliquid import HyperliquidAdapter
from arbitrage_engine.adapters.dydx import dYdXAdapter
from arbitrage_engine.adapters.gmx import GMXAdapter
from arbitrage_engine.adapters.aster import AsterAdapter
from arbitrage_engine.adapters.lighter import LighterAdapter

class ArbitrageEngine:
    def __init__(self):
        self.adapters = [
            HyperliquidAdapter(),
            dYdXAdapter(),
            GMXAdapter(),
            AsterAdapter(),
            LighterAdapter()
        ]
        self.min_apr_diff = 5.0
        self.top_n = 30
        self.refresh_interval = 30  # seconds

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    async def run_once(self):
        # 1. Fetch data concurrently
        tasks = [adapter.fetch_funding_rates() for adapter in self.adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_rates: Dict[str, Dict[str, Any]] = {} # Symbol -> {Platform -> RateData}

        for i, res in enumerate(results):
            if isinstance(res, Exception):
                # Print to stderr to avoid cluttering the cleared screen if possible,
                # or just log it.
                # print(f"Adapter {self.adapters[i].__class__.__name__} failed: {res}", file=sys.stderr)
                pass
            else:
                platform_rates = res
                if not platform_rates:
                    continue

                for symbol, data in platform_rates.items():
                    if symbol not in all_rates:
                        all_rates[symbol] = {}
                    all_rates[symbol][data['platform']] = data

        # 2. Find Opportunities
        opportunities = []
        for symbol, platforms in all_rates.items():
            if len(platforms) < 2:
                continue

            # Convert to list to sort
            venue_list = list(platforms.values())
            venue_list.sort(key=lambda x: x['apr'], reverse=True)

            long_venue = venue_list[-1]
            short_venue = venue_list[0]

            spread_apr = short_venue['apr'] - long_venue['apr']

            if spread_apr > self.min_apr_diff:
                opportunities.append({
                    'Symbol': symbol,
                    'Long': f"{long_venue['platform']} ({long_venue['apr']:.2f}%)",
                    'Short': f"{short_venue['platform']} ({short_venue['apr']:.2f}%)",
                    'Spread APR': spread_apr,
                    'spread_val': spread_apr # Keep numeric for sorting
                })

        # 3. Output
        self.clear_screen()
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Scanning {len(all_rates)} symbols across {len(self.adapters)} venues...")

        if opportunities:
            df = pd.DataFrame(opportunities)
            df = df.sort_values(by='spread_val', ascending=False)

            # Filter Top N
            df = df.head(self.top_n)

            # Format for display
            df['Spread APR'] = df['Spread APR'].apply(lambda x: f"{x:.2f}%")
            display_df = df[['Symbol', 'Long', 'Short', 'Spread APR']]

            print(f"\n💰 TOP {self.top_n} ARBITRAGE OPPORTUNITIES 💰")
            print(display_df.to_string(index=False))
        else:
            print("No opportunities > 5% spread found.")

    async def run_loop(self):
        try:
            while True:
                await self.run_once()
                await asyncio.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print("\nArbitrage Engine stopped.")

if __name__ == "__main__":
    engine = ArbitrageEngine()
    try:
        asyncio.run(engine.run_loop())
    except KeyboardInterrupt:
        pass
