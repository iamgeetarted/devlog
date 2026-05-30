# devlog

## What's New in v2.5.0

### `devlog template` — Built-in quick-entry templates

Five built-in templates for common developer workflows (standup, retro, incident, pr-review, sprint), plus full support for custom templates defined in `~/.devlog.toml`.

```bash
devlog template list          # show all built-in and custom templates
devlog template use standup   # preview the standup template
devlog add -T standup "filled in my standup"  # use as entry prefix
```

```
╭─ Templates (5) ─────────────────────────────────────────────────────────────╮
│  Name       Kind      Preview                                               │
│  standup    built-in  ## Yesterday    ## Today    ## Blockers               │
│  retro      built-in  ## Went well    ## To improve    ## Action item:      │
│  incident   built-in  ## Incident:    ## Impact:    ## Root cause:          │
│  pr-review  built-in  ## PR:    ## Summary:    ## Feedback:    ## Decision: │
│  sprint     built-in  ## Sprint goal:    ## Completed: -    ## Carried …    │
╰─────────────────────────────────────────────────────────────────────────────╯
Use as prefix:  devlog add -T NAME "your note here"
Preview full:   devlog template use NAME
```

Add custom templates in `~/.devlog.toml`:
```toml
[templates]
deploy = "## What shipped: \n\n## Rollback plan: \n\n## Monitoring: "
research = "## Question: \n\n## Findings: \n\n## Next step: "
```

---

### `devlog compare` — Side-by-side monthly comparison

Compare any two calendar months — entry volume, active days, coverage %, average mood, and tag breakdown — all in a single Rich table. Add `--ai` for a streaming narrative.

```bash
devlog compare                          # last month vs this month
devlog compare --period1 2026-03 --period2 2026-05
devlog compare --period1 2026-03 --period2 2026-05 --ai
```

```
╭─ Comparison: March 2026 → May 2026 ─────────────────────────────────────╮
│  Metric        March 2026  May 2026   Δ                                  │
│  Total entries         31        48   +17                                │
│  Active days        12/31      21/31   +9                                │
│  Coverage             39%       68%   +29                                │
│  Avg / day            1.0       1.5   +0.5                               │
│  Avg mood            3.2/5     3.8/5  +0.6                               │
╰──────────────────────────────────────────────────────────────────────────╯
╭─ Tag Breakdown ──────────────────────╮
│  Tag      March 2026  May 2026   Δ   │
│  feat              8        15  +7   │
│  bug               5         6  +1   │
│  fix               3         9  +6   │
│  docs              4         3  −1   │
╰──────────────────────────────────────╯
```

---

### `devlog ai-year` — Annual AI retrospective

A streaming, Claude-powered year-in-review that analyses the last 365 days of journal entries: major themes, accomplishments, patterns, and concrete goals for the year ahead. Uses `claude-sonnet-4-6` for a deeper analysis than the weekly review.

```bash
devlog ai-year
```

```
Annual Review — 2025–2026

365 entries  ·  218 active days  ·  14 distinct tags  ·  109 mood data points

## Year in Review
- Shipped 3 major product features (auth overhaul, async pipeline, v2 API)
- Transitioned from monolith to microservices architecture — reflected in
  surge of [infra] and [deploy] entries in Q3

## Major Themes
- API design and async architecture dominated H1
- Performance optimisation became the H2 focus after the v2 launch
...
```

Requires `ANTHROPIC_API_KEY`.

---

## What's New in v2.4.0

### `devlog pin` — Pinboard for important entries

Pin any entry to your personal pinboard and recall it instantly. Great for decisions, key discoveries, or entries you want to surface during reviews.

```bash
devlog pin add 42         # pin entry #42
devlog pin                # show pinboard (alias for "devlog pin list")
devlog pin list           # list all pinned entries
devlog pin remove 42      # unpin
```

```
╭─ Pinboard (2 entries) ─────────────────────────────────────────────────────╮
│   ID  Date        Tag      Entry                                           │
│   42  2026-05-21  feat     Decided on async architecture for the ingestion │
│   17  2026-05-14  research Benchmarked 3 DB strategies — Postgres wins     │
╰────────────────────────────────────────────────────────────────────────────╯
```

---

### `devlog correlate` — Mood × Tag correlation table

See which types of work leave you energised vs drained. Computes average mood per tag over the last N days and shows deviation from your baseline.

```bash
devlog correlate               # last 90 days
devlog correlate --days 30     # shorter window
```

```
╭─ Mood × Tag Correlation — last 90 days ──────────────────────────────────╮
│  Tag       Entries  Avg mood  vs. avg  Distribution                      │
│  feat           23      4.2    +0.6   ▓▓▓▓▓▓▓▓▓▓▓▓                      │
│  research        8      3.9    +0.3   ▓▓▓▓▓▓▓▓▓▓▓                       │
│  docs            6      3.6    +0.0   ▓▓▓▓▓▓▓▓▓▓                        │
│  fix            15      3.2    -0.4   ▓▓▓▓▓▓▓▓▓                         │
│  meeting        11      2.4    -1.2   ▓▓▓▓▓▓▓                           │
╰──────────────────────────────────────────────────────────────────────────╯
  Overall avg mood: 3.6/5  ·  63 entries with mood data
  Happiest tag: feat (avg 4.2/5)  ·  Hardest tag: meeting (avg 2.4/5)
```

---

### `devlog ai-plan` — AI daily plan for tomorrow

Streams a structured daily plan for tomorrow based on today's journal entries, yesterday's notes, and your open weekly goals.

```bash
devlog ai-plan
```

```
Daily Plan for 2026-05-29

Based on 4 today + 2 yesterday entries, 2 open goal(s)

## Morning (high-focus)
- Finish the async ingestion PR — you noted it's 80% done (#fix, started today)
- Write tests for the new retry logic before moving on

## Afternoon (lower-focus)
- Update docs/ARCHITECTURE.md (goal: "document the data pipeline")
- Review open PRs from teammates

## Don't forget
- Run the weekly correlate report to close the loop on mood tracking
```

Requires `ANTHROPIC_API_KEY`.

---

## What's New in v2.3.0

### `devlog habit` — Daily habit tracker with streaks and Rich history view

Track daily habits alongside your journal. Each habit gets its own streak counter and a visual ■/· history grid showing the last N days at a glance.

```bash
devlog habit add "exercise"
devlog habit add "read 30min"
devlog habit check 1              # mark habit #1 done today
devlog habit status               # show all habits
devlog habit status --days 21     # show 21-day history
devlog habit uncheck 1            # undo today's check-in
devlog habit delete 2             # remove a habit
```

```
╭─ Habits — last 14 days ──────────────────────────────────────────╮
│  ID  Habit          Streak    %   Last 14 days →                 │
│   1  exercise          5d   64%   ■·■■■·■■■·■·■■                │
│   2  read 30min        2d   50%   ·■·■■·■·■·■·■■                │
╰──────────────────────────────────────────────────────────────────╯
  Legend: ■ done  · missed  ·  devlog habit check ID  to log today
```

---

### `devlog metrics` — Cross-dimensional productivity metrics with AI analysis

Computes velocity, mood-tag correlations, peak hour, and busiest weekday across your log history. Pass `--ai` to stream an AI interpretation of your patterns.

```bash
devlog metrics                  # last 30 days
devlog metrics --days 60        # longer window
devlog metrics --days 30 --ai   # AI interpretation (needs ANTHROPIC_API_KEY)
```

```
╭─ Productivity Metrics — last 30 days ─────╮
│  Total entries       47                   │
│  Active days         18 / 30              │
│  Velocity            1.57 entries/day     │
│  Trend               improving            │
│  Peak hour           10:00                │
│  Busiest weekday     Tue                  │
│  Avg mood            3.8/5                │
╰───────────────────────────────────────────╯
╭─ Top tags ──────────────────────────────────╮
│  Tag       n   Avg mood                     │
│  feat     18      4.2                       │
│  bug       9      2.9                       │
│  review    7      3.5                       │
╰─────────────────────────────────────────────╯
  Happiest tag: feat (avg mood 4.2/5)
  Hardest tag:  bug  (avg mood 2.9/5)
```

---

### `devlog standout` — Identify your most significant entries via TF-IDF outlier scoring

Uses TF-IDF to surface entries with unusually rare or distinctive language — your most notable moments, decisions, and discoveries — without needing an AI API key.

```bash
devlog standout                # top 10 in last 90 days
devlog standout --top 5        # top 5
devlog standout --days 180     # wider window
```

```
╭─ Standout entries — last 90 days (TF-IDF outliers) ─────────────────╮
│  Score  Date          Tag       Entry                               │
│   8.41  2026-05-15    feat      migrated auth to PKCE flow in...   │
│   7.92  2026-04-28    deploy    zero-downtime blue-green deploy...  │
│   7.34  2026-04-10    research  investigated CRDT approaches for... │
╰──────────────────────────────────────────────────────────────────────╯
  Scoring: entries with rare, repeated keywords score highest  ·  312 entries analysed
```

---

## What's New in v2.2.0

### `devlog streak` — Streak milestones, best-ever record, and 14-day calendar

Enhanced streak tracking that goes beyond a simple count. Shows your current streak, your all-time best streak and when it occurred, days until the next milestone, a 30-day visual flame bar, and a compact 14-day calendar.

```bash
devlog streak
```

```
╭─ Streak ───────────────────────────────╮
│  Current streak: 5 days                │
╰────────────────────────────────────────╯
  Best ever: 14 days  (2026-04-07 → 2026-04-20)
  Next milestone: 7 days  (2 days to go)

  Last 30 days:  🔥🔥🔥❄️ 🔥🔥🔥🔥🔥❄️ ❄️ 🔥...

  Last 14 days:
     11 12 13 14 15 16 17 18 19 20 21 22 23 24
      ·  ✓  ✓  ✓  ·  ·  ✓  ✓  ✓  ✓  ✓  ·  ·  ✓
```

Milestones tracked: 7, 14, 30, 60, 90, 180, and 365 days.

---

### `devlog note` — Long-form notes with title, body, and tag

Write and manage long-form notes alongside your daily entries. Supports Markdown bodies, optional tags, and persistent storage in `~/.devlog_notes.json`.

```bash
# Add a note
devlog note add --title "Architecture decision: switch to async" --body "We decided to..." --tag arch

# List notes (optionally filter by tag)
devlog note list
devlog note list --tag arch --limit 5

# View a note (body rendered as Markdown)
devlog note view 1

# Delete a note
devlog note delete 1
```

```
╭─ Notes ───────────────────────────────────────────────────────────────────╮
│ ID  Date        Tag   Title                           Preview              │
│  2  2026-05-24  arch  Architecture decision: …        We decided to sw…   │
│  1  2026-05-23        Sprint retro notes              Good velocity thi…  │
╰───────────────────────────────────────────────────────────────────────────╯
```

---

### `devlog digest` — AI standup digest for Slack, Markdown, or plain text

Generate a concise, ready-to-paste standup digest from your devlog entries. Covers today or the current week. AI formats (slack/markdown) use Claude Haiku; plain format needs no API key.

```bash
export ANTHROPIC_API_KEY=sk-ant-...

devlog digest                        # today's entries, Slack format (default)
devlog digest --period week          # this week's entries
devlog digest --format markdown      # Markdown bullets instead of Slack bold
devlog digest --format plain         # no AI — plain bullet list, no API key needed
devlog digest --no-cache             # bypass cache and regenerate
```

```
Digest — 2026-05-24

• *Accomplished:* Fixed race condition in the job queue (#142) and merged auth PR
• Refactored DB connection pool — reduced connection overhead by ~30%
• Deployed v2.2.0 to staging; smoke tests passing
• *Next:* Write integration tests for the new async worker
```

Results are cached for 1 hour per period/format combination. Use `--no-cache` to force regeneration.

---

## What's New in v2.1.0

### `devlog sync-git [PATH]` — Import git commits as journal entries

Pull recent commits from any git repository directly into your devlog. Uses `git log` under the hood, deduplicates automatically, and tags every imported entry so you can filter them later.

```bash
devlog sync-git                              # import commits from current repo (last 24h)
devlog sync-git ~/projects/myapp            # import from another repo
devlog sync-git --since "7 days ago"        # look further back
devlog sync-git --since 2026-05-01         # since a specific date
devlog sync-git --tag feat                  # use a custom tag (default: commit)
devlog sync-git --dry-run                   # preview without saving
```

```
✓ Imported 5 commits from '.' as entries (tag: commit)
  2026-05-21 10:14  fix null pointer in session handler [a1b2c3d4]
  2026-05-21 11:30  add rate limiting to auth endpoint [e5f6a7b8]
  2026-05-21 14:02  refactor DB connection pool [c9d0e1f2]
```

Duplicate detection is automatic — running `sync-git` twice won't create duplicate entries.

---

### `devlog summarize` — AI caching (no redundant API calls)

`devlog summarize` now caches AI-generated summaries to disk (`~/.devlog/ai_cache.json`) with a 1-hour TTL. Re-running the command for the same day is instant and free — the cached result is returned immediately. Use `--no-cache` to force regeneration.

```bash
devlog summarize              # uses cache if available (shown with "(cached)" note)
devlog summarize --no-cache   # bypass cache and call the API fresh
devlog summarize 2026-05-20   # cached per-day — each date has its own cache key
```

```
Summary for 2026-05-21

Worked on stabilising the auth layer by fixing a null pointer bug and adding rate
limiting. Spent the afternoon refactoring the DB connection pool for better
reliability under load. Wrapped up with code review and documentation updates.

  (cached — run with --no-cache to regenerate)
```

Expired entries are evicted automatically on each write to keep the cache file small.

---

### `devlog timer [MINUTES]` — Pomodoro timer with auto-log

A full-featured Pomodoro-style countdown timer that renders a live Rich progress bar in your terminal and prompts you to log what you worked on when the session ends (or when you cancel early with Ctrl+C).

```bash
devlog timer               # 25-minute Pomodoro (default)
devlog timer 50            # custom duration
devlog timer 15 --label "quick bug fix" --tag bug
devlog timer -l "writing docs"
```

```
🍅 Timer started: 25m session (25 min)
  Press Ctrl+C to cancel and log partial session.

╭──────────────────────────────────────────────────────╮
│              🍅  25m session                         │
│                                                      │
│  ████████████████░░░░░░░░░░░░░░░░░░░░░░  42%        │
│                                                      │
│                10:42 remaining                       │
│               elapsed 14:18                          │
╰──────────────────────────────────────────────────────╯

✓ Timer complete! 25 minute session finished.

What did you work on during this session?
  > finished the auth refactor and wrote tests

✓ Logged: [focus] finished the auth refactor and wrote tests (25m00s)  (2026-05-21 15:30)
```

The auto-logged entry includes the actual elapsed time so partial sessions are accurately recorded. The tag defaults to `focus` (or your configured `default_tag`).

---

## What's New in v2.0.0

### `devlog semantic <query> [--top N]` — Semantic search with TF-IDF

Find entries by meaning, not just keywords. Uses a pure-Python TF-IDF cosine similarity engine (no external ML dependencies) to rank all entries by relevance to your natural-language query.

```bash
devlog semantic "database performance issues"
devlog semantic "auth refactor" --top 5
devlog semantic "deployment problems production"
```

```
╭─ Semantic: "database performance issues" ─────────────────────────────────────╮
│  Score   Date          Tag        Entry                                        │
│  0.847   2026-05-10    bug        fixed slow query on users table              │
│  0.712   2026-05-08    refactor   optimised DB connection pool                 │
│  0.634   2026-05-14    feat       added query caching layer                    │
╰────────────────────────────────────────────────────────────────────────────────╯
```

Works entirely offline — no API key required. The TF-IDF vectors are built fresh from your corpus on each query.

### `devlog ai-tag [--count N]` — AI batch tagging

Automatically tag all untagged entries in bulk using Claude Haiku. Processes entries one by one and saves results immediately. Requires `ANTHROPIC_API_KEY`.

```bash
export ANTHROPIC_API_KEY=sk-ant-...

devlog ai-tag              # tag all untagged entries
devlog ai-tag --count 20   # tag only the first 20 untagged entries
devlog ai-tag -n 5         # short form
```

```
Auto-tagging 12 untagged entries...
  #3 fixed null pointer in auth middleware → bug
  #7 refactored DB connection pool → refactor
  #9 deployed v2.1.3 to staging → deploy
  #11 reviewed PR #88 auth changes → review
  ...

✓ Tagged 12 entries
```

### `devlog focus [--all-hours]` — Focus hours analysis

Discover when you're most productive by analysing the timestamps of all your journal entries. Displays a visual bar chart by hour of day and identifies your peak hour and peak period.

```bash
devlog focus               # show active hours only
devlog focus --all-hours   # show all 24 hours
```

```
╭─ Focus Hours ──────────────────────────────────╮
│  Hour    n                                      │
│  09:00   8  ████████████████████               │
│  10:00  12  ████████████████████████████████   │
│  11:00   9  ██████████████████████             │
│  14:00  15  ████████████████████████████████   │
│  15:00  11  ████████████████████████████       │
│  16:00   6  ██████████████                     │
╰────────────────────────────────────────────────╯

  Peak hour: 14:00  ·  Peak period: afternoon  ·  61 entries analysed
```

---

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
