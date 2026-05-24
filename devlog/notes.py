"""Long-form note storage for devlog."""
import json
from datetime import datetime
from pathlib import Path

NOTES_FILE = Path.home() / ".devlog_notes.json"


def _load_notes() -> list[dict]:
    if not NOTES_FILE.exists():
        return []
    return json.loads(NOTES_FILE.read_text())


def _save_notes(notes: list[dict]) -> None:
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


def add_note(title: str, body: str, tag: str | None = None) -> dict:
    notes = _load_notes()
    note_id = max((n["id"] for n in notes), default=0) + 1
    now = datetime.now()
    note = {
        "id": note_id,
        "title": title,
        "body": body,
        "tag": tag,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "updated": now.isoformat(),
    }
    notes.append(note)
    _save_notes(notes)
    return note


def list_notes(tag: str | None = None, limit: int | None = None) -> list[dict]:
    notes = _load_notes()
    if tag:
        notes = [n for n in notes if n.get("tag") == tag]
    notes = sorted(notes, key=lambda n: n["updated"], reverse=True)
    return notes[:limit] if limit else notes


def get_note(note_id: int) -> dict | None:
    return next((n for n in _load_notes() if n["id"] == note_id), None)


def delete_note(note_id: int) -> bool:
    notes = _load_notes()
    new = [n for n in notes if n["id"] != note_id]
    if len(new) == len(notes):
        return False
    _save_notes(new)
    return True
