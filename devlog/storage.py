import json
import os
from datetime import date
from pathlib import Path

DATA_DIR = Path.home() / ".devlog"
LOG_FILE = DATA_DIR / "entries.json"


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text("[]")


def load_entries():
    ensure_data_dir()
    return json.loads(LOG_FILE.read_text())


def save_entries(entries):
    LOG_FILE.write_text(json.dumps(entries, indent=2))


def add_entry(text: str, tag: str | None = None):
    from datetime import datetime
    entries = load_entries()
    entry = {
        "id": len(entries) + 1,
        "date": date.today().isoformat(),
        "time": datetime.now().strftime("%H:%M"),
        "text": text,
        "tag": tag,
    }
    entries.append(entry)
    save_entries(entries)
    return entry


def get_entries(day: str | None = None):
    entries = load_entries()
    if day:
        entries = [e for e in entries if e["date"] == day]
    return entries


def delete_entry(entry_id: int):
    entries = load_entries()
    before = len(entries)
    entries = [e for e in entries if e["id"] != entry_id]
    save_entries(entries)
    return len(entries) < before


def search_entries(keyword: str, tag: str | None = None) -> list[dict]:
    entries = load_entries()
    keyword_lower = keyword.lower()
    results = [e for e in entries if keyword_lower in e["text"].lower()]
    if tag:
        results = [e for e in results if e.get("tag") == tag]
    return results
