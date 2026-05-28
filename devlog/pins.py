"""Pinned entry board — persist a set of pinned entry IDs."""

from __future__ import annotations

import json
from pathlib import Path
from .storage import DATA_DIR


_PINS_FILE = DATA_DIR / "pins.json"


def _load() -> list[int]:
    if not _PINS_FILE.exists():
        return []
    try:
        return json.loads(_PINS_FILE.read_text())
    except Exception:
        return []


def _save(pins: list[int]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    _PINS_FILE.write_text(json.dumps(sorted(set(pins)), indent=2))


def pin_entry(entry_id: int) -> bool:
    pins = _load()
    if entry_id in pins:
        return False
    pins.append(entry_id)
    _save(pins)
    return True


def unpin_entry(entry_id: int) -> bool:
    pins = _load()
    if entry_id not in pins:
        return False
    pins = [p for p in pins if p != entry_id]
    _save(pins)
    return True


def get_pinned_ids() -> list[int]:
    return _load()
