import requests
import pandas as pd
import time
import asyncio
import json

# --- CONFIGURATION ---
LIGHTER_API_KEY = "API KEY"  # <--- PASTE KEY HERE
# ---------------------

# Lighter SDK (elliottech/lighter-python)
try:
    from lighter.api_client import ApiClient
    from lighter.configuration import Configuration
    from lighter.api.order_api import OrderApi
    from lighter.api.candlestick_api import CandlestickApi
    SDK_AVAILABLE = True
except ImportError:
    print("⚠️ Lighter SDK not found. Install with: pip install git+https://github.com/elliottech/lighter-python.git")
    SDK_AVAILABLE = False

class ArbEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.min_apr_diff = 5.0  # Show opportunities with >5% APR difference

        if SDK_AVAILABLE and LIGHTER_API_KEY and "YOUR_" not in LIGHTER_API_KEY:
            print("✅ Lighter SDK configured")
        elif SDK_AVAILABLE:
            print("⚠️ Lighter SDK installed but API Key is missing.")
        else:
            print("⚠️ Lighter SDK not available.")

    def get_hyperliquid(self):
        print("Fetching Hyperliquid...")
        url = "https://api.hyperliquid.xyz/info"
        try:
            res = requests.post(url, json={"type": "predictedFundings"}, headers=self.headers, timeout=5)
            data = res.json()
            rates = {}
            for item in data:
                if len(item) > 1:
                    sym = item[0]
                    for ex in item[1]:
                        if ex[0] == 'HlPerp':
                            raw_rate = float(ex[1]['fundingRate'])
                            # Hyperliquid returns 1h rate as decimal (e.g. 0.0001)
                            # APR = Rate * 24h * 365d * 100 (to get %)
                            apr = raw_rate * 24 * 365 * 100
                            rates[sym] = {'rate': raw_rate, 'apr': apr, 'interval': '1h'}
            return rates
        except Exception as e:
            print(f"❌ Hyperliquid Error: {e}")
            return {}

    def get_aster(self):
        print("Fetching Aster...")
        url = "https://fapi.apollox.finance/fapi/v1/premiumIndex"
        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            data = res.json()
            rates = {}
            for item in data:
                sym = item['symbol'].replace('USDT', '')
                raw_rate = float(item['lastFundingRate'])
                # Aster returns 8h rate as decimal
                # APR = Rate * 3 * 365d * 100
                apr = raw_rate * 3 * 365 * 100
                rates[sym] = {'rate': raw_rate, 'apr': apr, 'interval': '8h'}
            return rates
        except Exception as e:
            print(f"❌ Aster Error: {e}")
            return {}

    async def _get_lighter_async(self):
        if not SDK_AVAILABLE or not LIGHTER_API_KEY or "YOUR_" in LIGHTER_API_KEY:
            return {}

        config = Configuration.get_default()
        config.api_key["apiKey"] = LIGHTER_API_KEY
        api_client = ApiClient(configuration=config)
        order_api = OrderApi(api_client)
        candlestick_api = CandlestickApi(api_client)

        try:
            # 1) Get Order Books for Market IDs
            ob_params = order_api._order_books_serialize(
                market_id=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0
            )
            ob_resp = await api_client.call_api(*ob_params, _request_timeout=None)
            await ob_resp.read()
            ob_json = json.loads(ob_resp.data.decode("utf-8"))
            order_books = ob_json.get("order_books", [])

            now_ms = int(time.time() * 1000)
            one_day_ms = 24 * 60 * 60 * 1000
            rates = {}

            for ob in order_books:
                symbol = str(ob.get("symbol", "")).replace("_USDC", "").replace("USDC", "")
                market_id = ob.get("market_id")
                if market_id is None:
                    continue

                # 2) Get Fundings
                try:
                    fd_params = candlestick_api._fundings_serialize(
                        market_id=market_id,
                        resolution="1h",
                        start_timestamp=now_ms - one_day_ms,
                        end_timestamp=now_ms,
                        count_back=1,
                        _request_auth=None, _content_type=None, _headers=None, _host_index=0
                    )
                    fd_resp = await api_client.call_api(*fd_params, _request_timeout=None)
                    await fd_resp.read()
                    fd_json = json.loads(fd_resp.data.decode("utf-8"))
                    fundings_list = fd_json.get("fundings", [])
                except Exception:
                    continue

                if not fundings_list:
                    continue

                last = fundings_list[-1]
                try:
                    raw_rate = float(last.get("rate", 0))
                except (TypeError, ValueError):
                    continue

                # --- CORRECTED CALCULATION ---
                # Removed "* 100" as requested.
                # Assuming raw_rate is already percentage-scaled (e.g. 0.01 for 0.01%)
                # OR user indicated raw_rate * 24 * 365 is the correct APR value.
                apr = raw_rate * 24 * 365 
                
                rates[symbol] = {
                    "rate": raw_rate,
                    "apr": apr,
                    "interval": "1h",
                }

            return rates
        except Exception as e:
            print(f"⚠️ Lighter SDK Fetch Error: {e}")
            return {}
        finally:
            try:
                await api_client.close()
            except Exception:
                pass

    def get_lighter(self):
        print("Fetching Lighter...")
        try:
            return asyncio.run(self._get_lighter_async())
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self._get_lighter_async())
            except Exception as e:
                print(f"⚠️ Lighter event loop error: {e}")
                return {}

    def run(self):
        hl = self.get_hyperliquid()
        aster = self.get_aster()
        lighter = self.get_lighter()

        all_syms = set(hl.keys()) | set(aster.keys()) | set(lighter.keys())
        opportunities = []

        print(f"\nAnalyzing {len(all_syms)} symbols for arbitrage...\n")

        for sym in all_syms:
            venues = []
            if sym in hl: venues.append(('Hyperliquid', hl[sym]))
            if sym in aster: venues.append(('Aster', aster[sym]))
            if sym in lighter: venues.append(('Lighter', lighter[sym]))

            if len(venues) < 2:
                continue

            # Sort by APR High -> Low
            venues.sort(key=lambda x: x[1]['apr'], reverse=True)

            short_venue = venues[0]
            long_venue = venues[-1]

            spread_apr = short_venue[1]['apr'] - long_venue[1]['apr']

            if spread_apr > self.min_apr_diff:
                opportunities.append({
                    'Symbol': sym,
                    'Long': f"{long_venue[0]} ({long_venue[1]['apr']:.1f}%)",
                    'Short': f"{short_venue[0]} ({short_venue[1]['apr']:.1f}%)",
                    'Spread APR': spread_apr
                })

        if opportunities:
            df = pd.DataFrame(opportunities)
            df = df.sort_values(by='Spread APR', ascending=False)
            df['Spread APR'] = df['Spread APR'].apply(lambda x: f"{x:.2f}%")
            print("💰 ARBITRAGE OPPORTUNITIES 💰")
            print(df.to_string(index=False))
        else:
            print("No opportunities > 5% spread found.")

if __name__ == "__main__":
    bot = ArbEngine()
    bot.run()
