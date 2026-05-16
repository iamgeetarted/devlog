# devlog

## What's New in v1.9.0

### `devlog month [YYYY-MM] [--ai]` — Monthly summary & retro

View all entries for a calendar month grouped by ISO week, with tag breakdown and activity stats. Add `--ai` to stream a concise monthly retrospective from Claude.

```bash
devlog month               # current month
devlog month 2026-04       # specific month
devlog month --ai          # with AI monthly retro
devlog month 2026-04 --ai  # specific month + AI retro
```

```
╭─ Month — May 2026 ──────────────────────────────╮
│  Week       n                                    │
│  2026-W19   8  ██████████████████               │
│  2026-W20   5  ███████████                      │
│  2026-W21   3  ██████                           │
╰─────────────────────────────────────────────────╯
╭─ Tags this month ────────╮
│  Tag    n                 │
│  feat   9                 │
│  bug    4                 │
│  deploy 3                 │
╰──────────────────────────╯

  May 2026:  20 entries  ·  12/31 active days  ·  3 active weeks  ·  avg 0.6/day
```

### `devlog import <file>` — Bulk import entries

Import entries from a plain-text file (one line per entry), a JSON array, or a CSV export. Supports `--dry-run` to preview, `--date` to override the date, and `--tag` to set a default tag.

```bash
# Plain text: one entry per line, optional [tag] prefix
devlog import notes.txt
devlog import notes.txt --date 2026-05-10 --tag feat

# JSON array: [{text, tag?, date?, time?}, ...]
devlog import entries.json

# CSV (with id,date,time,tag,text columns)
devlog import log.csv

# Preview without saving
devlog import notes.txt --dry-run
```

Plain text format:
```
[feat] finished the auth refactor
[bug] fixed null pointer in session handler
deployed v2.1 to staging
```

### `devlog add --suggest-tag` / `-s` — AI tag suggestion

Add `-s` to any `devlog add` command to get an AI-suggested tag when you haven't specified one. Claude Haiku analyses the entry text and recommends a tag.

```bash
devlog add -s "fixed a race condition in the job queue"
# ✓ Logged: fixed a race condition in the job queue  (2026-05-16 14:22)
#   AI suggests tag: bug  Accept? devlog edit 47 -t bug
```

---

## What's New in v1.8.0

### Mood & Energy Tracking — `devlog add -m 4 "..."` + `devlog mood`

Track your daily mood/energy (1–5) alongside journal entries. View a colour-coded chart of how you've been feeling over time, with optional AI insights to surface trends.

```bash
# Log with mood (1=rough, 2=meh, 3=okay, 4=good, 5=great)
devlog add -m 5 "Shipped the auth refactor — feeling great"
devlog add -m 2 "Debugging a gnarly race condition all day"

# Show mood chart for the last 30 days
devlog mood
devlog mood --days 7

# Stream an AI analysis of your mood trends
devlog mood --insight
```

```
╭─ Mood — last 30 days ───────────────────────────────╮
│  Date        Avg  Chart              Entries          │
│  2026-05-12  4.5  ████████████████   2               │
│  2026-05-13  3.0  █████████          1               │
│  2026-05-14  4.0  ████████████       3               │
╰─────────────────────────────────────────────────────╯
  Average: 3.8/5 🙂 good  ·  12 days with mood data
```

### HTML Export — `devlog export -f html -o log.html`

Generate a polished, self-contained HTML report from all (or filtered) entries. Dark-themed, mobile-friendly, with tag badges, mood indicators, and an activity summary — no external assets required.

```bash
devlog export -f html -o devlog.html          # all entries
devlog export -f html --since 2026-05-01 -o may.html
```

### Daily Reminder — `devlog remind`

Drop into your shell startup or a cron job. Prints a gentle nudge if you haven't logged anything today; exits 0 if you have (scriptable).

```bash
# ~/.bashrc or ~/.zshrc
devlog remind || true

# Use in scripts:
devlog remind && echo "Already logged today" || echo "Remember to log!"
```

Customise the message in `~/.devlog.toml`:
```toml
remind_message = "Hey! Log your progress before you forget."
```

---

## What's New in v1.7.0

### `devlog heatmap [--weeks N]` — GitHub-style activity calendar

Renders a colour-coded contribution grid for the last N weeks (default: 16) directly in your terminal — immediately shows quiet patches and productive sprints at a glance.

```bash
devlog heatmap            # last 16 weeks
devlog heatmap --weeks 8  # last 8 weeks
```

```
╭─ Activity heatmap — last 16 weeks ─────────────────────────────────────────────╮
│     01/27  02/03  02/10  02/17  02/24  03/03 ...                               │
│ Mon  ▪      ■      ·      ■      ·      ·                                       │
│ Tue  ■      ■      ▪      ■      ·      ■                                       │
│ Wed  ·      ■      ·      ·      ▪      ■                                       │
│ Thu  ■      ■      ■      ·      ■      ·                                       │
│ Fri  ■      ·      ■      ■      ■      ■                                       │
│ Sat  ·      ·      ·      ·      ·      ·                                       │
│ Sun  ·      ·      ·      ·      ·      ·                                       │
╰──────────────────────────────────────────────────────────────────────────────╯

  Total: 89 entries  ·  Active: 42 days  ·  Peak: 7/day
  Legend: · 0  ▪ 1  ■ 2-3  ■ 4-6  ■ 7+
```

### `devlog completions [bash|zsh|fish]` — Shell auto-completion

Generate and install a completion script for your shell so Tab-completion works for all devlog subcommands, flags, and sub-subcommands.

```bash
# bash — add to ~/.bashrc
eval "$(devlog completions bash)"

# zsh — add to ~/.zshrc
eval "$(devlog completions zsh)"

# fish — install permanently
devlog completions fish > ~/.config/fish/completions/devlog.fish
```

After sourcing, pressing `Tab` after `devlog` completes subcommands, `devlog goal <Tab>` lists goal sub-commands, `devlog export -f <Tab>` lists format choices, etc.

### `devlog tags` — Tag management

List every tag in your journal with entry counts and a visual frequency bar, or bulk-rename a tag across all historical entries in one command.

```bash
devlog tags list             # rich table of all tags and counts
devlog tags rename bug fix   # rename 'bug' → 'fix' everywhere
```

```
╭─ Tags (4 unique, 63 tagged entries) ──────────────────────────╮
│ Tag      Count                                                 │
│ feat        28  ████████████████████                           │
│ bug         15  ███████████                                    │
│ deploy       9  ██████                                         │
│ chore       11  ████████                                       │
╰───────────────────────────────────────────────────────────────╯

✓ Renamed tag 'bug' → 'fix' across 15 entries
```

---

## What's New in v1.6.0

### Weekly Goals System (`devlog goal`)

Track your weekly intentions alongside your journal. Set goals, mark them complete, and run an AI accountability check that compares your open goals against your actual log entries.

```bash
# Add a goal for the current ISO week
devlog goal add "Ship the search API refactor"
devlog goal add "Write unit tests for auth module"

# List goals (all weeks, or filter to a specific week)
devlog goal list
devlog goal list --week 2026-W19

# Mark a goal done
devlog goal done 1

# AI accountability check: Claude compares goals vs journal entries
export ANTHROPIC_API_KEY=sk-ant-...
devlog goal check
```

```
Weekly Goals — 2026-W19  (1/2 marked done)
╭────────────────────────────────────────────────────────────╮
│ ID  Week      Status   Goal                                 │
│  1  2026-W19  ✓ done   Ship the search API refactor        │
│  2  2026-W19  ○ open   Write unit tests for auth module    │
╰────────────────────────────────────────────────────────────╯

Goal Check — 2026-W19  (1/2 marked done)

- **Search API refactor** — Multiple entries mention completing and deploying
  the refactor on Wednesday. Looks fully done ✓
- **Unit tests for auth** — No entries reference auth tests yet. You have
  2 days left in the week — consider blocking 90 minutes tomorrow.
```

### Entry Templates (`-T template_name`)

Define reusable entry prefixes in `~/.devlog.toml` to enforce consistent standup formats, PR review notes, or any structured entry type — without re-typing the prefix every time.

```toml
# ~/.devlog.toml
[templates]
standup  = "Standup: "
review   = "PR review: "
incident = "Incident: "
```

```bash
devlog add -T standup "merged auth PR, working on caching layer next"
# → logs: "Standup: merged auth PR, working on caching layer next"

devlog add -T review "#1234 approved — minor nits on error handling"
# → logs: "PR review: #1234 approved — minor nits on error handling"
```

### Date Range Filtering (`--since` / `--until`)

Filter `log` and `export` commands to an arbitrary date range — ideal for monthly retros, sprint reviews, or exporting a specific time slice.

```bash
# Show entries for a specific week range
devlog log --since 2026-05-01 --until 2026-05-07

# Export last sprint as Markdown
devlog export --since 2026-04-21 --until 2026-05-02 -f markdown -o sprint-42.md

# Export everything from May as JSON
devlog export --since 2026-05-01 -f json > may.json
```

---

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
