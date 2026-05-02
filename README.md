# devlog

## What's New in v1.2.0

### Rich Terminal UI
All entry views (`today`, `yesterday`, `log`, `search`) now render in a polished Rich table with rounded borders, colour-coded columns, and a Panel title instead of plain ANSI text.

### `devlog search <keyword>` — full-text search
Search across all journal entries with an optional tag filter:

```bash
devlog search "auth middleware"
devlog search refactor -t feat
```

### `devlog summarize [date]` — AI-powered daily summary
Uses the Anthropic API (claude-haiku-4-5-20251001) to produce a concise paragraph summarising the day's work. Requires `ANTHROPIC_API_KEY` set in your environment:

```bash
export ANTHROPIC_API_KEY=sk-...
devlog summarize              # summarise today
devlog summarize 2026-04-28   # summarise a specific date
```

---

A minimal CLI daily journal for developers. Log what you worked on, view entries by date, and export clean Markdown — all from the terminal.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Add an entry
devlog add "fixed null pointer in auth middleware"
devlog add "refactored DB connection pool" -t feat
devlog add "deployed v2.1.3 to prod" -t deploy

# View today's log
devlog today

# View yesterday
devlog yesterday

# View all entries or a specific date
devlog log
devlog log 2026-04-28

# Export as Markdown
devlog export
devlog export 2026-04-28 -o april28.md

# Delete an entry by ID
devlog delete 3
```

## Output example

```
Today — 2026-04-30
────────────────────────────────────────
  1.  09:14  fixed null pointer in auth middleware
  2.  10:32  [feat] refactored DB connection pool
  3.  14:55  [deploy] deployed v2.1.3 to prod
```

## Data

Entries are stored in `~/.devlog/entries.json`. No accounts, no cloud, no tracking.

## License

MIT
