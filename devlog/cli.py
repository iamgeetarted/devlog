import argparse
import os
import sys
from datetime import date, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box

from .storage import add_entry, get_entries, delete_entry, search_entries, edit_entry, get_stats, load_entries, save_entries

try:
    from .config import load_config as _load_config
    _cfg = _load_config()
except ValueError as _cfg_err:
    from rich.console import Console as _C
    _C(stderr=True).print(f"[yellow]devlog: config warning: {_cfg_err}[/yellow]")
    _cfg: dict = {}

console = Console()


def make_entries_table(entries: list[dict]) -> Table:
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        expand=False,
    )
    table.add_column("ID", style="dim", justify="right", no_wrap=True)
    table.add_column("Time", style="dim", no_wrap=True)
    table.add_column("Tag", style="yellow", no_wrap=True)
    table.add_column("Entry", style="white")

    for e in entries:
        tag = e.get("tag") or ""
        table.add_row(str(e["id"]), e["time"], tag, e["text"])

    return table


def print_entries(entries: list[dict], title: str | None = None) -> None:
    if title:
        if not entries:
            console.print(Panel("[dim]No entries found.[/dim]", title=title, border_style="dim", box=box.ROUNDED))
        else:
            table = make_entries_table(entries)
            console.print(Panel(table, title=title, border_style="cyan", box=box.ROUNDED))
    else:
        if not entries:
            console.print("[dim]No entries found.[/dim]")
            return
        current_date = None
        for group_date in dict.fromkeys(e["date"] for e in entries):
            day_entries = [e for e in entries if e["date"] == group_date]
            table = make_entries_table(day_entries)
            console.print(Panel(table, title=group_date, border_style="cyan", box=box.ROUNDED))


def export_markdown(entries: list[dict]) -> str:
    if not entries:
        return "No entries."
    lines = ["# Dev Log\n"]
    current_date = None
    for e in entries:
        if e["date"] != current_date:
            current_date = e["date"]
            lines.append(f"## {current_date}\n")
        tag = f"**[{e['tag']}]** " if e.get("tag") else ""
        lines.append(f"- `{e['time']}` {tag}{e['text']}")
    return "\n".join(lines)


def export_json(entries: list[dict]) -> str:
    import json
    return json.dumps(entries, indent=2)


def export_csv(entries: list[dict]) -> str:
    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "date", "time", "tag", "text"])
    for e in entries:
        writer.writerow([e["id"], e["date"], e["time"], e.get("tag") or "", e["text"]])
    return buf.getvalue()


def export_html(entries: list[dict]) -> str:
    """Generate a self-contained HTML report from entries."""
    from collections import Counter

    tag_counts: Counter = Counter(e.get("tag") for e in entries if e.get("tag"))
    total = len(entries)
    days = len({e["date"] for e in entries})

    # Group entries by date
    dates: dict[str, list[dict]] = {}
    for e in entries:
        dates.setdefault(e["date"], []).append(e)

    TAG_COLORS = ["#5bc0eb", "#fde74c", "#9bc53d", "#c3423f", "#e55934",
                  "#fa7921", "#a23b72", "#2ec4b6", "#cbf3f0", "#ffbf69"]

    def tag_color(tag: str) -> str:
        return TAG_COLORS[hash(tag) % len(TAG_COLORS)]

    def mood_emoji(m: int) -> str:
        return ["", "😞", "😕", "😐", "🙂", "😄"][m]

    rows_html = []
    for d in sorted(dates, reverse=True):
        rows_html.append(f'<h2 class="date-header">{d}</h2><div class="day-group">')
        for e in dates[d]:
            tag_html = ""
            if e.get("tag"):
                c = tag_color(e["tag"])
                tag_html = f'<span class="tag" style="background:{c}22;color:{c};border:1px solid {c}66">{e["tag"]}</span>'
            mood_html = ""
            if e.get("mood"):
                mood_html = f'<span class="mood" title="Mood {e[\"mood\"]}/5">{mood_emoji(e["mood"])} {e["mood"]}/5</span>'
            rows_html.append(
                f'<div class="entry"><span class="time">{e["time"]}</span>'
                f'{tag_html}{mood_html}'
                f'<span class="text">{e["text"]}</span></div>'
            )
        rows_html.append("</div>")

    tags_html = "".join(
        f'<span class="tag" style="background:{tag_color(t)}22;color:{tag_color(t)};border:1px solid {tag_color(t)}66">'
        f'{t} <strong>{c}</strong></span>'
        for t, c in tag_counts.most_common(10)
    )

    generated = date.today().isoformat()
    content = "\n".join(rows_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dev Log</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,monospace;background:#0d1117;color:#c9d1d9;line-height:1.6;padding:2rem}}
  h1{{color:#58a6ff;font-size:1.6rem;margin-bottom:.25rem}}
  .meta{{color:#8b949e;font-size:.85rem;margin-bottom:2rem}}
  .stats{{display:flex;gap:1.5rem;margin-bottom:2rem;flex-wrap:wrap}}
  .stat{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:.75rem 1.25rem;min-width:100px;text-align:center}}
  .stat-val{{font-size:1.5rem;font-weight:700;color:#58a6ff}}
  .stat-lbl{{font-size:.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em}}
  .tags-summary{{margin-bottom:2rem;display:flex;flex-wrap:wrap;gap:.4rem}}
  h2.date-header{{color:#8b949e;font-size:.85rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin:1.5rem 0 .5rem;border-bottom:1px solid #21262d;padding-bottom:.25rem}}
  .day-group{{display:flex;flex-direction:column;gap:.4rem;margin-bottom:.5rem}}
  .entry{{background:#161b22;border:1px solid #21262d;border-radius:6px;padding:.5rem .75rem;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}}
  .time{{color:#8b949e;font-size:.8rem;font-family:monospace;min-width:42px}}
  .tag{{font-size:.72rem;padding:.1rem .45rem;border-radius:12px;font-weight:600;white-space:nowrap}}
  .mood{{font-size:.78rem;color:#8b949e;white-space:nowrap}}
  .text{{color:#c9d1d9;flex:1;min-width:0}}
  footer{{margin-top:3rem;color:#8b949e;font-size:.75rem;text-align:center}}
</style>
</head>
<body>
<h1>Dev Log</h1>
<p class="meta">Generated {generated} · {total} entries across {days} days</p>
<div class="stats">
  <div class="stat"><div class="stat-val">{total}</div><div class="stat-lbl">Entries</div></div>
  <div class="stat"><div class="stat-val">{days}</div><div class="stat-lbl">Days</div></div>
  <div class="stat"><div class="stat-val">{len(tag_counts)}</div><div class="stat-lbl">Tags</div></div>
</div>
{('<div class="tags-summary">' + tags_html + '</div>') if tags_html else ''}
{content}
<footer>Generated by <a href="https://github.com/iamgeetarted/devlog" style="color:#58a6ff">devlog</a></footer>
</body>
</html>"""


def _print_formatted(entries: list[dict], fmt: str) -> None:
    if fmt == "json":
        print(export_json(entries))
    elif fmt == "markdown":
        print(export_markdown(entries))
    elif fmt == "csv":
        print(export_csv(entries))


def _mood_icon(mood: int) -> str:
    return ["", "😞", "😕", "😐", "🙂", "😄"][mood]


def _mood_style(mood: int) -> str:
    return ["", "red", "yellow", "dim", "cyan", "green"][mood]


def _suggest_tag_for_entry(entry: dict) -> None:
    """Use Claude Haiku to suggest a tag for an untagged entry."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return
    try:
        import anthropic
    except ImportError:
        return

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"Given this developer journal entry: \"{entry['text']}\"\n\n"
        "Suggest ONE short tag (1-2 words, lowercase, no spaces — use hyphens if needed). "
        "Common tags: feat, bug, fix, docs, chore, deploy, review, meeting, research, refactor. "
        "Reply with ONLY the tag, nothing else."
    )
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=16,
            messages=[{"role": "user", "content": prompt}],
        )
        suggested = resp.content[0].text.strip().lower().split()[0]
        console.print(f"  [dim]AI suggests tag:[/dim] [yellow]{suggested}[/yellow]  "
                      f"[dim]Accept? devlog edit {entry['id']} -t {suggested}[/dim]")
    except Exception:
        pass


def cmd_add(args):
    text = " ".join(args.text)

    # Apply template prefix if -T given
    if args.template:
        templates = _cfg.get("templates", {})
        prefix = templates.get(args.template)
        if prefix is None:
            console.print(
                f"[red]✗ Template '{args.template}' not found in ~/.devlog.toml[/red]\n"
                f"  Defined templates: {', '.join(templates) or '(none)'}"
            )
            return
        text = prefix + text

    tag = args.tag or _cfg.get("default_tag")
    mood = getattr(args, "mood", None)
    if mood is not None and not (1 <= mood <= 5):
        console.print("[red]✗ Mood must be 1–5 (1=rough, 5=great)[/red]")
        return
    entry = add_entry(text, tag=tag, mood=mood)
    tag_str = f"[yellow]\\[{entry['tag']}][/yellow] " if entry.get("tag") else ""
    mood_str = f" [{_mood_style(entry['mood'])}]{_mood_icon(entry['mood'])} {entry['mood']}/5[/{_mood_style(entry['mood'])}]" if entry.get("mood") else ""
    console.print(
        f"[green]✓[/green] Logged: {tag_str}{entry['text']}{mood_str} "
        f"[dim]({entry['date']} {entry['time']})[/dim]"
    )

    # After the entry is saved and printed, offer tag suggestion if requested
    if getattr(args, "suggest_tag", False) and not (args.tag or _cfg.get("default_tag")):
        _suggest_tag_for_entry(entry)


def cmd_today(args: argparse.Namespace) -> None:
    today = date.today().isoformat()
    entries = get_entries(day=today)
    fmt = getattr(args, "format", None)
    if fmt and fmt != "table":
        _print_formatted(entries, fmt)
    else:
        print_entries(entries, title=f"Today — {today}")


def cmd_yesterday(args):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    entries = get_entries(day=yesterday)
    print_entries(entries, title=f"Yesterday — {yesterday}")


def cmd_log(args: argparse.Namespace) -> None:
    since = getattr(args, "since", None)
    until = getattr(args, "until", None)
    entries = get_entries(day=args.date, since=since, until=until)
    fmt = getattr(args, "format", None)

    if since or until:
        parts = []
        if since:
            parts.append(f"since {since}")
        if until:
            parts.append(f"until {until}")
        title = "Entries — " + ", ".join(parts)
    else:
        title = args.date if args.date else None

    if fmt and fmt != "table":
        _print_formatted(entries, fmt)
    else:
        print_entries(entries, title=title)


def cmd_export(args):
    since = getattr(args, "since", None)
    until = getattr(args, "until", None)
    entries = get_entries(day=args.date, since=since, until=until)
    fmt = args.format or _cfg.get("default_export_format", "markdown")
    if fmt == "json":
        content = export_json(entries)
    elif fmt == "csv":
        content = export_csv(entries)
    elif fmt == "html":
        content = export_html(entries)
    else:
        content = export_markdown(entries)

    if args.output:
        with open(args.output, "w") as f:
            f.write(content)
        console.print(f"[green]✓ Exported {len(entries)} entries ({fmt}) to {args.output}[/green]")
    else:
        print(content)


def cmd_delete(args):
    if delete_entry(args.id):
        console.print(f"[green]✓ Deleted entry {args.id}[/green]")
    else:
        console.print(f"[red]✗ Entry {args.id} not found[/red]")


def cmd_search(args):
    keyword = " ".join(args.keyword)
    entries = search_entries(keyword, tag=args.tag)
    title = f'Search: "{keyword}"'
    if args.tag:
        title += f"  [tag={args.tag}]"
    print_entries(entries, title=title)


def cmd_edit(args):
    entry_id = args.id
    new_text = " ".join(args.text) if args.text else None
    tag = args.tag  # None means clear, string means set, ... means leave unchanged
    if new_text is None and tag is ...:
        console.print("[yellow]Nothing to change — provide new text and/or -t TAG[/yellow]")
        return
    if edit_entry(entry_id, text=new_text, tag=tag):
        console.print(f"[green]✓ Updated entry {entry_id}[/green]")
    else:
        console.print(f"[red]✗ Entry {entry_id} not found[/red]")


def cmd_stats(args):
    from rich.table import Table, box as rbox
    from rich.panel import Panel

    days = args.days
    stats = get_stats(days=days)
    by_date = stats["by_date"]
    tag_counts = stats["tag_counts"]
    streak = stats["streak"]
    total = stats["total"]

    BAR_WIDTH = 24
    max_count = max(by_date.values(), default=1) or 1

    day_table = Table(box=rbox.SIMPLE, show_header=True, header_style="bold cyan", pad_edge=False)
    day_table.add_column("Date", style="dim", no_wrap=True)
    day_table.add_column("n", justify="right", style="white", width=3)
    day_table.add_column("", style="cyan")

    for d, count in by_date.items():
        if count == 0 and not args.all_days:
            continue
        bar = "█" * max(1, round(count / max_count * BAR_WIDTH)) if count else ""
        day_table.add_row(d, str(count) if count else "·", bar)

    tag_table = Table(box=rbox.SIMPLE, show_header=True, header_style="bold yellow", pad_edge=False)
    tag_table.add_column("Tag", style="yellow")
    tag_table.add_column("Count", justify="right")

    for tag, cnt in tag_counts.items():
        tag_table.add_row(tag, str(cnt))

    console.print(Panel(day_table, title=f"Entries — last {days} days", border_style="cyan", box=rbox.ROUNDED))
    if tag_counts:
        console.print(Panel(tag_table, title="Tag breakdown", border_style="yellow", box=rbox.ROUNDED))
    console.print(
        f"\n  [bold cyan]Streak:[/bold cyan] {streak} consecutive day{'s' if streak != 1 else ''}  "
        f"[dim]·[/dim]  [dim]Total entries: {total}[/dim]"
    )


def cmd_summarize(args):
    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(
            "[red]ANTHROPIC_API_KEY environment variable is not set.[/red]\n"
            "Export it with: [bold]export ANTHROPIC_API_KEY=your-key[/bold]"
        )
        sys.exit(1)

    day = args.date or date.today().isoformat()
    entries = get_entries(day=day)

    if not entries:
        console.print(f"[dim]No entries found for {day}.[/dim]")
        return

    bullet_list = "\n".join(
        f"- [{e['time']}]{' [' + e['tag'] + ']' if e.get('tag') else ''} {e['text']}"
        for e in entries
    )
    prompt = (
        f"Here are my developer journal entries for {day}:\n\n"
        f"{bullet_list}\n\n"
        "Write a concise paragraph (3-5 sentences) summarizing what was accomplished. "
        "Use past tense, be specific, and group related work together naturally."
    )

    from .cache import make_key, cache_get, cache_set
    cache_key = make_key(f"summarize:{day}:{bullet_list}")
    cached = cache_get(cache_key)

    console.print(f"\n[bold cyan]Summary for {day}[/bold cyan]\n")

    if cached and not getattr(args, "no_cache", False):
        console.print(cached)
        console.print("\n[dim]  (cached — run with --no-cache to regenerate)[/dim]")
        return

    client = anthropic.Anthropic(api_key=api_key)
    collected = []
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            collected.append(text)
    print()
    cache_set(cache_key, "".join(collected))


def cmd_week(args: argparse.Namespace) -> None:
    import re
    from datetime import date, timedelta

    today = date.today()
    if args.week:
        m = re.match(r"^(\d{4})-?[Ww](\d{1,2})$", args.week)
        if not m:
            console.print("[red]Invalid week format. Use YYYY-WNN, e.g. 2026-W18[/red]")
            return
        year, week_num = int(m.group(1)), int(m.group(2))
        jan4 = date(year, 1, 4)
        monday = jan4 + timedelta(weeks=week_num - 1, days=-jan4.weekday())
    else:
        monday = today - timedelta(days=today.weekday())

    days = [monday + timedelta(days=i) for i in range(7)]
    all_entries: list[dict] = []
    for d in days:
        if d <= today:
            all_entries.extend(get_entries(day=d.isoformat()))

    week_label = monday.strftime("Week of %B %d, %Y")
    print_entries(all_entries, title=week_label)


def cmd_dash(args: argparse.Namespace) -> None:
    """Live-updating Rich dashboard for today's entries."""
    import time
    from datetime import date
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table, box as rbox
    from rich.align import Align
    from rich.text import Text

    def build_dashboard() -> Layout:
        today = date.today().isoformat()
        entries = get_entries(day=today)
        stats = get_stats(days=7)

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="entries", ratio=2),
            Layout(name="sidebar", ratio=1),
        )

        layout["header"].update(
            Panel(Align.center(Text("devlog dashboard", style="bold cyan")), border_style="cyan")
        )

        t = Table(box=rbox.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
        t.add_column("ID", style="dim", justify="right", width=4)
        t.add_column("Time", style="dim", width=6)
        t.add_column("Tag", style="yellow", width=10)
        t.add_column("Entry", style="white")
        for e in entries:
            t.add_row(str(e["id"]), e["time"], e.get("tag") or "", e["text"])
        layout["entries"].update(
            Panel(t if entries else Align.center(Text("No entries yet today.", style="dim")),
                  title=f"Today — {today} ({len(entries)} entries)", border_style="cyan")
        )

        sidebar = Table(box=rbox.SIMPLE, show_header=False, expand=True)
        sidebar.add_column("Key", style="cyan")
        sidebar.add_column("Val", style="white", justify="right")
        sidebar.add_row("Streak", f"{stats['streak']} day{'s' if stats['streak'] != 1 else ''}")
        sidebar.add_row("Total", str(stats["total"]))
        sidebar.add_section()
        for tag, cnt in list(stats["tag_counts"].items())[:8]:
            sidebar.add_row(f"  [{tag}]", str(cnt))
        layout["sidebar"].update(Panel(sidebar, title="Stats", border_style="yellow"))

        ts = time.strftime("%H:%M:%S")
        layout["footer"].update(
            Panel(Align.center(Text(f"Refreshed {ts} · Ctrl+C to exit", style="dim")), border_style="dim")
        )
        return layout

    try:
        with Live(build_dashboard(), refresh_per_second=0.5, screen=True) as live:
            while True:
                time.sleep(2)
                live.update(build_dashboard())
    except KeyboardInterrupt:
        console.print("[dim]Dashboard closed.[/dim]")


def cmd_review(args: argparse.Namespace) -> None:
    """Stream an AI weekly productivity review for a given ISO week."""
    import os, re
    from datetime import date, timedelta

    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Set ANTHROPIC_API_KEY first.[/red]")
        return

    today = date.today()
    if args.week:
        m = re.match(r"^(\d{4})-?[Ww](\d{1,2})$", args.week)
        if not m:
            console.print("[red]Invalid week format. Use YYYY-WNN, e.g. 2026-W18[/red]")
            return
        year, week_num = int(m.group(1)), int(m.group(2))
        jan4 = date(year, 1, 4)
        monday = jan4 + timedelta(weeks=week_num - 1, days=-jan4.weekday())
    else:
        monday = today - timedelta(days=today.weekday())

    days = [monday + timedelta(days=i) for i in range(7)]
    all_entries = []
    for d in days:
        all_entries.extend(get_entries(day=d.isoformat()))

    week_label = monday.strftime("Week of %B %d, %Y")

    if not all_entries:
        console.print(f"[dim]No entries found for {week_label}.[/dim]")
        return

    bullet_list = "\n".join(
        f"- [{e['date']} {e['time']}]{' [' + e['tag'] + ']' if e.get('tag') else ''} {e['text']}"
        for e in all_entries
    )

    tag_counts: dict[str, int] = {}
    for e in all_entries:
        t = e.get("tag")
        if t:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    prompt = (
        f"Here are my developer journal entries for {week_label}:\n\n"
        f"{bullet_list}\n\n"
        f"Tag distribution: {tag_counts}\n\n"
        "Please provide a concise weekly productivity review covering:\n"
        "1. Major accomplishments this week (2-3 sentences)\n"
        "2. Work patterns observed (focus areas, tag trends)\n"
        "3. One actionable suggestion for next week\n\n"
        "Be specific and developer-focused. Use markdown formatting with ## headers."
    )

    client = anthropic.Anthropic(api_key=api_key)
    console.print(f"\n[bold cyan]Weekly Review — {week_label}[/bold cyan]\n")
    console.print(f"[dim]{len(all_entries)} entries across {sum(1 for d in days if any(e['date'] == d.isoformat() for e in all_entries))} days[/dim]\n")

    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def cmd_goal(args: argparse.Namespace) -> None:
    """Manage weekly goals."""
    import re
    from .goals import add_goal, complete_goal, delete_goal, list_goals

    subcmd = args.goal_cmd

    if subcmd == "add":
        text = " ".join(args.text)
        goal = add_goal(text, week=getattr(args, "week", None))
        console.print(
            f"[green]✓[/green] Goal #{goal['id']} added for [cyan]{goal['week']}[/cyan]: {goal['text']}"
        )

    elif subcmd == "done":
        if complete_goal(args.id):
            console.print(f"[green]✓ Goal #{args.id} marked complete[/green]")
        else:
            console.print(f"[red]✗ Goal #{args.id} not found[/red]")

    elif subcmd == "delete":
        if delete_goal(args.id):
            console.print(f"[green]✓ Goal #{args.id} deleted[/green]")
        else:
            console.print(f"[red]✗ Goal #{args.id} not found[/red]")

    elif subcmd == "list":
        week = getattr(args, "week", None)
        goals = list_goals(week=week)

        if not goals:
            label = f" for {week}" if week else ""
            console.print(f"[dim]No goals found{label}. Add one with: devlog goal add \"finish X\"[/dim]")
            return

        from rich.table import Table, box as rbox
        from rich.panel import Panel

        t = Table(box=rbox.ROUNDED, show_header=True, header_style="bold cyan", border_style="dim")
        t.add_column("ID", style="dim", justify="right", width=4)
        t.add_column("Week", style="dim", width=10)
        t.add_column("Status", width=8, justify="center")
        t.add_column("Goal", style="white")

        for g in goals:
            status = "[green]✓ done[/green]" if g["done"] else "[yellow]○ open[/yellow]"
            t.add_row(str(g["id"]), g["week"], status, g["text"])

        done = sum(1 for g in goals if g["done"])
        label = f"Goals{' — ' + week if week else ''} ({done}/{len(goals)} done)"
        console.print(Panel(t, title=label, border_style="cyan", box=rbox.ROUNDED))

    elif subcmd == "check":
        _cmd_goal_check(args)


def _cmd_goal_check(args: argparse.Namespace) -> None:
    """AI accountability check: compare open goals against this week's entries."""
    import re
    from datetime import date, timedelta
    from .goals import list_goals

    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Set ANTHROPIC_API_KEY first.[/red]")
        return

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_days = [monday + timedelta(days=i) for i in range(7)]

    # Current week ISO label
    iso = today.isocalendar()
    week_label = f"{iso[0]}-W{iso[1]:02d}"

    goals = list_goals(week=week_label)
    if not goals:
        console.print(f"[dim]No goals for {week_label}. Set some with: devlog goal add \"...[/dim]")
        return

    all_entries: list[dict] = []
    for d in week_days:
        if d <= today:
            all_entries.extend(get_entries(day=d.isoformat()))

    goals_text = "\n".join(
        f"- [{'✓' if g['done'] else '○'}] #{g['id']}: {g['text']}"
        for g in goals
    )
    entries_text = "\n".join(
        f"- [{e['date']} {e['time']}]{' [' + e['tag'] + ']' if e.get('tag') else ''} {e['text']}"
        for e in all_entries
    ) or "(no journal entries this week yet)"

    prompt = (
        f"Weekly goals for {week_label}:\n{goals_text}\n\n"
        f"Journal entries so far this week:\n{entries_text}\n\n"
        "Based on the journal entries, which goals appear to be on track, in progress, "
        "or not yet started? Be concise and specific. Finish with one motivational nudge "
        "for any unaddressed goals. Use markdown bullet points."
    )

    client = anthropic.Anthropic(api_key=api_key)
    done = sum(1 for g in goals if g["done"])
    console.print(f"\n[bold cyan]Goal Check — {week_label}[/bold cyan]  [dim]({done}/{len(goals)} marked done)[/dim]\n")

    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def cmd_semantic(args: argparse.Namespace) -> None:
    """Semantic search through all entries using TF-IDF cosine similarity."""
    from .semantic import semantic_search
    query = " ".join(args.query)
    entries = load_entries()
    results = semantic_search(query, entries, top_k=args.top)
    if not results:
        console.print("[dim]No semantically similar entries found.[/dim]")
        return
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    t = Table(box=rbox.ROUNDED, show_header=True, header_style="bold cyan", border_style="dim")
    t.add_column("Score", justify="right", style="cyan", width=7)
    t.add_column("Date", style="dim", width=12)
    t.add_column("Tag", style="yellow", width=10)
    t.add_column("Entry", style="white")
    for entry, score in results:
        t.add_row(f"{score:.3f}", entry["date"], entry.get("tag") or "", entry["text"])
    console.print(Panel(t, title=f'Semantic: "{query}"', border_style="cyan", box=rbox.ROUNDED))


def cmd_ai_tag(args: argparse.Namespace) -> None:
    """Auto-tag untagged entries in bulk using Claude Haiku."""
    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        return
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Set ANTHROPIC_API_KEY first.[/red]")
        return

    all_entries = load_entries()
    untagged = [e for e in all_entries if not e.get("tag")]
    if not untagged:
        console.print("[dim]All entries already have tags.[/dim]")
        return
    limit = args.count if args.count else len(untagged)
    batch = untagged[:limit]
    console.print(f"[cyan]Auto-tagging {len(batch)} untagged entries...[/cyan]")

    client = anthropic.Anthropic(api_key=api_key)
    tagged_count = 0

    for entry in batch:
        prompt = (
            f"Developer journal entry: \"{entry['text']}\"\n\n"
            "Suggest ONE short tag (1-2 words, lowercase, hyphens only). "
            "Common tags: feat, bug, fix, docs, chore, deploy, review, meeting, research, refactor, test, infra. "
            "Reply with ONLY the tag."
        )
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=16,
                messages=[{"role": "user", "content": prompt}],
            )
            tag = resp.content[0].text.strip().lower().split()[0]
            # Update entry in all_entries
            for e in all_entries:
                if e["id"] == entry["id"]:
                    e["tag"] = tag
                    break
            console.print(f"  [dim]#{entry['id']}[/dim] {entry['text'][:50]} → [yellow]{tag}[/yellow]")
            tagged_count += 1
        except Exception as exc:
            console.print(f"  [red]✗ #{entry['id']}: {exc}[/red]")

    if tagged_count:
        from .storage import save_entries
        save_entries(all_entries)
        console.print(f"\n[green]✓ Tagged {tagged_count} entries[/green]")


def cmd_focus(args: argparse.Namespace) -> None:
    """Show when you're most productive based on entry timing."""
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from rich.text import Text
    from collections import Counter

    all_entries = load_entries()
    if not all_entries:
        console.print("[dim]No entries yet.[/dim]")
        return

    hour_counts: Counter = Counter()
    for e in all_entries:
        try:
            hour = int(e["time"].split(":")[0])
            hour_counts[hour] += 1
        except (ValueError, IndexError, KeyError):
            pass

    if not hour_counts:
        console.print("[dim]No time data available.[/dim]")
        return

    max_count = max(hour_counts.values()) or 1
    total = sum(hour_counts.values())

    BLOCKS = ["░", "▒", "▓", "█"]
    def _bar(count: int) -> str:
        width = max(1, round(count / max_count * 20))
        level = min(3, round(count / max_count * 3))
        style_map = {0: "dim", 1: "cyan", 2: "bright_cyan", 3: "bold bright_cyan"}
        return f"[{style_map[level]}]{BLOCKS[level] * width}[/{style_map[level]}]"

    PERIODS = {
        "early morning": range(5, 9),
        "morning": range(9, 12),
        "afternoon": range(12, 17),
        "evening": range(17, 21),
        "night": range(21, 24),
    }

    t = Table(box=rbox.SIMPLE, show_header=True, header_style="bold cyan", pad_edge=False)
    t.add_column("Hour", style="dim", width=6, no_wrap=True)
    t.add_column("n", justify="right", style="white", width=4)
    t.add_column("", style="cyan")

    for h in range(24):
        cnt = hour_counts.get(h, 0)
        if cnt == 0 and not getattr(args, "all_hours", False):
            continue
        label = f"{h:02d}:00"
        t.add_row(label, str(cnt) if cnt else "·", _bar(cnt) if cnt else "")

    # Find peak period
    period_counts = {p: sum(hour_counts.get(h, 0) for h in hrs) for p, hrs in PERIODS.items()}
    peak_period = max(period_counts, key=period_counts.get)
    peak_hour = max(hour_counts, key=hour_counts.get)

    console.print(Panel(t, title="Focus Hours", border_style="cyan", box=rbox.ROUNDED))
    console.print(
        f"\n  [bold cyan]Peak hour:[/bold cyan] {peak_hour:02d}:00  "
        f"[dim]·[/dim]  [bold cyan]Peak period:[/bold cyan] {peak_period}  "
        f"[dim]·[/dim]  [dim]{total} entries analysed[/dim]"
    )


def cmd_streak(args: argparse.Namespace) -> None:
    """Enhanced streak summary with milestones, best-ever record, and 14-day calendar."""
    from datetime import date, timedelta
    from rich.table import Table, box as rbox

    entries = load_entries()
    today = date.today()

    # Build set of dates that have at least one entry
    dates_with_entries: set[str] = set(e["date"] for e in entries)

    # --- Current streak (consecutive days ending today) ---
    current_streak = 0
    d = today
    while d.isoformat() in dates_with_entries:
        current_streak += 1
        d -= timedelta(days=1)

    # --- Best-ever streak ---
    best_streak = 0
    best_start: date | None = None
    best_end: date | None = None

    if dates_with_entries:
        sorted_dates = sorted(date.fromisoformat(s) for s in dates_with_entries)
        run = 1
        run_start = sorted_dates[0]
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                run += 1
            else:
                if run > best_streak:
                    best_streak = run
                    best_start = run_start
                    best_end = sorted_dates[i - 1]
                run = 1
                run_start = sorted_dates[i]
        # final run
        if run > best_streak:
            best_streak = run
            best_start = run_start
            best_end = sorted_dates[-1]

    # --- Milestones ---
    milestones = [7, 14, 30, 60, 90, 180, 365]
    next_milestone: int | None = None
    days_to_milestone: int | None = None
    for m in milestones:
        if current_streak < m:
            next_milestone = m
            days_to_milestone = m - current_streak
            break

    # --- Visual flame bar (last 30 days) ---
    flame_days = 30
    flame_parts: list[str] = []
    for i in range(flame_days - 1, -1, -1):
        day = (today - timedelta(days=i)).isoformat()
        if day in dates_with_entries:
            flame_parts.append("[bold red]🔥[/bold red]")
        else:
            flame_parts.append("[blue]❄️ [/blue]")
    flame_bar = "".join(flame_parts)

    # --- 14-day mini calendar ---
    cal_days = 14
    cal_header = ""
    cal_marks = ""
    for i in range(cal_days - 1, -1, -1):
        d = today - timedelta(days=i)
        cal_header += f" {d.day:2d}"
        if d.isoformat() in dates_with_entries:
            cal_marks += "  [green]✓[/green]"
        else:
            cal_marks += "  [dim]·[/dim]"

    # --- Output ---
    console.print()
    console.print(Panel(
        f"[bold yellow]Current streak:[/bold yellow] [bold white]{current_streak}[/bold white] day{'s' if current_streak != 1 else ''}",
        title="[bold red]Streak[/bold red]",
        border_style="yellow",
        box=rbox.ROUNDED,
    ))

    if best_streak > 0 and best_start and best_end:
        period_str = f"{best_start.isoformat()} → {best_end.isoformat()}"
        console.print(
            f"  [bold cyan]Best ever:[/bold cyan] [bold white]{best_streak}[/bold white] days  "
            f"[dim]({period_str})[/dim]"
        )
    else:
        console.print("  [bold cyan]Best ever:[/bold cyan] [dim]no entries yet[/dim]")

    if next_milestone is not None:
        console.print(
            f"  [bold magenta]Next milestone:[/bold magenta] {next_milestone} days  "
            f"[dim]({days_to_milestone} day{'s' if days_to_milestone != 1 else ''} to go)[/dim]"
        )
    else:
        console.print("  [bold magenta]Milestone:[/bold magenta] [green]All milestones reached![/green]")

    console.print()
    console.print(f"  [bold]Last {flame_days} days:[/bold]  {flame_bar}")

    console.print()
    console.print(f"  [bold]Last {cal_days} days:[/bold]")
    console.print(f"  [dim]{cal_header}[/dim]")
    console.print(f" {cal_marks}")
    console.print()


def cmd_note(args: argparse.Namespace) -> None:
    """Long-form notes — add, list, view, delete."""
    from .notes import add_note, list_notes, get_note, delete_note
    from rich.table import Table, box as rbox
    from rich.markdown import Markdown

    subcmd = getattr(args, "note_cmd", None)

    if subcmd == "add":
        title = args.title
        body = args.body if args.body else ""
        tag = getattr(args, "tag", None)
        note = add_note(title, body, tag)
        tag_str = f"  [yellow][{note['tag']}][/yellow]" if note.get("tag") else ""
        console.print(f"[green]✓ Note #{note['id']} saved:[/green] {note['title']}{tag_str}  [dim]({note['date']} {note['time']})[/dim]")

    elif subcmd == "list":
        tag_filter = getattr(args, "tag", None)
        limit = getattr(args, "limit", None)
        notes = list_notes(tag=tag_filter, limit=limit)
        if not notes:
            console.print("[dim]No notes found. Add one with: devlog note add --title '...' --body '...'[/dim]")
            return
        t = Table(box=rbox.ROUNDED, show_header=True, header_style="bold cyan", border_style="dim")
        t.add_column("ID", style="dim", justify="right", no_wrap=True)
        t.add_column("Date", style="dim", no_wrap=True)
        t.add_column("Tag", style="yellow", no_wrap=True)
        t.add_column("Title", style="white")
        t.add_column("Preview", style="dim")
        for n in notes:
            preview = (n["body"][:60] + "…") if len(n["body"]) > 60 else n["body"]
            preview = preview.replace("\n", " ")
            t.add_row(str(n["id"]), n["date"], n.get("tag") or "", n["title"], preview)
        title_str = "Notes"
        if tag_filter:
            title_str += f" [{tag_filter}]"
        console.print(Panel(t, title=title_str, border_style="cyan", box=rbox.ROUNDED))

    elif subcmd == "view":
        note = get_note(args.id)
        if note is None:
            console.print(f"[red]Note #{args.id} not found.[/red]")
            return
        tag_str = f"  [yellow][{note['tag']}][/yellow]" if note.get("tag") else ""
        header = f"[bold]{note['title']}[/bold]{tag_str}  [dim]#{note['id']} · {note['date']} {note['time']}[/dim]"
        body_md = Markdown(note["body"]) if note["body"] else "[dim](no body)[/dim]"
        console.print(Panel(body_md, title=header, border_style="cyan", box=rbox.ROUNDED))

    elif subcmd == "delete":
        ok = delete_note(args.id)
        if ok:
            console.print(f"[green]✓ Note #{args.id} deleted.[/green]")
        else:
            console.print(f"[red]Note #{args.id} not found.[/red]")

    else:
        console.print("[dim]Usage: devlog note add|list|view|delete[/dim]")
        console.print("[dim]  devlog note add --title 'My note' --body 'Details...' [--tag TAG][/dim]")
        console.print("[dim]  devlog note list [--tag TAG] [--limit N][/dim]")
        console.print("[dim]  devlog note view ID[/dim]")
        console.print("[dim]  devlog note delete ID[/dim]")


def cmd_digest(args: argparse.Namespace) -> None:
    """AI-powered standup digest for Slack/email/standup."""
    from datetime import date, timedelta

    period = getattr(args, "period", "day")
    fmt = getattr(args, "format", "slack")
    no_cache = getattr(args, "no_cache", False)

    today = date.today()
    if period == "week":
        # ISO week: Monday to today
        week_start = today - timedelta(days=today.weekday())
        since = week_start.isoformat()
        period_label = f"week of {week_start.isoformat()}"
    else:
        since = today.isoformat()
        period_label = f"{today.isoformat()}"

    entries = get_entries(since=since, until=today.isoformat())

    if not entries:
        console.print(f"[yellow]No entries found for {period_label}.[/yellow]")
        return

    if fmt == "plain":
        console.print(f"\n[bold]Digest — {period_label}[/bold]\n")
        for e in entries:
            tag_str = f"[{e['tag']}] " if e.get("tag") else ""
            console.print(f"  • {tag_str}{e['text']}")
        console.print()
        return

    # AI formats: slack or markdown
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]ANTHROPIC_API_KEY not set. Use --format plain or set the key.[/red]")
        return

    # Cache support
    import json as _json
    from pathlib import Path
    from .storage import DATA_DIR

    cache_file = DATA_DIR / "ai_cache.json"
    cache_key = f"digest:{period}:{since}:{fmt}"

    if not no_cache and cache_file.exists():
        try:
            cache = _json.loads(cache_file.read_text())
            entry_cache = cache.get(cache_key)
            if entry_cache:
                import time as _time
                if _time.time() - entry_cache.get("ts", 0) < 3600:
                    console.print(f"\n[bold]Digest — {period_label}[/bold]\n")
                    console.print(entry_cache["text"])
                    console.print("\n  [dim](cached — run with --no-cache to regenerate)[/dim]")
                    return
        except Exception:
            pass

    entry_lines = "\n".join(
        f"- [{e['date']} {e['time']}]{' [' + e['tag'] + ']' if e.get('tag') else ''} {e['text']}"
        for e in entries
    )

    if fmt == "slack":
        format_instruction = "Format for Slack: use bold (*text*) for section headers, bullet points with •, and emoji to make it scannable. Keep it under 8 bullets."
    else:
        format_instruction = "Format as Markdown: use ## headers, bullet points with -, and emoji. Keep it under 8 bullets."

    prompt = (
        f"Generate a concise standup/digest based on these devlog entries:\n\n"
        f"{entry_lines}\n\n"
        f"Instructions: {format_instruction} "
        f"Lead with what was accomplished, then any blockers (if apparent), then plans or next steps. "
        f"Be direct and professional. Period covered: {period_label}."
    )

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    console.print(f"\n[bold]Digest — {period_label}[/bold]\n")

    output_parts: list[str] = []
    try:
        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                output_parts.append(text)
    except Exception as e:
        console.print(f"\n[red]AI request failed: {e}[/red]")
        return

    print()

    # Save to cache
    full_text = "".join(output_parts)
    try:
        import time as _time
        cache: dict = {}
        if cache_file.exists():
            try:
                cache = _json.loads(cache_file.read_text())
            except Exception:
                cache = {}
        cache[cache_key] = {"text": full_text, "ts": _time.time()}
        # Evict entries older than 1 hour
        now_ts = _time.time()
        cache = {k: v for k, v in cache.items() if now_ts - v.get("ts", 0) < 3600}
        cache[cache_key] = {"text": full_text, "ts": now_ts}
        cache_file.write_text(_json.dumps(cache, indent=2))
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        prog="devlog",
        description="Minimal developer daily journal",
    )
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Add a log entry")
    p_add.add_argument("text", nargs="+", help="Entry text")
    p_add.add_argument("-t", "--tag", help="Tag (e.g. bug, feat, chore)")
    p_add.add_argument("-m", "--mood", type=int, metavar="1-5",
                       help="Mood/energy level: 1=rough 2=meh 3=okay 4=good 5=great")
    p_add.add_argument("-T", "--template", metavar="NAME",
                       help="Expand a named template prefix from ~/.devlog.toml [templates]")
    p_add.add_argument("-s", "--suggest-tag", action="store_true",
                       help="Use AI to suggest a tag for this entry (requires ANTHROPIC_API_KEY)")
    p_add.set_defaults(func=cmd_add)

    p_today = sub.add_parser("today", help="Show today's entries")
    p_today.add_argument("-f", "--format", choices=["table", "json", "markdown", "csv"], default="table")
    p_today.set_defaults(func=cmd_today)

    p_yesterday = sub.add_parser("yesterday", help="Show yesterday's entries")
    p_yesterday.set_defaults(func=cmd_yesterday)

    p_log = sub.add_parser("log", help="Show all entries or a specific date")
    p_log.add_argument("date", nargs="?", help="Date (YYYY-MM-DD)")
    p_log.add_argument("-f", "--format", choices=["table", "json", "markdown", "csv"], default="table")
    p_log.add_argument("--since", metavar="YYYY-MM-DD", help="Show entries on or after this date")
    p_log.add_argument("--until", metavar="YYYY-MM-DD", help="Show entries on or before this date")
    p_log.set_defaults(func=cmd_log)

    p_export = sub.add_parser("export", help="Export entries as Markdown, JSON, CSV, or HTML")
    p_export.add_argument("date", nargs="?", help="Date to export (omit for all)")
    p_export.add_argument("-o", "--output", help="Output file path")
    p_export.add_argument(
        "-f", "--format",
        choices=["markdown", "json", "csv", "html"],
        default=None,
        dest="format",
        help="Output format (default: markdown or config default_export_format)",
    )
    p_export.add_argument("--since", metavar="YYYY-MM-DD", help="Export entries on or after this date")
    p_export.add_argument("--until", metavar="YYYY-MM-DD", help="Export entries on or before this date")
    p_export.set_defaults(func=cmd_export)

    p_del = sub.add_parser("delete", help="Delete an entry by ID")
    p_del.add_argument("id", type=int, help="Entry ID")
    p_del.set_defaults(func=cmd_delete)

    p_search = sub.add_parser("search", help="Search entries by keyword")
    p_search.add_argument("keyword", nargs="+", help="Keyword(s) to search for")
    p_search.add_argument("-t", "--tag", help="Filter by tag")
    p_search.set_defaults(func=cmd_search)

    p_summarize = sub.add_parser("summarize", help="AI-powered summary of a day's entries")
    p_summarize.add_argument("date", nargs="?", help="Date to summarize (default: today)")
    p_summarize.add_argument("--no-cache", action="store_true", help="Skip cache and regenerate from AI")
    p_summarize.set_defaults(func=cmd_summarize)

    p_edit = sub.add_parser("edit", help="Edit an existing entry by ID")
    p_edit.add_argument("id", type=int, help="Entry ID to edit")
    p_edit.add_argument("text", nargs="*", help="New entry text (omit to keep current)")
    p_edit.add_argument("-t", "--tag", nargs="?", default=..., const=None,
                        help="New tag (omit flag to keep current; -t with no value clears the tag)")
    p_edit.set_defaults(func=cmd_edit)

    p_stats = sub.add_parser("stats", help="Show entry statistics and tag breakdown")
    p_stats.add_argument("--days", type=int, default=30, metavar="N",
                         help="Number of past days to include (default: 30)")
    p_stats.add_argument("--all-days", action="store_true",
                         help="Show all days including empty ones")
    p_stats.set_defaults(func=cmd_stats)

    p_week = sub.add_parser("week", help="Show entries for a full ISO week")
    p_week.add_argument("week", nargs="?", metavar="YYYY-WNN",
                        help="Week to show, e.g. 2026-W18 (default: current week)")
    p_week.set_defaults(func=cmd_week)

    p_dash = sub.add_parser("dash", help="Live-updating Rich dashboard for today's entries")
    p_dash.set_defaults(func=cmd_dash)

    p_review = sub.add_parser("review", help="AI weekly productivity review (streamed)")
    p_review.add_argument("--week", metavar="YYYY-WNN",
                          help="Week to review, e.g. 2026-W18 (default: current week)")
    p_review.set_defaults(func=cmd_review)

    # goal subcommand
    p_goal = sub.add_parser("goal", help="Manage weekly goals")
    goal_sub = p_goal.add_subparsers(dest="goal_cmd")

    pg_add = goal_sub.add_parser("add", help="Add a new goal")
    pg_add.add_argument("text", nargs="+", help="Goal description")
    pg_add.add_argument("--week", metavar="YYYY-WNN",
                        help="Target week (default: current week)")

    pg_done = goal_sub.add_parser("done", help="Mark a goal as complete")
    pg_done.add_argument("id", type=int, help="Goal ID")

    pg_del = goal_sub.add_parser("delete", help="Delete a goal")
    pg_del.add_argument("id", type=int, help="Goal ID")

    pg_list = goal_sub.add_parser("list", help="List goals")
    pg_list.add_argument("--week", metavar="YYYY-WNN",
                         help="Filter to a specific week (default: all weeks)")

    pg_check = goal_sub.add_parser("check", help="AI accountability check against this week's entries")

    p_goal.set_defaults(func=cmd_goal)

    p_heatmap = sub.add_parser("heatmap", help="GitHub-style activity heatmap calendar")
    p_heatmap.add_argument(
        "--weeks", type=int, default=16, metavar="N",
        help="Number of weeks to display (default: 16)",
    )
    p_heatmap.set_defaults(func=cmd_heatmap)

    p_mood = sub.add_parser("mood", help="Show mood/energy chart for recent entries")
    p_mood.add_argument("--days", type=int, default=30, metavar="N",
                        help="Number of past days to include (default: 30)")
    p_mood.add_argument("--insight", action="store_true",
                        help="Stream an AI analysis of your mood trends")
    p_mood.set_defaults(func=cmd_mood)

    p_remind = sub.add_parser("remind", help="Print a reminder if no entries logged today (exits 1 if unlogged)")
    p_remind.set_defaults(func=cmd_remind)

    p_completions = sub.add_parser("completions", help="Print shell completion script (bash/zsh/fish)")
    p_completions.add_argument("shell", choices=["bash", "zsh", "fish"], help="Target shell")
    p_completions.set_defaults(func=cmd_completions)

    p_month = sub.add_parser("month", help="Monthly entry summary with optional AI retro")
    p_month.add_argument("month", nargs="?", metavar="YYYY-MM",
                         help="Month to view, e.g. 2026-05 (default: current month)")
    p_month.add_argument("--ai", action="store_true",
                         help="Stream an AI monthly retro (requires ANTHROPIC_API_KEY)")
    p_month.set_defaults(func=cmd_month)

    p_import = sub.add_parser("import", help="Bulk import entries from a text/JSON/CSV file")
    p_import.add_argument("file", help="Path to the import file")
    p_import.add_argument("--date", metavar="YYYY-MM-DD",
                          help="Override date for imported entries (default: today)")
    p_import.add_argument("--tag", help="Default tag for imported entries")
    p_import.add_argument("--format", choices=["text", "json", "csv"], default=None,
                          help="Force file format (auto-detected from extension by default)")
    p_import.add_argument("--dry-run", action="store_true",
                          help="Preview what would be imported without saving")
    p_import.set_defaults(func=cmd_import)

    p_sem = sub.add_parser("semantic", help="Semantic search using TF-IDF cosine similarity")
    p_sem.add_argument("query", nargs="+", help="Natural language search query")
    p_sem.add_argument("--top", type=int, default=10, metavar="N", help="Number of results (default: 10)")
    p_sem.set_defaults(func=cmd_semantic)

    p_aitag = sub.add_parser("ai-tag", help="Auto-tag untagged entries in bulk using AI")
    p_aitag.add_argument("--count", "-n", type=int, metavar="N", help="Max entries to tag (default: all untagged)")
    p_aitag.set_defaults(func=cmd_ai_tag)

    p_focus = sub.add_parser("focus", help="Show your most productive hours based on entry timing")
    p_focus.add_argument("--all-hours", action="store_true", help="Show all 24 hours including empty ones")
    p_focus.set_defaults(func=cmd_focus)

    p_sync_git = sub.add_parser("sync-git", help="Import recent git commits as journal entries")
    p_sync_git.add_argument("path", nargs="?", default=".", help="Path to git repo (default: .)")
    p_sync_git.add_argument("--since", metavar="TIMESPEC",
                            help="How far back to look (default: '1 day ago'). Examples: '7 days ago', '2026-05-01'")
    p_sync_git.add_argument("--tag", default="commit", help="Tag for imported entries (default: commit)")
    p_sync_git.add_argument("--dry-run", action="store_true", help="Preview without saving")
    p_sync_git.set_defaults(func=cmd_sync_git)

    p_timer = sub.add_parser("timer", help="Pomodoro-style countdown timer with auto-log on completion")
    p_timer.add_argument("minutes", type=int, nargs="?", default=25,
                         help="Timer duration in minutes (default: 25)")
    p_timer.add_argument("--label", "-l", metavar="TEXT",
                         help="Label for this session (default: 'Nm session')")
    p_timer.add_argument("--tag", "-t", help="Tag for the auto-logged entry (default: focus)")
    p_timer.set_defaults(func=cmd_timer)

    p_tags = sub.add_parser("tags", help="List entry tags with counts or rename a tag")
    tags_sub = p_tags.add_subparsers(dest="tags_cmd")
    tags_sub.add_parser("list", help="List all tags with entry counts")
    pt_rename = tags_sub.add_parser("rename", help="Rename a tag across all entries")
    pt_rename.add_argument("old_tag", help="Existing tag name")
    pt_rename.add_argument("new_tag", help="New tag name")
    p_tags.set_defaults(func=cmd_tags)

    p_streak = sub.add_parser("streak", help="Streak summary with milestones and best-ever record")
    p_streak.set_defaults(func=cmd_streak)

    # note subcommand
    p_note = sub.add_parser("note", help="Manage long-form notes with title, body, and optional tag")
    note_sub = p_note.add_subparsers(dest="note_cmd")

    pn_add = note_sub.add_parser("add", help="Add a new note")
    pn_add.add_argument("--title", "-T", required=True, help="Note title")
    pn_add.add_argument("--body", "-b", default="", help="Note body (supports Markdown)")
    pn_add.add_argument("--tag", "-t", help="Optional tag")

    pn_list = note_sub.add_parser("list", help="List notes")
    pn_list.add_argument("--tag", "-t", help="Filter by tag")
    pn_list.add_argument("--limit", "-n", type=int, metavar="N", help="Maximum number of notes to show")

    pn_view = note_sub.add_parser("view", help="View a note by ID")
    pn_view.add_argument("id", type=int, help="Note ID")

    pn_del = note_sub.add_parser("delete", help="Delete a note by ID")
    pn_del.add_argument("id", type=int, help="Note ID")

    p_note.set_defaults(func=cmd_note)

    p_digest = sub.add_parser("digest", help="AI-powered standup digest for Slack/email/standup")
    p_digest.add_argument(
        "--period", choices=["day", "week"], default="day",
        help="Time period to cover (default: day)",
    )
    p_digest.add_argument(
        "--format", "-f", choices=["slack", "markdown", "plain"], default="slack",
        dest="format",
        help="Output format (default: slack). 'plain' requires no API key.",
    )
    p_digest.add_argument(
        "--no-cache", action="store_true",
        help="Bypass cache and regenerate from AI",
    )
    p_digest.set_defaults(func=cmd_digest)

    # habit subcommand
    p_habit = sub.add_parser("habit", help="Daily habit tracker with streaks and Rich status view")
    habit_sub = p_habit.add_subparsers(dest="habit_cmd")

    ph_add = habit_sub.add_parser("add", help="Add a new habit to track")
    ph_add.add_argument("name", help="Habit name (e.g. 'exercise', 'read 30min')")

    ph_del = habit_sub.add_parser("delete", help="Remove a habit by ID")
    ph_del.add_argument("id", type=int, help="Habit ID")

    ph_check = habit_sub.add_parser("check", help="Mark a habit done for today")
    ph_check.add_argument("id", type=int, help="Habit ID")
    ph_check.add_argument("--date", metavar="YYYY-MM-DD", help="Override date (default: today)")
    ph_check.add_argument("--note", default="", help="Optional note for this check-in")

    ph_uncheck = habit_sub.add_parser("uncheck", help="Remove today's check-in for a habit")
    ph_uncheck.add_argument("id", type=int, help="Habit ID")
    ph_uncheck.add_argument("--date", metavar="YYYY-MM-DD", help="Override date (default: today)")

    ph_status = habit_sub.add_parser("status", help="Show habit streaks and recent history")
    ph_status.add_argument("--days", type=int, default=14, metavar="N",
                           help="Days of history to show (default: 14)")

    p_habit.set_defaults(func=cmd_habit)

    # metrics subcommand
    p_metrics = sub.add_parser("metrics", help="Cross-dimensional productivity metrics with AI analysis")
    p_metrics.add_argument("--days", type=int, default=30, metavar="N",
                           help="Analysis window in days (default: 30)")
    p_metrics.add_argument("--ai", action="store_true",
                           help="Stream an AI interpretation of the metrics (requires ANTHROPIC_API_KEY)")
    p_metrics.set_defaults(func=cmd_metrics)

    # standout subcommand
    p_standout = sub.add_parser("standout", help="Identify your most significant entries via TF-IDF outlier scoring")
    p_standout.add_argument("--days", type=int, default=90, metavar="N",
                            help="Analysis window in days (default: 90)")
    p_standout.add_argument("--top", type=int, default=10, metavar="N",
                            help="Number of standout entries to show (default: 10)")
    p_standout.set_defaults(func=cmd_standout)

    # pin subcommand
    p_pin = sub.add_parser("pin", help="Pin/unpin important entries for quick reference")
    pin_sub = p_pin.add_subparsers(dest="pin_cmd")
    pp_add = pin_sub.add_parser("add", help="Pin an entry by ID")
    pp_add.add_argument("id", type=int, help="Entry ID to pin")
    pp_remove = pin_sub.add_parser("remove", help="Unpin an entry by ID")
    pp_remove.add_argument("id", type=int, help="Entry ID to unpin")
    pin_sub.add_parser("list", help="Show all pinned entries (default)")
    p_pin.set_defaults(func=cmd_pin)

    # correlate subcommand
    p_corr = sub.add_parser("correlate", help="Show mood vs tag correlation table")
    p_corr.add_argument("--days", type=int, default=90, metavar="N",
                        help="Analysis window in days (default: 90)")
    p_corr.set_defaults(func=cmd_correlate)

    # ai-plan subcommand
    p_plan = sub.add_parser("ai-plan", help="AI-generated daily plan for tomorrow (requires ANTHROPIC_API_KEY)")
    p_plan.set_defaults(func=cmd_ai_plan)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


def cmd_heatmap(args: argparse.Namespace) -> None:
    """GitHub-style activity heatmap for the last N weeks."""
    from datetime import date, timedelta
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from rich.text import Text

    weeks = args.weeks
    today = date.today()
    start_monday = today - timedelta(days=today.weekday() + 7 * (weeks - 1))

    stats = get_stats(days=weeks * 7 + 7)
    by_date = stats["by_date"]

    PALETTE = ["[dim]·[/dim]", "[green]▪[/green]", "[green]■[/green]",
               "[bright_green]■[/bright_green]", "[bold bright_green]■[/bold bright_green]"]

    def _cell(count: int) -> str:
        if count == 0:
            return PALETTE[0]
        if count == 1:
            return PALETTE[1]
        if count <= 3:
            return PALETTE[2]
        if count <= 6:
            return PALETTE[3]
        return PALETTE[4]

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    week_starts = [start_monday + timedelta(weeks=w) for w in range(weeks)]

    table = Table(
        box=None, show_header=True, header_style="dim cyan",
        pad_edge=False, show_edge=False, show_lines=False,
    )
    table.add_column("   ", width=3, no_wrap=True)
    for w, ws in enumerate(week_starts):
        table.add_column(
            ws.strftime("%m/%d") if w % 4 == 0 else "",
            justify="center", width=2, no_wrap=True,
        )

    for day_idx in range(7):
        row = [f"[dim]{day_labels[day_idx]}[/dim]"]
        for ws in week_starts:
            d = ws + timedelta(days=day_idx)
            row.append("  " if d > today else _cell(by_date.get(d.isoformat(), 0)))
        table.add_row(*row)

    max_count = max(by_date.values(), default=0)
    total = sum(by_date.values())
    active_days = sum(1 for c in by_date.values() if c > 0)

    console.print(Panel(table, title=f"Activity heatmap — last {weeks} weeks",
                        border_style="cyan", box=rbox.ROUNDED))
    console.print(
        f"\n  [dim]Total: {total} entries  ·  Active: {active_days} days  "
        f"·  Peak: {max_count}/day[/dim]\n"
        f"  [dim]Legend: · 0  ▪ 1  ■ 2-3  [bright_green]■[/bright_green] 4-6  "
        f"[bold bright_green]■[/bold bright_green] 7+[/dim]"
    )


def cmd_completions(args: argparse.Namespace) -> None:
    """Print a shell completion script for devlog."""
    shell = args.shell

    if shell == "bash":
        script = r"""# devlog bash completion — source this or add to ~/.bashrc:
# eval "$(devlog completions bash)"
_devlog_complete() {
    local cur prev
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    local subcommands="add today yesterday log export delete search edit stats week dash review goal summarize completions heatmap tags mood remind month import"
    local goal_subcmds="add done delete list check"

    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$subcommands" -- "$cur"))
    elif [[ $COMP_CWORD -eq 2 ]]; then
        case $prev in
            goal)        COMPREPLY=($(compgen -W "$goal_subcmds" -- "$cur")) ;;
            completions) COMPREPLY=($(compgen -W "bash zsh fish" -- "$cur")) ;;
            tags)        COMPREPLY=($(compgen -W "list rename" -- "$cur")) ;;
            export|log|today) COMPREPLY=($(compgen -W "-f --format --since --until" -- "$cur")) ;;
        esac
    fi
}
complete -F _devlog_complete devlog
"""
    elif shell == "zsh":
        script = r"""#compdef devlog
# devlog zsh completion — source or add to ~/.zshrc:
# eval "$(devlog completions zsh)"
_devlog() {
    local -a subcommands
    subcommands=(
        'add:Add a log entry'
        'today:Show today'\''s entries'
        'yesterday:Show yesterday'\''s entries'
        'log:Show all entries or a specific date'
        'export:Export entries as Markdown/JSON/CSV'
        'delete:Delete an entry by ID'
        'search:Search entries by keyword'
        'edit:Edit an existing entry by ID'
        'stats:Show entry statistics and tag breakdown'
        'week:Show entries for a full ISO week'
        'dash:Live-updating Rich dashboard'
        'review:AI weekly productivity review'
        'goal:Manage weekly goals'
        'summarize:AI-powered summary of a day'\''s entries'
        'completions:Generate shell completion script'
        'heatmap:GitHub-style activity heatmap calendar'
        'tags:List and manage entry tags'
        'mood:Show mood/energy chart for recent entries'
        'remind:Print a reminder if no entries logged today'
        'month:Monthly entry summary with optional AI retro'
        'import:Bulk import entries from a text/JSON/CSV file'
    )
    _arguments -C '1:command:->cmd' '*::arg:->args'
    case $state in
        cmd)  _describe 'commands' subcommands ;;
        args)
            case $words[1] in
                goal)        local -a gc; gc=('add:Add' 'done:Mark done' 'delete:Delete' 'list:List' 'check:AI check'); _describe 'goal subcommands' gc ;;
                completions) _values 'shell' bash zsh fish ;;
                tags)        local -a tc; tc=('list:List all tags' 'rename:Rename a tag'); _describe 'tag subcommands' tc ;;
                export|log)  _arguments '-f[format]:format:(markdown json csv)' '--since[since date]:date:' '--until[until date]:date:' ;;
                heatmap)     _arguments '--weeks[number of weeks]:weeks:' ;;
            esac ;;
    esac
}
_devlog
"""
    elif shell == "fish":
        script = """# devlog fish completion
# Save to ~/.config/fish/completions/devlog.fish

set -l cmds add today yesterday log export delete search edit stats week dash review goal summarize completions heatmap tags mood remind month import

complete -c devlog -f -n 'not __fish_seen_subcommand_from $cmds' -a "$cmds"
complete -c devlog -n '__fish_seen_subcommand_from goal' -a 'add done delete list check'
complete -c devlog -n '__fish_seen_subcommand_from completions' -a 'bash zsh fish'
complete -c devlog -n '__fish_seen_subcommand_from tags' -a 'list rename'
complete -c devlog -n '__fish_seen_subcommand_from export log today' -s f -l format -a 'markdown json csv'
complete -c devlog -n '__fish_seen_subcommand_from heatmap' -l weeks -d 'Number of weeks to show'
"""
    else:
        console.print(f"[red]Unknown shell '{shell}'. Choose: bash, zsh, fish[/red]")
        return

    print(script)


def cmd_mood(args: argparse.Namespace) -> None:
    """Show a mood chart for the last N days, with optional AI insights."""
    from datetime import date, timedelta
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from rich.text import Text

    days = args.days
    today = date.today()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    all_entries = load_entries()
    mood_rows: list[tuple[str, list[int]]] = []
    for d in date_range:
        moods = [e["mood"] for e in all_entries if e["date"] == d and e.get("mood") is not None]
        if moods:
            mood_rows.append((d, moods))

    if not mood_rows:
        console.print(
            "[dim]No mood data yet. Add moods with: devlog add -m 4 \"your entry\"[/dim]\n"
            "  Scale: 1 = rough, 2 = meh, 3 = okay, 4 = good, 5 = great"
        )
        return

    MOOD_BLOCKS = {1: "[red]▓[/red]", 2: "[yellow]▓[/yellow]", 3: "[dim]▓[/dim]", 4: "[cyan]▓[/cyan]", 5: "[green]▓[/green]"}
    MOOD_LABELS = {1: "rough", 2: "meh", 3: "okay", 4: "good", 5: "great"}

    table = Table(box=rbox.SIMPLE, show_header=True, header_style="bold cyan", pad_edge=False)
    table.add_column("Date", style="dim", no_wrap=True)
    table.add_column("Avg", justify="center", width=4)
    table.add_column("Chart", width=20)
    table.add_column("Entries", style="dim", width=7, justify="right")

    all_moods: list[float] = []
    for d, moods in mood_rows:
        avg = sum(moods) / len(moods)
        all_moods.append(avg)
        lvl = round(avg)
        bar = MOOD_BLOCKS[lvl] * max(1, round(avg * 3))
        table.add_row(d, f"{avg:.1f}", bar, str(len(moods)))

    overall = sum(all_moods) / len(all_moods) if all_moods else 0
    lvl = round(overall)

    console.print(Panel(table, title=f"Mood — last {days} days", border_style="cyan", box=rbox.ROUNDED))
    console.print(
        f"\n  [bold cyan]Average:[/bold cyan] [{_mood_style(lvl)}]{overall:.1f}/5 {_mood_icon(lvl)} {MOOD_LABELS.get(lvl, '')}[/{_mood_style(lvl)}]  "
        f"[dim]·[/dim]  [dim]{len(mood_rows)} days with mood data[/dim]"
    )
    console.print(
        "\n  [dim]Legend: [red]▓[/red] rough  [yellow]▓[/yellow] meh  ▓ okay  [cyan]▓[/cyan] good  [green]▓[/green] great[/dim]"
    )

    if getattr(args, "insight", False):
        _cmd_mood_insight(mood_rows)


def _cmd_mood_insight(mood_rows: list[tuple[str, list[int]]]) -> None:
    """Stream an AI analysis of mood trends."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Set ANTHROPIC_API_KEY first.[/red]")
        return
    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        return

    lines = "\n".join(f"- {d}: avg mood {sum(m)/len(m):.1f}/5 ({len(m)} entries)" for d, m in mood_rows)
    prompt = (
        f"Here is my mood-per-day data from my developer journal:\n\n{lines}\n\n"
        "Identify any trends (improving, declining, weekly patterns). "
        "Give one concrete observation and one actionable suggestion. "
        "Be brief (3-4 sentences). Be empathetic but practical."
    )
    client = anthropic.Anthropic(api_key=api_key)
    console.print("\n[bold cyan]Mood Insight[/bold cyan]\n")
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def cmd_remind(args: argparse.Namespace) -> None:
    """Print a reminder if no entries logged today; exit 1 if unlogged."""
    today = date.today().isoformat()
    entries = get_entries(day=today)
    if entries:
        console.print(
            f"[green]✓ You've already logged {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} today.[/green]"
            f"  [dim]Last: {entries[-1]['text'][:60]}[/dim]"
        )
        sys.exit(0)
    else:
        msg = _cfg.get("remind_message", "No devlog entries yet today. What are you working on?")
        console.print(f"[yellow]⊙[/yellow] {msg}")
        console.print("[dim]  Add one with: devlog add \"your note here\"[/dim]")
        sys.exit(1)


def cmd_month(args: argparse.Namespace) -> None:
    """Show a monthly summary of entries with week breakdown and optional AI retro."""
    import re
    from calendar import monthrange
    from datetime import date
    from collections import Counter
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from rich.columns import Columns

    today = date.today()
    if args.month:
        m = re.match(r'^(\d{4})-(\d{2})$', args.month)
        if not m:
            console.print("[red]Invalid month format. Use YYYY-MM, e.g. 2026-05[/red]")
            return
        year, month_num = int(m.group(1)), int(m.group(2))
    else:
        year, month_num = today.year, today.month

    month_label = date(year, month_num, 1).strftime("%B %Y")
    _, days_in_month = monthrange(year, month_num)
    month_prefix = f"{year}-{month_num:02d}"

    all_entries = load_entries()
    entries = [e for e in all_entries if e["date"].startswith(month_prefix)]

    # Group by ISO week
    weeks: dict[str, list[dict]] = {}
    for e in entries:
        d = date.fromisoformat(e["date"])
        iso = d.isocalendar()
        wk = f"{iso[0]}-W{iso[1]:02d}"
        weeks.setdefault(wk, []).append(e)

    tag_counts: Counter = Counter(e.get("tag") for e in entries if e.get("tag"))
    active_days = len({e["date"] for e in entries})
    avg_per_day = len(entries) / days_in_month if days_in_month else 0

    # Week breakdown table
    wk_table = Table(box=rbox.SIMPLE, show_header=True, header_style="bold cyan", pad_edge=False)
    wk_table.add_column("Week", style="cyan", no_wrap=True)
    wk_table.add_column("n", justify="right", style="white", width=4)
    wk_table.add_column("", style="cyan")
    max_wk = max((len(v) for v in weeks.values()), default=1) or 1
    for wk in sorted(weeks):
        cnt = len(weeks[wk])
        bar = "█" * max(1, round(cnt / max_wk * 18))
        wk_table.add_row(wk, str(cnt), bar)

    console.print(Panel(wk_table, title=f"Month — {month_label}", border_style="cyan", box=rbox.ROUNDED))

    if tag_counts:
        tg_table = Table(box=rbox.SIMPLE, show_header=True, header_style="bold yellow", pad_edge=False)
        tg_table.add_column("Tag", style="yellow")
        tg_table.add_column("n", justify="right", style="white", width=4)
        max_c = tag_counts.most_common(1)[0][1] or 1
        for tag, cnt in tag_counts.most_common(10):
            tg_table.add_row(tag, str(cnt))
        console.print(Panel(tg_table, title="Tags this month", border_style="yellow", box=rbox.ROUNDED))

    console.print(
        f"\n  [bold cyan]{month_label}:[/bold cyan]  "
        f"[dim]{len(entries)} entries  ·  {active_days}/{days_in_month} active days  "
        f"·  {len(weeks)} active weeks  ·  avg {avg_per_day:.1f}/day[/dim]"
    )

    if not entries:
        console.print("[dim]No entries for this month.[/dim]")
        return

    if getattr(args, "ai", False):
        _cmd_month_ai(entries, month_label, tag_counts)


def _cmd_month_ai(entries: list[dict], month_label: str, tag_counts: "Counter") -> None:
    """Stream an AI monthly retro for the given entries."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Set ANTHROPIC_API_KEY first.[/red]")
        return
    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        return

    bullet_list = "\n".join(
        f"- [{e['date']} {e['time']}]{' [' + e['tag'] + ']' if e.get('tag') else ''} {e['text']}"
        for e in entries
    )
    prompt = (
        f"Here are my developer journal entries for {month_label}:\n\n"
        f"{bullet_list}\n\n"
        f"Tag distribution: {dict(tag_counts)}\n\n"
        "Write a concise monthly retro (4-6 sentences) covering:\n"
        "1. Major themes and accomplishments this month\n"
        "2. Any patterns or notable work rhythms\n"
        "3. One goal or focus area to carry into next month\n\n"
        "Be specific and developer-focused. Use markdown."
    )
    client = anthropic.Anthropic(api_key=api_key)
    console.print(f"\n[bold cyan]Monthly Retro — {month_label}[/bold cyan]\n")
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def cmd_import(args: argparse.Namespace) -> None:
    """Bulk import entries from a plain-text, JSON, or CSV file."""
    import json as _json
    import csv as _csv
    import io
    from datetime import date, datetime
    from pathlib import Path

    path = Path(args.file)
    if not path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        return

    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        console.print("[yellow]File is empty.[/yellow]")
        return

    # Detect format
    fmt = args.format
    if fmt is None:
        suffix = path.suffix.lower()
        if suffix == ".json":
            fmt = "json"
        elif suffix == ".csv":
            fmt = "csv"
        else:
            fmt = "text"

    new_entries: list[dict] = []
    default_date = args.date or date.today().isoformat()
    default_tag = args.tag or _cfg.get("default_tag")

    if fmt == "json":
        try:
            data = _json.loads(raw)
        except _json.JSONDecodeError as e:
            console.print(f"[red]JSON parse error: {e}[/red]")
            return
        if not isinstance(data, list):
            console.print("[red]JSON file must contain an array of entry objects.[/red]")
            return
        for obj in data:
            if not isinstance(obj, dict) or not obj.get("text"):
                continue
            new_entries.append({
                "text": str(obj["text"]),
                "tag": obj.get("tag") or default_tag,
                "date": obj.get("date") or default_date,
                "time": obj.get("time") or datetime.now().strftime("%H:%M"),
            })

    elif fmt == "csv":
        reader = _csv.DictReader(io.StringIO(raw))
        for row in reader:
            text = row.get("text", "").strip()
            if not text:
                continue
            new_entries.append({
                "text": text,
                "tag": row.get("tag") or default_tag,
                "date": row.get("date") or default_date,
                "time": row.get("time") or datetime.now().strftime("%H:%M"),
            })

    else:  # plain text
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Optional inline tag: [tag] entry text
            tag = default_tag
            import re as _re
            m = _re.match(r'^\[([^\]]+)\]\s+(.*)', line)
            if m:
                tag, line = m.group(1), m.group(2)
            new_entries.append({
                "text": line,
                "tag": tag,
                "date": default_date,
                "time": datetime.now().strftime("%H:%M"),
            })

    if not new_entries:
        console.print("[yellow]No valid entries found in file.[/yellow]")
        return

    if args.dry_run:
        console.print(f"[cyan]Dry run — {len(new_entries)} entries would be imported:[/cyan]\n")
        for i, e in enumerate(new_entries[:20], 1):
            tag_str = f"[yellow]\\[{e['tag']}][/yellow] " if e.get("tag") else ""
            console.print(f"  [dim]{i}.[/dim] {e['date']} {tag_str}{e['text']}")
        if len(new_entries) > 20:
            console.print(f"  [dim]... and {len(new_entries) - 20} more[/dim]")
        return

    # Load and append
    existing = load_entries()
    next_id = max((e["id"] for e in existing), default=0) + 1
    for e in new_entries:
        e["id"] = next_id
        next_id += 1
    save_entries(existing + new_entries)
    console.print(f"[green]✓ Imported {len(new_entries)} entries from {path.name}[/green]")


def cmd_sync_git(args: argparse.Namespace) -> None:
    """Import recent git commits from a repo as journal entries."""
    from .gitimport import get_recent_commits

    repo = args.path or "."
    since = args.since or "1 day ago"
    tag = args.tag or "commit"

    commits = get_recent_commits(repo_path=repo, since=since)
    if not commits:
        console.print(f"[yellow]No commits found in '{repo}' since '{since}'.[/yellow]")
        return

    if args.dry_run:
        console.print(f"[cyan]Dry run — {len(commits)} commits found:[/cyan]\n")
        for c in commits[:20]:
            console.print(f"  [dim]{c['date']} {c['time']}[/dim] [yellow][{tag}][/yellow] {c['subject']} [dim]({c['sha']})[/dim]")
        if len(commits) > 20:
            console.print(f"  [dim]... and {len(commits) - 20} more[/dim]")
        return

    existing = load_entries()
    # Avoid duplicates by checking for entries with same sha in text
    existing_texts = {e["text"] for e in existing}
    new_entries = []
    for c in commits:
        text = f"{c['subject']} [{c['sha']}]"
        if text in existing_texts:
            continue
        new_entries.append({
            "id": 0,  # assigned below
            "date": c["date"],
            "time": c["time"],
            "text": text,
            "tag": tag,
        })

    if not new_entries:
        console.print("[dim]No new commits to import (all already logged).[/dim]")
        return

    next_id = max((e["id"] for e in existing), default=0) + 1
    for e in new_entries:
        e["id"] = next_id
        next_id += 1

    save_entries(existing + new_entries)
    console.print(f"[green]✓ Imported {len(new_entries)} commits from '{repo}' as entries (tag: [yellow]{tag}[/yellow])[/green]")
    for e in new_entries[:10]:
        console.print(f"  [dim]{e['date']} {e['time']}[/dim] {e['text']}")
    if len(new_entries) > 10:
        console.print(f"  [dim]... and {len(new_entries) - 10} more[/dim]")


def cmd_timer(args: argparse.Namespace) -> None:
    """Pomodoro-style timer with Rich Live countdown and auto-log on completion."""
    import time as _time
    from rich.live import Live
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text
    from rich.table import Table, box as rbox

    minutes = args.minutes
    label = args.label or f"{minutes}m session"
    tag = args.tag or _cfg.get("default_tag") or "focus"
    total_secs = minutes * 60

    POMODORO_ICONS = ["🍅", "⏱", "🔥", "⚡", "🎯"]
    icon = POMODORO_ICONS[minutes % len(POMODORO_ICONS)]

    console.print(f"\n[bold cyan]{icon} Timer started:[/bold cyan] {label} ({minutes} min)\n"
                  f"  [dim]Press Ctrl+C to cancel and log partial session.[/dim]\n")

    start = _time.monotonic()
    elapsed = 0.0
    cancelled = False

    def _render(elapsed: float) -> Panel:
        remaining = max(0.0, total_secs - elapsed)
        pct = min(1.0, elapsed / total_secs)
        mins_left = int(remaining // 60)
        secs_left = int(remaining % 60)

        BAR_WIDTH = 40
        filled = round(pct * BAR_WIDTH)
        bar = "[cyan]" + "█" * filled + "[/cyan]" + "[dim]" + "░" * (BAR_WIDTH - filled) + "[/dim]"

        t = Table.grid(expand=True)
        t.add_column(justify="center")
        t.add_row(Text(f"{icon}  {label}", style="bold cyan"))
        t.add_row(Text(""))
        t.add_row(Text(f"{bar}  {pct:.0%}", justify="center"))
        t.add_row(Text(""))
        t.add_row(Text(f"{mins_left:02d}:{secs_left:02d} remaining", style="bold", justify="center"))
        t.add_row(Text(f"elapsed {int(elapsed // 60):02d}:{int(elapsed % 60):02d}", style="dim", justify="center"))
        return Panel(t, border_style="cyan", box=rbox.ROUNDED)

    try:
        with Live(_render(0), refresh_per_second=2, screen=False) as live:
            while True:
                _time.sleep(0.5)
                elapsed = _time.monotonic() - start
                live.update(_render(elapsed))
                if elapsed >= total_secs:
                    break
    except KeyboardInterrupt:
        elapsed = _time.monotonic() - start
        cancelled = True

    elapsed_mins = int(elapsed) // 60
    elapsed_secs = int(elapsed) % 60

    if cancelled:
        console.print(f"\n[yellow]⊙ Timer cancelled after {elapsed_mins:02d}:{elapsed_secs:02d}.[/yellow]")
    else:
        console.print(f"\n[green]✓ Timer complete! {minutes} minute session finished.[/green]")

    console.print(f"\n[dim]What did you work on during this session?[/dim]")
    try:
        note = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        note = ""

    if note:
        duration_note = f" ({elapsed_mins}m{elapsed_secs:02d}s)"
        text = f"{note}{duration_note}"
        entry = add_entry(text, tag=tag)
        tag_str = f"[yellow]\\[{entry['tag']}][/yellow] " if entry.get("tag") else ""
        console.print(
            f"\n[green]✓[/green] Logged: {tag_str}{entry['text']} "
            f"[dim]({entry['date']} {entry['time']})[/dim]"
        )
    else:
        console.print("[dim]  (no entry logged)[/dim]")


def cmd_tags(args: argparse.Namespace) -> None:
    """List all tags with entry counts, or rename a tag across all entries."""
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from collections import Counter

    subcmd = args.tags_cmd

    if subcmd == "list":
        all_entries = get_entries()
        counts: Counter = Counter(e.get("tag") for e in all_entries if e.get("tag"))
        if not counts:
            console.print("[dim]No tags found. Add tagged entries with: devlog add -t TAG ...[/dim]")
            return

        t = Table(box=rbox.ROUNDED, show_header=True, header_style="bold yellow", border_style="dim")
        t.add_column("Tag", style="yellow")
        t.add_column("Count", justify="right", style="white")
        t.add_column("", style="cyan")  # bar

        max_c = counts.most_common(1)[0][1] or 1
        for tag, cnt in counts.most_common():
            bar = "█" * max(1, round(cnt / max_c * 20))
            t.add_row(tag, str(cnt), bar)

        console.print(Panel(t, title=f"Tags ({len(counts)} unique, {sum(counts.values())} tagged entries)",
                            border_style="yellow", box=rbox.ROUNDED))

    elif subcmd == "rename":
        old_tag, new_tag = args.old_tag, args.new_tag
        all_entries = get_entries()
        changed = 0
        for e in all_entries:
            if e.get("tag") == old_tag:
                e["tag"] = new_tag
                changed += 1
        if changed == 0:
            console.print(f"[yellow]No entries with tag '{old_tag}' found.[/yellow]")
            return
        from .storage import save_entries
        save_entries(all_entries)
        console.print(f"[green]✓ Renamed tag '{old_tag}' → '{new_tag}' across {changed} entries[/green]")

    else:
        console.print("[dim]Usage: devlog tags list | devlog tags rename OLD NEW[/dim]")


def cmd_habit(args: argparse.Namespace) -> None:
    """Manage daily habits: track streaks and view history."""
    from .habits import add_habit, delete_habit, check_habit, uncheck_habit, get_status
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from rich.text import Text

    subcmd = getattr(args, "habit_cmd", None)

    if subcmd == "add":
        try:
            habit = add_habit(args.name)
        except ValueError as e:
            console.print(f"[red]✗ {e}[/red]")
            return
        console.print(f"[green]✓[/green] Habit [cyan]#{habit['id']}[/cyan] added: {habit['name']}")

    elif subcmd == "delete":
        from .habits import delete_habit
        if delete_habit(args.id):
            console.print(f"[green]✓ Habit #{args.id} deleted.[/green]")
        else:
            console.print(f"[red]✗ Habit #{args.id} not found.[/red]")

    elif subcmd == "check":
        if check_habit(args.id, day=getattr(args, "date", None), note=args.note):
            console.print(f"[green]✓ Habit #{args.id} checked for {getattr(args, 'date', None) or 'today'}[/green]")
        else:
            console.print(f"[red]✗ Habit #{args.id} not found.[/red]")

    elif subcmd == "uncheck":
        from .habits import uncheck_habit
        day = getattr(args, "date", None)
        if uncheck_habit(args.id, day=day):
            console.print(f"[green]✓ Check-in removed for habit #{args.id}[/green]")
        else:
            console.print(f"[yellow]No check-in found for habit #{args.id} on {day or 'today'}.[/yellow]")

    elif subcmd == "status" or subcmd is None:
        days = getattr(args, "days", 14)
        statuses = get_status(days=days)

        if not statuses:
            console.print(
                "[dim]No habits yet. Add one with:[/dim]\n"
                "  [cyan]devlog habit add \"your habit\"[/cyan]"
            )
            return

        t = Table(
            box=rbox.ROUNDED, show_header=True, header_style="bold cyan",
            border_style="dim", expand=False,
        )
        t.add_column("ID", style="dim", justify="right", width=4)
        t.add_column("Habit", style="white")
        t.add_column("Streak", justify="right", style="bold yellow", width=7)
        t.add_column("%", justify="right", style="cyan", width=5)
        t.add_column(f"Last {days} days →", style="dim")

        DONE = "[green]■[/green]"
        MISS = "[dim]·[/dim]"

        for s in statuses:
            bar = "".join(DONE if h else MISS for h in s["history"])
            streak_str = f"{s['streak']}d" if s["streak"] else "—"
            t.add_row(str(s["id"]), s["name"], streak_str, f"{s['rate']}%", bar)

        console.print(Panel(t, title=f"Habits — last {days} days", border_style="cyan", box=rbox.ROUNDED))
        console.print(
            f"  [dim]Legend: [green]■[/green] done  · missed  "
            f"·  devlog habit check ID  to log today's completion[/dim]"
        )

    else:
        console.print("[dim]Usage: devlog habit add|delete|check|uncheck|status[/dim]")


def cmd_metrics(args: argparse.Namespace) -> None:
    """Show cross-dimensional productivity metrics and optionally stream AI interpretation."""
    from .metrics import compute_metrics
    from .storage import load_entries
    from rich.table import Table, box as rbox
    from rich.panel import Panel

    days = args.days
    entries = load_entries()
    m = compute_metrics(entries, days=days)

    if not m["total_entries"]:
        console.print(f"[dim]No entries in the last {days} days.[/dim]")
        return

    # Summary table
    t = Table(box=rbox.SIMPLE, show_header=False, pad_edge=False)
    t.add_column("Metric", style="cyan")
    t.add_column("Value", style="white", justify="right")

    t.add_row("Total entries", str(m["total_entries"]))
    t.add_row("Active days", f"{m['active_days']} / {days}")
    t.add_row("Velocity", f"{m['velocity']:.2f} entries/day")
    t.add_row("Trend", m["velocity_trend"])
    if m["peak_hour"] is not None:
        t.add_row("Peak hour", f"{m['peak_hour']:02d}:00")
    if m["busiest_weekday"]:
        t.add_row("Busiest weekday", m["busiest_weekday"])
    if m["avg_mood"] is not None:
        t.add_row("Avg mood", f"{m['avg_mood']:.1f}/5")
    if m["mood_variance"] is not None:
        t.add_row("Mood variance", f"±{m['mood_variance']:.2f}")

    console.print(Panel(t, title=f"Productivity Metrics — last {days} days", border_style="cyan", box=rbox.ROUNDED))

    # Tag table
    if m["top_tags"]:
        tg = Table(box=rbox.SIMPLE, show_header=True, header_style="bold yellow", pad_edge=False)
        tg.add_column("Tag", style="yellow")
        tg.add_column("n", justify="right", width=5)
        tg.add_column("Avg mood", justify="right", width=9)
        for tag, count in m["top_tags"]:
            mood_str = f"{m['tag_moods'][tag]:.1f}" if tag in m["tag_moods"] else "—"
            tg.add_row(tag, str(count), mood_str)
        console.print(Panel(tg, title="Top tags", border_style="yellow", box=rbox.ROUNDED))

    if m["best_mood_tag"]:
        console.print(
            f"\n  [bold cyan]Happiest tag:[/bold cyan] [yellow]{m['best_mood_tag']}[/yellow] "
            f"[dim](avg mood {m['tag_moods'][m['best_mood_tag']]:.1f}/5)[/dim]"
        )
    if m["worst_mood_tag"] and m["worst_mood_tag"] != m["best_mood_tag"]:
        console.print(
            f"  [bold cyan]Hardest tag:[/bold cyan]  [yellow]{m['worst_mood_tag']}[/yellow] "
            f"[dim](avg mood {m['tag_moods'][m['worst_mood_tag']]:.1f}/5)[/dim]"
        )

    if getattr(args, "ai", False):
        _cmd_metrics_ai(m, days)


def _cmd_metrics_ai(m: dict, days: int) -> None:
    """Stream an AI interpretation of the productivity metrics."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Set ANTHROPIC_API_KEY first.[/red]")
        return
    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        return

    metric_text = (
        f"Analysis window: {days} days\n"
        f"Total entries: {m['total_entries']}\n"
        f"Active days: {m['active_days']} / {days}\n"
        f"Velocity: {m['velocity']:.2f} entries/day ({m['velocity_trend']} trend)\n"
        f"Peak hour: {m['peak_hour']:02d}:00\n" if m["peak_hour"] is not None else ""
        f"Busiest weekday: {m['busiest_weekday']}\n" if m["busiest_weekday"] else ""
        f"Average mood: {m['avg_mood']}/5\n" if m["avg_mood"] else ""
        f"Top tags: {', '.join(f\"{t}({n})\" for t, n in m['top_tags'])}\n"
        f"Tag mood correlation: {m['tag_moods']}\n" if m["tag_moods"] else ""
        f"Happiest tag: {m['best_mood_tag']}\n" if m["best_mood_tag"] else ""
        f"Hardest tag: {m['worst_mood_tag']}\n" if m["worst_mood_tag"] else ""
    )

    prompt = (
        f"Here are productivity metrics from my developer journal for the past {days} days:\n\n"
        f"{metric_text}\n"
        "Provide a concise developer-focused analysis (4-5 sentences):\n"
        "1. What do these patterns say about my work rhythm?\n"
        "2. Any correlation between mood and work type worth noting?\n"
        "3. One specific, actionable improvement suggestion.\n\n"
        "Be concrete and practical. Use markdown formatting."
    )

    client = anthropic.Anthropic(api_key=api_key)
    console.print(f"\n[bold cyan]AI Metrics Interpretation[/bold cyan]\n")
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def cmd_standout(args: argparse.Namespace) -> None:
    """Find your most significant entries via TF-IDF outlier scoring."""
    from datetime import date, timedelta
    from collections import Counter
    import math
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from .storage import load_entries

    days = args.days
    top_n = args.top
    today = date.today()
    cutoff = (today - timedelta(days=days)).isoformat()
    window = [e for e in load_entries() if e.get("date", "") >= cutoff]

    if not window:
        console.print(f"[dim]No entries in the last {days} days.[/dim]")
        return

    def _tokenize(text: str) -> list[str]:
        import re
        return re.findall(r"[a-z]+", text.lower())

    # Build corpus
    docs = [_tokenize(e["text"]) for e in window]
    n_docs = len(docs)

    # Term frequency per document
    tf_list = [Counter(doc) for doc in docs]

    # Inverse document frequency across corpus
    df: Counter = Counter()
    for doc in docs:
        for term in set(doc):
            df[term] += 1
    idf = {term: math.log((n_docs + 1) / (count + 1)) + 1 for term, count in df.items()}

    # TF-IDF score for each entry = sum of top-3 word scores
    scored = []
    for i, (entry, tf) in enumerate(zip(window, tf_list)):
        if not tf:
            scored.append((0.0, entry))
            continue
        word_scores = sorted(
            (tf[term] * idf.get(term, 0) for term in tf),
            reverse=True,
        )
        score = sum(word_scores[:3])
        scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_n]

    t = Table(
        box=rbox.ROUNDED, show_header=True, header_style="bold cyan",
        border_style="dim", expand=False,
    )
    t.add_column("Score", justify="right", style="cyan", width=7)
    t.add_column("Date", style="dim", width=12)
    t.add_column("Tag", style="yellow", width=10)
    t.add_column("Entry", style="white")

    for score, entry in top:
        t.add_row(
            f"{score:.2f}",
            entry["date"],
            entry.get("tag") or "",
            entry["text"],
        )

    console.print(Panel(
        t,
        title=f"Standout entries — last {days} days (TF-IDF outliers)",
        border_style="cyan",
        box=rbox.ROUNDED,
    ))
    console.print(
        f"\n  [dim]Scoring: entries with rare, repeated keywords score highest  "
        f"·  {len(window)} entries analysed[/dim]"
    )


def cmd_pin(args: argparse.Namespace) -> None:
    """Pin, unpin, and list pinned entries."""
    from .pins import pin_entry, unpin_entry, get_pinned_ids
    from rich.table import Table, box as rbox
    from rich.panel import Panel

    subcmd = getattr(args, "pin_cmd", None)

    if subcmd == "add":
        if pin_entry(args.id):
            console.print(f"[green]✓ Entry #{args.id} pinned.[/green]")
        else:
            console.print(f"[yellow]Entry #{args.id} is already pinned.[/yellow]")

    elif subcmd == "remove":
        if unpin_entry(args.id):
            console.print(f"[green]✓ Entry #{args.id} unpinned.[/green]")
        else:
            console.print(f"[red]Entry #{args.id} is not pinned.[/red]")

    else:  # list (default)
        ids = get_pinned_ids()
        if not ids:
            console.print("[dim]No pinned entries. Pin one with: devlog pin add ID[/dim]")
            return

        all_entries = load_entries()
        by_id = {e["id"]: e for e in all_entries}
        pinned = [by_id[i] for i in ids if i in by_id]

        if not pinned:
            console.print("[dim]No pinned entries found (they may have been deleted).[/dim]")
            return

        t = Table(box=rbox.ROUNDED, show_header=True, header_style="bold cyan", border_style="yellow")
        t.add_column("ID", style="dim", justify="right", no_wrap=True)
        t.add_column("Date", style="dim", no_wrap=True)
        t.add_column("Tag", style="yellow", no_wrap=True)
        t.add_column("Entry", style="white")
        for e in pinned:
            t.add_row(str(e["id"]), e["date"], e.get("tag") or "", e["text"])
        console.print(Panel(t, title=f"[bold yellow]Pinboard[/bold yellow] ({len(pinned)} entries)", border_style="yellow", box=rbox.ROUNDED))


def cmd_correlate(args: argparse.Namespace) -> None:
    """Show correlations between tags and mood scores."""
    from collections import defaultdict
    from rich.table import Table, box as rbox
    from rich.panel import Panel
    from rich.text import Text
    from datetime import date, timedelta

    days = getattr(args, "days", 90)
    today = date.today()
    cutoff = (today - timedelta(days=days)).isoformat()

    all_entries = load_entries()
    window = [e for e in all_entries if e.get("date", "") >= cutoff]

    if not window:
        console.print(f"[dim]No entries in the last {days} days.[/dim]")
        return

    # Gather per-tag mood stats
    tag_moods: dict[str, list[int]] = defaultdict(list)
    untagged_moods: list[int] = []
    total_with_mood = 0

    for e in window:
        mood = e.get("mood")
        if mood is not None:
            total_with_mood += 1
            tag = e.get("tag")
            if tag:
                tag_moods[tag].append(mood)
            else:
                untagged_moods.append(mood)

    if not tag_moods and not untagged_moods:
        console.print(
            f"[dim]No mood data in the last {days} days. "
            "Add moods with: devlog add -m 4 \"your entry\"[/dim]"
        )
        return

    overall_avg = (
        sum(m for moods in tag_moods.values() for m in moods) + sum(untagged_moods)
    ) / total_with_mood if total_with_mood else 0

    rows = []
    for tag, moods in tag_moods.items():
        avg = sum(moods) / len(moods)
        delta = avg - overall_avg
        rows.append((tag, avg, delta, len(moods)))

    # Sort by average mood descending
    rows.sort(key=lambda x: -x[1])

    t = Table(box=rbox.ROUNDED, show_header=True, header_style="bold cyan", border_style="dim")
    t.add_column("Tag", style="yellow")
    t.add_column("Entries", justify="right", style="dim", width=8)
    t.add_column("Avg mood", justify="right", width=9)
    t.add_column("vs. avg", justify="right", width=9)
    t.add_column("Distribution", width=20)

    MOOD_BLOCKS = {1: "[red]▓[/red]", 2: "[yellow]▓[/yellow]", 3: "[dim]▓[/dim]", 4: "[cyan]▓[/cyan]", 5: "[green]▓[/green]"}

    for tag, avg, delta, count in rows:
        delta_str = f"[green]+{delta:.1f}[/green]" if delta > 0.1 else (
            f"[red]{delta:.1f}[/red]" if delta < -0.1 else f"[dim]{delta:.1f}[/dim]"
        )
        lvl = max(1, min(5, round(avg)))
        bar = MOOD_BLOCKS[lvl] * max(1, round(avg * 3))
        t.add_row(tag, str(count), f"{avg:.1f}", delta_str, bar)

    if untagged_moods:
        avg = sum(untagged_moods) / len(untagged_moods)
        delta = avg - overall_avg
        delta_str = f"[green]+{delta:.1f}[/green]" if delta > 0.1 else (
            f"[red]{delta:.1f}[/red]" if delta < -0.1 else f"[dim]{delta:.1f}[/dim]"
        )
        lvl = max(1, min(5, round(avg)))
        bar = MOOD_BLOCKS[lvl] * max(1, round(avg * 3))
        t.add_row("[dim](untagged)[/dim]", str(len(untagged_moods)), f"{avg:.1f}", delta_str, bar)

    console.print(Panel(
        t,
        title=f"[bold]Mood × Tag Correlation[/bold] — last {days} days",
        border_style="cyan",
        box=rbox.ROUNDED,
    ))

    if rows:
        best_tag, best_avg, *_ = rows[0]
        worst_tag, worst_avg, *_ = rows[-1]
        console.print(
            f"\n  [bold cyan]Overall avg mood:[/bold cyan] {overall_avg:.1f}/5  "
            f"[dim]·[/dim]  [dim]{total_with_mood} entries with mood data[/dim]"
        )
        if len(rows) > 1:
            console.print(
                f"  [bold green]Happiest tag:[/bold green] [yellow]{best_tag}[/yellow] [dim](avg {best_avg:.1f}/5)[/dim]  "
                f"[dim]·[/dim]  "
                f"[bold red]Hardest tag:[/bold red] [yellow]{worst_tag}[/yellow] [dim](avg {worst_avg:.1f}/5)[/dim]"
            )


def cmd_ai_plan(args: argparse.Namespace) -> None:
    """Stream an AI-generated daily plan for tomorrow based on recent context."""
    from datetime import date, timedelta

    try:
        import anthropic
    except ImportError:
        console.print("[red]Install anthropic: pip install anthropic[/red]")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Set ANTHROPIC_API_KEY first.[/red]")
        return

    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Gather recent context: today's entries + open goals
    today_entries = get_entries(day=today.isoformat())
    yesterday_entries = get_entries(day=(today - timedelta(days=1)).isoformat())

    try:
        from .goals import list_goals
        iso = today.isocalendar()
        week_label = f"{iso[0]}-W{iso[1]:02d}"
        open_goals = [g for g in list_goals(week=week_label) if not g["done"]]
    except Exception:
        open_goals = []

    if not today_entries and not yesterday_entries:
        console.print("[yellow]No recent journal entries to base a plan on.[/yellow]")
        console.print("[dim]Add some with: devlog add \"what you worked on today\"[/dim]")
        return

    def _fmt(entries: list[dict]) -> str:
        return "\n".join(
            f"- [{e['time']}]{' [' + e['tag'] + ']' if e.get('tag') else ''} {e['text']}"
            for e in entries
        ) or "(none)"

    goals_text = "\n".join(f"- #{g['id']}: {g['text']}" for g in open_goals) or "(none)"

    prompt = (
        f"You are a thoughtful engineering coach.\n\n"
        f"Today's journal ({today.isoformat()}):\n{_fmt(today_entries)}\n\n"
        f"Yesterday's journal ({(today - timedelta(days=1)).isoformat()}):\n{_fmt(yesterday_entries)}\n\n"
        f"Open goals for this week:\n{goals_text}\n\n"
        f"Generate a concise, actionable daily plan for tomorrow ({tomorrow.isoformat()}).\n"
        "Structure it as:\n"
        "## Morning (high-focus)\n"
        "## Afternoon (lower-focus)\n"
        "## Don't forget\n\n"
        "3-5 bullets per section maximum. Be specific — reference actual tasks from the journal. "
        "Prioritise unfinished work and open goals. Use markdown."
    )

    client = anthropic.Anthropic(api_key=api_key)
    console.print(f"\n[bold cyan]Daily Plan for {tomorrow.isoformat()}[/bold cyan]\n")
    console.print(f"[dim]Based on {len(today_entries)} today + {len(yesterday_entries)} yesterday entries, {len(open_goals)} open goal(s)[/dim]\n")

    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")
