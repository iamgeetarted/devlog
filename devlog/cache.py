"""Disk-based cache with TTL for AI-generated text."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


_CACHE_FILE = Path.home() / ".devlog" / "ai_cache.json"
_DEFAULT_TTL = 3600  # seconds


def _load() -> dict[str, Any]:
    try:
        return json.loads(_CACHE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict[str, Any]) -> None:
    _CACHE_FILE.parent.mkdir(exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(data))


def make_key(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:24]


def cache_get(key: str) -> str | None:
    """Return cached value if present and not expired."""
    data = _load()
    entry = data.get(key)
    if entry and time.time() < entry.get("expires", 0):
        return entry["value"]
    return None


def cache_set(key: str, value: str, ttl: int = _DEFAULT_TTL) -> None:
    """Store a value with a TTL."""
    data = _load()
    # Evict expired entries to keep the file small
    now = time.time()
    data = {k: v for k, v in data.items() if v.get("expires", 0) > now}
    data[key] = {"value": value, "expires": now + ttl}
    _save(data)
