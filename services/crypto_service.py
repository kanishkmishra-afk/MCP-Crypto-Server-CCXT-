# services/crypto_service.py
import asyncio
from typing import Any, List
import ccxt.async_support as ccxt
from .cache import TTLCache
class ExchangeError(Exception):
pass
class CryptoService:
def __init__(self, cache: TTLCache, default_exchange: str = "binance"):
self.cache = cache
self.default_exchange = default_exchange
self._exchanges = {}
self._lock = asyncio.Lock()
async def _get_exchange(self, exchange_id: str):
# cached exchange instances
async with self._lock:
if exchange_id in self._exchanges:
return self._exchanges[exchange_id]
try:
ex = getattr(ccxt, exchange_id)({})
except AttributeError:
raise ExchangeError(f"Exchange '{exchange_id}' not supported
in CCXT")
self._exchanges[exchange_id] = ex
return ex

async def get_ticker(self, exchange_id: str, symbol: str) -> dict:
key = f"ticker:{exchange_id}:{symbol}"
cached = self.cache.get(key)
if cached is not None:
return cached
ex = await self._get_exchange(exchange_id)
try:
# many ccxt implementations are async methods
ticker = await ex.fetch_ticker(symbol)
# normalize commonly used fields
out = {
"symbol": ticker.get("symbol"),
"timestamp": ticker.get("timestamp"),
"datetime": ticker.get("datetime"),
"last": ticker.get("last"),
"bid": ticker.get("bid"),
"ask": ticker.get("ask"),

"info": ticker.get("info"),
}
self.cache.set(key, out)
return out
except Exception as e:
raise ExchangeError(str(e))
async def get_ohlcv(self, exchange_id: str, symbol: str, timeframe: str =
"1m", limit: int = 100) -> List[List[Any]]:
key = f"ohlcv:{exchange_id}:{symbol}:{timeframe}:{limit}"
cached = self.cache.get(key)
if cached is not None:
return cached
ex = await self._get_exchange(exchange_id)
try:
ohlcv = await ex.fetch_ohlcv(symbol, timeframe=timeframe,
limit=limit)
self.cache.set(key, ohlcv)
return ohlcv
except Exception as e:
raise ExchangeError(str(e))