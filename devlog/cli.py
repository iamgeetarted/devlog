import argparse
import os
import sys
from datetime import date, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box

from .storage import add_entry, get_entries, delete_entry, search_entries, edit_entry, get_stats

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


def _print_formatted(entries: list[dict], fmt: str) -> None:
    if fmt == "json":
        print(export_json(entries))
    elif fmt == "markdown":
        print(export_markdown(entries))
    elif fmt == "csv":
        print(export_csv(entries))


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
    entry = add_entry(text, tag=tag)
    tag_str = f"[yellow]\\[{entry['tag']}][/yellow] " if entry.get("tag") else ""
    console.print(
        f"[green]✓[/green] Logged: {tag_str}{entry['text']} "
        f"[dim]({entry['date']} {entry['time']})[/dim]"
    )


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
    p_add.add_argument("-T", "--template", metavar="NAME",
                       help="Expand a named template prefix from ~/.devlog.toml [templates]")
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

    p_export = sub.add_parser("export", help="Export entries as Markdown, JSON, or CSV")
    p_export.add_argument("date", nargs="?", help="Date to export (omit for all)")
    p_export.add_argument("-o", "--output", help="Output file path")
    p_export.add_argument(
        "-f", "--format",
        choices=["markdown", "json", "csv"],
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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)
