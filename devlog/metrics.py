"""Cross-dimensional productivity metrics for devlog."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from statistics import mean, stdev
from typing import Any


_WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def compute_metrics(entries: list[dict], days: int = 30) -> dict[str, Any]:
    """Compute cross-dimensional productivity metrics over the last *days* days."""
    today = date.today()
    cutoff = (today - timedelta(days=days)).isoformat()
    window = [e for e in entries if e.get("date", "") >= cutoff]

    dates_with_entries: Counter = Counter(e["date"] for e in window)
    active_days = len(dates_with_entries)
    velocity = len(window) / days if days else 0

    tag_counts: Counter = Counter(e["tag"] for e in window if e.get("tag"))
    top_tags = tag_counts.most_common(5)

    # Average mood per tag (only for tags with ≥2 mood data points)
    mood_by_tag: dict[str, list[int]] = defaultdict(list)
    for e in window:
        if e.get("mood") and e.get("tag"):
            mood_by_tag[e["tag"]].append(e["mood"])
    tag_moods = {
        tag: round(mean(moods), 2)
        for tag, moods in mood_by_tag.items()
        if len(moods) >= 2
    }
    best_mood_tag = max(tag_moods, key=lambda t: tag_moods[t]) if tag_moods else None
    worst_mood_tag = min(tag_moods, key=lambda t: tag_moods[t]) if tag_moods else None

    hour_counts: Counter = Counter()
    for e in window:
        try:
            hour_counts[int(e["time"].split(":")[0])] += 1
        except (ValueError, IndexError, KeyError):
            pass
    peak_hour = max(hour_counts, key=lambda h: hour_counts[h]) if hour_counts else None

    weekday_counts: Counter = Counter()
    for e in window:
        try:
            weekday_counts[date.fromisoformat(e["date"]).weekday()] += 1
        except ValueError:
            pass
    busiest_weekday_idx = (
        max(weekday_counts, key=lambda d: weekday_counts[d]) if weekday_counts else None
    )

    all_moods = [e["mood"] for e in window if e.get("mood")]
    avg_mood = round(mean(all_moods), 2) if all_moods else None
    mood_variance = round(stdev(all_moods), 2) if len(all_moods) >= 2 else None

    mid_cutoff = (today - timedelta(days=days // 2)).isoformat()
    first_half = sum(1 for e in window if e.get("date", "") < mid_cutoff)
    second_half = sum(1 for e in window if e.get("date", "") >= mid_cutoff)
    velocity_trend = (
        "improving" if second_half > first_half
        else "declining" if second_half < first_half
        else "stable"
    )

    return {
        "days": days,
        "total_entries": len(window),
        "active_days": active_days,
        "velocity": round(velocity, 2),
        "velocity_trend": velocity_trend,
        "top_tags": top_tags,
        "tag_moods": tag_moods,
        "best_mood_tag": best_mood_tag,
        "worst_mood_tag": worst_mood_tag,
        "peak_hour": peak_hour,
        "busiest_weekday": (
            _WEEKDAY_NAMES[busiest_weekday_idx] if busiest_weekday_idx is not None else None
        ),
        "avg_mood": avg_mood,
        "mood_variance": mood_variance,
        "weekday_counts": {_WEEKDAY_NAMES[k]: v for k, v in weekday_counts.items()},
    }
