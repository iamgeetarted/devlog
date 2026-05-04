"""Load user configuration from ~/.devlog.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

_CONFIG_FILE = Path.home() / ".devlog.toml"
_VALID_KEYS = {"data_dir", "default_tag", "default_export_format"}


def load_config() -> dict[str, Any]:
    """Return config from ~/.devlog.toml; empty dict if absent."""
    try:
        with open(_CONFIG_FILE, "rb") as f:
            raw = tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML in {_CONFIG_FILE}: {e}") from e

    unknown = set(raw) - _VALID_KEYS
    if unknown:
        raise ValueError(f"Unknown config key(s): {', '.join(sorted(unknown))}")

    if "default_export_format" in raw and raw["default_export_format"] not in {"markdown", "json", "csv"}:
        raise ValueError("config 'default_export_format' must be one of: markdown, json, csv")

    return raw
