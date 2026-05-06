# devlog

## What's New in v1.5.0

### `devlog dash` — Live Rich Dashboard

A live-updating full-screen terminal dashboard showing today's entries, your streak, total count, and tag breakdown — refreshed every 2 seconds. Press Ctrl+C to exit.

```bash
devlog dash
```

```
╭─ devlog dashboard ────────────────────────────────────────────╮
│                       devlog dashboard                        │
╰───────────────────────────────────────────────────────────────╯
╭─ Today — 2026-05-06 (3 entries) ──╮  ╭─ Stats ──────────────╮
│  ID  Time  Tag        Entry        │  │ Streak       3 days  │
│   1  09:14            fixed bug    │  │ Total           47   │
│   2  11:00  feat      added auth   │  │   [feat]        12   │
│   3  14:30  deploy    released v2  │  │   [bug]          7   │
╰────────────────────────────────────╯  ╰──────────────────────╯
╭─ Refreshed 14:32:10 · Ctrl+C to exit ────────────────────────╮
```

### `devlog review [--week YYYY-WNN]` — AI Weekly Productivity Review

Streams a concise weekly productivity review from Claude (claude-haiku-4-5-20251001), covering accomplishments, work patterns, and one actionable suggestion for next week. Requires `ANTHROPIC_API_KEY`.

```bash
export ANTHROPIC_API_KEY=sk-...
devlog review               # review current week
devlog review --week 2026-W18   # review a specific ISO week
```

### `--format` flag for `today` and `log` commands

Output today's or any day's entries as JSON, Markdown, or CSV — pipe them directly into other tools.

```bash
devlog today --format json
devlog today -f csv
devlog log 2026-05-06 --format markdown
devlog log -f json | jq '.[].text'
```

---

## What's New in v1.3.0

### `devlog stats [--days N] [--all-days]` — activity dashboard

Renders a Rich bar chart of entries per day for the last N days (default 30), a tag-frequency breakdown, and your current consecutive-logging streak — all in one glance.

```bash
devlog stats
devlog stats --days 7
devlog stats --days 90 --all-days    # include days with zero entries
```

```
╭─ Entries — last 30 days ────────────────────────────────╮
│ Date         n                                           │
│ 2026-04-10   3  ████████████████████████                │
│ 2026-04-14   1  ████████                                 │
│ 2026-04-28   5  ████████████████████████████████████████ │
╰─────────────────────────────────────────────────────────╯
╭─ Tag breakdown ───╮
│ Tag      Count    │
│ feat        12    │
│ bug          7    │
│ deploy       4    │
╰───────────────────╯

  Streak: 3 consecutive days  ·  Total entries: 47
```

### `devlog edit <id> [new text] [-t TAG]` — in-place entry editing

Modify the text or tag of any entry by ID without deleting and re-adding it.

```bash
devlog edit 5 "fixed the null pointer in auth middleware"   # change text
devlog edit 5 -t bug                                        # change tag only
devlog edit 5 "updated copy" -t docs                        # change both
devlog edit 5 -t                                            # clear tag
```

---

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

## What's New in v1.4.0

### Config File (`~/.devlog.toml`)
Persist your preferences without passing flags every time:
```toml
data_dir = "~/notes/devlog"      # custom storage location
default_tag = "work"             # applied when -t is omitted
default_export_format = "json"   # used by `devlog export`
```

### Structured Export (`--format json|csv|markdown`)
Export your log in machine-readable formats:
```bash
devlog export --format json > entries.json
devlog export --format csv -o log.csv
devlog export 2026-05-04 --format json   # single day as JSON
```

### Week View (`devlog week`)
Browse a full ISO week at a glance:
```bash
devlog week              # current week
devlog week 2026-W18     # specific ISO week
```
