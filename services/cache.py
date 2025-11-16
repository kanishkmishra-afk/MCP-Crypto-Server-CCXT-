# services/cache.py
import time
from typing import Any, Optional
class TTLCache:
def __init__(self, ttl_seconds: int = 5):
self.ttl = ttl_seconds
self._store = {} # key -> (value, expiry)
def set(self, key: str, value: Any):
self._store[key] = (value, time.time() + self.ttl)
def get(self, key: str) -> Optional[Any]:
item = self._store.get(key)
if not item:
return None
value, expiry = item
if time.time() > expiry:
del self._store[key]
return None 
return value

def clear(self):
self._store.clear()