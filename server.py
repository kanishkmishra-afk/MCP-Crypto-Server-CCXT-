# server.py
import asyncio
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import ccxt.async_support as ccxt
from services.crypto_service import CryptoService, ExchangeError
from services.cache import TTLCache


app = FastAPI(title="MCP Crypto Server (CCXT)")
# Simple in-memory cache (ticker -> (value, expiry))
cache = TTLCache(ttl_seconds=5)
crypto = CryptoService(cache=cache)
# WebSocket manager for broadcasting price updates
class ConnectionManager:
def __init__(self):
self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
async def connect(self, websocket: WebSocket):
await websocket.accept()
self.active_connections[websocket] = {"subscriptions": set()}
def disconnect(self, websocket: WebSocket):
if websocket in self.active_connections:
del self.active_connections[websocket]
async def broadcast(self, message: dict):
to_remove = []
for ws in list(self.active_connections.keys()):
try:
await ws.send_text(json.dumps(message))
except Exception:
to_remove.append(ws)
for ws in to_remove:
self.disconnect(ws)

def subscribe(self, websocket: WebSocket, symbol: str):
if websocket in self.active_connections:
self.active_connections[websocket]["subscriptions"].add(symbol)
def unsubscribe(self, websocket: WebSocket, symbol: str):
if websocket in self.active_connections:
self.active_connections[websocket]
["subscriptions"].discard(symbol)
manager = ConnectionManager()
@app.on_event("startup")
async def startup_event():
# can initialize shared resources here
app.state.stream_task = asyncio.create_task(price_stream_loop())
@app.on_event("shutdown")
async def shutdown_event():
task = app.state.stream_task
if task:
task.cancel()
@app.post("/mcp/tool")
async def mcp_tool(payload: dict):
"""
 Expected payload shape:
 {
 "action": "get_ticker" | "get_ohlcv",
 "params": { ... }
 }
 """
action = payload.get("action")
params = payload.get("params", {})
try:
if action == "get_ticker":
exchange = params.get("exchange", "binance")
symbol = params.get("symbol", "BTC/USDT")
res = await crypto.get_ticker(exchange, symbol)
return JSONResponse(content={"status": "ok", "data": res})
elif action == "get_ohlcv":
exchange = params.get("exchange", "binance")
symbol = params.get("symbol", "BTC/USDT")
timeframe = params.get("timeframe", "1m")
limit = int(params.get("limit", 100))
res = await crypto.get_ohlcv(exchange, symbol,
timeframe=timeframe, limit=limit)
return JSONResponse(content={"status": "ok", "data": res})

else:
raise HTTPException(status_code=400, detail=f"Unknown action:
{action}")
except ExchangeError as e:
raise HTTPException(status_code=502, detail=str(e))
except Exception as e:
raise HTTPException(status_code=500, detail=str(e))
@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
await manager.connect(websocket)
try:
while True:
data = await websocket.receive_text()
# JSON messages like {"op":"subscribe","symbol":"BTC/USDT"}
try:
msg = json.loads(data)

except Exception:
await websocket.send_text(json.dumps({"error": "invalid
json"}))
continue
op = msg.get("op")
symbol = msg.get("symbol")
if op == "subscribe" and symbol:
manager.subscribe(websocket, symbol)
await websocket.send_text(json.dumps({"subscribed": symbol}))
elif op == "unsubscribe" and symbol:
manager.unsubscribe(websocket, symbol)
await websocket.send_text(json.dumps({"unsubscribed":
symbol}))
else:
await websocket.send_text(json.dumps({"error": "unknown
op"}))
except WebSocketDisconnect:
manager.disconnect(websocket)
async def price_stream_loop():
"""Background loop that periodically fetches prices for subscribed
symbols and broadcasts."""
try:
while True:
# gather all subscribed symbols
all_symbols = set()
for meta in manager.active_connections.values():
all_symbols.update(meta["subscriptions"])

for symbol in list(all_symbols):
try:
# default to binance if not specified
price = await crypto.get_ticker("binance", symbol)
await manager.broadcast({"type": "ticker", "symbol":
symbol, "data": price})
except Exception:
# skip errors for individual symbols
pass
await asyncio.sleep(2)
except asyncio.CancelledError:
return
