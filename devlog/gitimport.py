"""Import recent git commits as devlog journal entries."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def get_recent_commits(
    repo_path: str = ".",
    since: str = "1 day ago",
    max_count: int = 50,
) -> list[dict]:
    """Run git log and return commit metadata as dicts."""
    cmd = [
        "git", "-C", repo_path, "log",
        f"--since={since}",
        f"--max-count={max_count}",
        "--format=%H|%aI|%s|%an",
        "--no-merges",
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    commits = []
    for line in out.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        sha, iso_date, subject, author = parts
        try:
            dt = datetime.fromisoformat(iso_date)
        except ValueError:
            continue
        commits.append({
            "sha": sha[:8],
            "date": dt.date().isoformat(),
            "time": dt.strftime("%H:%M"),
            "subject": subject.strip(),
            "author": author.strip(),
        })
    return commits
