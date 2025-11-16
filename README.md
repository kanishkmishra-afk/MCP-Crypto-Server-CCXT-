# MCP Crypto Server
## What this is
A small Python FastAPI server that exposes MCP-style tool endpoints and a
WebSocket stream to fetch cryptocurrency data using CCXT. Designed for
evaluation: reliability, test coverage, and clarity.
## Setup
1. Create a Python 3.10+ virtualenv
2. Install requirements: `pip install -r requirements.txt`
3. Run server locally:
 `uvicorn server:app --reload --port 8000`
## Endpoints
- POST /mcp/tool
 - JSON body: {"action": "get_ticker", "params":
{"exchange":"binance","symbol":"BTC/USDT"}}
- action: get_ticker | get_ohlcv
- WebSocket /ws/stream
 - send JSON: {"op":"subscribe","symbol":"BTC/USDT"}
 - server will push `{"type":"ticker","symbol":...,"data":...}` messages
periodically
## Tests
Run:
pytest -q
## Design notes (for a JavaScript developer)
- **FastAPI** ~ Express: similar routing model. Use async def handlers
instead of `async (req,res) => {}`.
- **ccxt**: same API shape between JS and Python. In JS you call `await
exchange.fetchTicker(symbol)`; in Python `await
exchange.fetch_ticker(symbol)` (snake_case).
- **Caching**: TTL cache here is like `node-cache` or `lru-cache` in Node.
- **WebSocket**: FastAPI uses `WebSocket` object; in Node you'd use `ws` or
Socket.IO.
## Assumptions
- Default exchange: `binance` (no API keys required for public endpoints)
- Symbols are CCXT-style (e.g., `BTC/USDT`)
- Small in-memory cache is acceptable for assignment. For production, use
Redis.
