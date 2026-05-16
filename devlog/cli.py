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

    client = anthropic.Anthropic(api_key=api_key)
    console.print(f"\n[bold cyan]Summary for {day}[/bold cyan]\n")
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print()


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

    p_tags = sub.add_parser("tags", help="List entry tags with counts or rename a tag")
    tags_sub = p_tags.add_subparsers(dest="tags_cmd")
    tags_sub.add_parser("list", help="List all tags with entry counts")
    pt_rename = tags_sub.add_parser("rename", help="Rename a tag across all entries")
    pt_rename.add_argument("old_tag", help="Existing tag name")
    pt_rename.add_argument("new_tag", help="New tag name")
    p_tags.set_defaults(func=cmd_tags)

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
