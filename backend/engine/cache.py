"""
Thread-safe LRU Cache implementation for legal citation verification payloads.
"""
from collections import OrderedDict
from threading import Lock
from typing import Optional, Dict, Any
import re

class LRUCache:
    """
    High-performance, synchronous LRU (Least Recently Used) cache.
    Safeguards server RAM by enforcing a strict storage capacity constraint.
    """
    def __init__(self, maxsize: int = 1024):
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.maxsize = maxsize
        self.lock = Lock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key: str, value: Dict[str, Any]) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)

# Singleton memory pool instance
lru_cache_pool = LRUCache(maxsize=1024)

def normalize_cache_key(citation_text: str) -> str:
    """
    Derives a unique, normalized string from the incoming legal citation token.
    (e.g., lowercase, stripped of double spaces).
    """
    return re.sub(r'\s+', ' ', citation_text.lower()).strip()

def get_cached_citation(citation_text: str) -> Optional[Dict[str, Any]]:
    """
    Dependency injection / retrieval wrapper for the LRU memory pool.
    """
    key = normalize_cache_key(citation_text)
    return lru_cache_pool.get(key)
