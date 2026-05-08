"""Weekly goal tracking for devlog."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .storage import DATA_DIR, ensure_data_dir


def _goals_file() -> Path:
    ensure_data_dir()
    return DATA_DIR / "goals.json"


def _load_goals() -> list[dict]:
    p = _goals_file()
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_goals(goals: list[dict]) -> None:
    _goals_file().write_text(json.dumps(goals, indent=2))


def _current_week() -> str:
    d = date.today()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def add_goal(text: str, week: str | None = None) -> dict:
    """Add a new goal for the given week (default: current week)."""
    goals = _load_goals()
    goal: dict = {
        "id": max((g["id"] for g in goals), default=0) + 1,
        "text": text,
        "week": week or _current_week(),
        "done": False,
        "created": date.today().isoformat(),
    }
    goals.append(goal)
    _save_goals(goals)
    return goal


def complete_goal(goal_id: int) -> bool:
    """Mark a goal as done. Returns True if found."""
    goals = _load_goals()
    for g in goals:
        if g["id"] == goal_id:
            g["done"] = True
            _save_goals(goals)
            return True
    return False


def delete_goal(goal_id: int) -> bool:
    """Delete a goal by id. Returns True if found."""
    goals = _load_goals()
    before = len(goals)
    goals = [g for g in goals if g["id"] != goal_id]
    _save_goals(goals)
    return len(goals) < before


def list_goals(week: str | None = None) -> list[dict]:
    """Return goals, optionally filtered to a specific week."""
    goals = _load_goals()
    if week:
        return [g for g in goals if g["week"] == week]
    return goals
