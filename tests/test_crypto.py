# tests/test_crypto.py
import asyncio
import pytest
from fastapi import status
from httpx import AsyncClient
import server
@pytest.mark.asyncio
async def test_get_ticker_mock(monkeypatch):
async def fake_fetch_ticker(self, symbol):
return {
"symbol": symbol,
"timestamp": 123456,
"datetime": "2025-01-01T00:00:00Z",
"last": 100.0,
"bid": 99.0,
"ask": 101.0,
"info": {"mock": True},
}
# monkeypatch the ccxt exchange class generator
class DummyExchange:
async def fetch_ticker(self, symbol):
return await fake_fetch_ticker(self, symbol)
async def dummy_get_exchange(self, exchange_id):
return DummyExchange()
monkeypatch.setattr(server.crypto, "_get_exchange", dummy_get_exchange)
async with AsyncClient(app=server.app, base_url="http://test") as ac:
payload = {"action": "get_ticker", "params": {"exchange": "binance",
"symbol": "BTC/USDT"}}

r = await ac.post("/mcp/tool", json=payload)
assert r.status_code == status.HTTP_200_OK
data = r.json()
assert data["status"] == "ok"
assert data["data"]["last"] == 100.0
@pytest.mark.asyncio
async def test_get_ohlcv_mock(monkeypatch):
async def fake_fetch_ohlcv(self, symbol, timeframe="1m", limit=10):
return [[1234567890000, 1, 2, 0.5, 1.5, 100]] * limit
class DummyExchange:
async def fetch_ohlcv(self, symbol, timeframe="1m", limit=10):
return await fake_fetch_ohlcv(self, symbol, timeframe, limit)
async def dummy_get_exchange(self, exchange_id):
return DummyExchange()
monkeypatch.setattr(server.crypto, "_get_exchange", dummy_get_exchange)
async with AsyncClient(app=server.app, base_url="http://test") as ac:
payload = {"action": "get_ohlcv", "params": {"exchange": "binance",
"symbol": "BTC/USDT", "timeframe": "1m", "limit": 5}}
r = await ac.post("/mcp/tool", json=payload)
assert r.status_code == status.HTTP_200_OK
data = r.json()
assert data["status"] == "ok"
assert len(data["data"]) == 5
