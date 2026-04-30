# devlog

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
