"""Habit tracking storage and logic for devlog."""

from __future__ import annotations

import json
from datetime import date, timedelta

from .storage import DATA_DIR

HABITS_FILE = DATA_DIR / "habits.json"


def _load() -> dict:
    if not HABITS_FILE.exists():
        return {"habits": [], "checkins": {}}
    try:
        return json.loads(HABITS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"habits": [], "checkins": {}}


def _save(data: dict) -> None:
    HABITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HABITS_FILE.write_text(json.dumps(data, indent=2))


def add_habit(name: str) -> dict:
    """Add a new habit. Raises ValueError if name already exists."""
    data = _load()
    if any(h["name"].lower() == name.lower() for h in data["habits"]):
        raise ValueError(f"Habit '{name}' already exists.")
    next_id = max((h["id"] for h in data["habits"]), default=0) + 1
    habit = {"id": next_id, "name": name, "created": date.today().isoformat()}
    data["habits"].append(habit)
    _save(data)
    return habit


def delete_habit(habit_id: int) -> bool:
    data = _load()
    before = len(data["habits"])
    data["habits"] = [h for h in data["habits"] if h["id"] != habit_id]
    if len(data["habits"]) == before:
        return False
    # Prune orphaned checkins
    data["checkins"] = {
        day: {hid: v for hid, v in day_data.items() if int(hid) != habit_id}
        for day, day_data in data["checkins"].items()
    }
    _save(data)
    return True


def check_habit(habit_id: int, day: str | None = None, note: str = "") -> bool:
    """Mark a habit done for *day* (default: today)."""
    data = _load()
    if not any(h["id"] == habit_id for h in data["habits"]):
        return False
    day = day or date.today().isoformat()
    data["checkins"].setdefault(day, {})[str(habit_id)] = {"done": True, "note": note}
    _save(data)
    return True


def uncheck_habit(habit_id: int, day: str | None = None) -> bool:
    """Remove a check-in for *day* (default: today)."""
    data = _load()
    day = day or date.today().isoformat()
    checkin = data["checkins"].get(day, {})
    if str(habit_id) not in checkin:
        return False
    del checkin[str(habit_id)]
    data["checkins"][day] = checkin
    _save(data)
    return True


def get_streak(habit_id: int) -> int:
    """Return consecutive days ending today with a completed check-in."""
    checkins = _load()["checkins"]
    today = date.today()
    streak = 0
    d = today
    while True:
        if checkins.get(d.isoformat(), {}).get(str(habit_id), {}).get("done"):
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak


def list_habits() -> list[dict]:
    return _load()["habits"]


def get_status(days: int = 14) -> list[dict]:
    """Return habits enriched with recent history, streak, and completion rate."""
    data = _load()
    today = date.today()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    result = []
    for habit in data["habits"]:
        hid = str(habit["id"])
        history = [
            bool(data["checkins"].get(d, {}).get(hid, {}).get("done"))
            for d in date_range
        ]
        streak = get_streak(habit["id"])
        done_count = sum(history)
        result.append({
            "id": habit["id"],
            "name": habit["name"],
            "streak": streak,
            "done_count": done_count,
            "rate": round(done_count / days * 100),
            "history": history,
            "dates": date_range,
        })
    return result
