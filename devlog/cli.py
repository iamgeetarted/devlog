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


def cmd_add(args):
    text = " ".join(args.text)
    tag = args.tag or _cfg.get("default_tag")
    entry = add_entry(text, tag=tag)
    tag_str = f"[yellow]\\[{entry['tag']}][/yellow] " if entry.get("tag") else ""
    console.print(
        f"[green]✓[/green] Logged: {tag_str}{entry['text']} "
        f"[dim]({entry['date']} {entry['time']})[/dim]"
    )


def cmd_today(args):
    today = date.today().isoformat()
    entries = get_entries(day=today)
    print_entries(entries, title=f"Today — {today}")


def cmd_yesterday(args):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    entries = get_entries(day=yesterday)
    print_entries(entries, title=f"Yesterday — {yesterday}")


def cmd_log(args):
    entries = get_entries(day=args.date)
    print_entries(entries, title=args.date if args.date else None)


def cmd_export(args):
    entries = get_entries(day=args.date)
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
    # Sentinel: if -t not provided args.tag will be ... (we pass it through)
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

    # Entries-per-day bar chart (only show days with entries unless --all)
    BAR_WIDTH = 24
    max_count = max(by_date.values(), default=1) or 1

    day_table = Table(box=rbox.SIMPLE, show_header=True, header_style="bold cyan", pad_edge=False)
    day_table.add_column("Date", style="dim", no_wrap=True)
    day_table.add_column("n", justify="right", style="white", width=3)
    day_table.add_column("", style="cyan")

    shown = 0
    for d, count in by_date.items():
        if count == 0 and not args.all_days:
            continue
        bar = "█" * max(1, round(count / max_count * BAR_WIDTH)) if count else ""
        day_table.add_row(d, str(count) if count else "·", bar)
        shown += 1

    # Tag breakdown
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


def main():
    parser = argparse.ArgumentParser(
        prog="devlog",
        description="Minimal developer daily journal",
    )
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Add a log entry")
    p_add.add_argument("text", nargs="+", help="Entry text")
    p_add.add_argument("-t", "--tag", help="Tag (e.g. bug, feat, chore)")
    p_add.set_defaults(func=cmd_add)

    p_today = sub.add_parser("today", help="Show today's entries")
    p_today.set_defaults(func=cmd_today)

    p_yesterday = sub.add_parser("yesterday", help="Show yesterday's entries")
    p_yesterday.set_defaults(func=cmd_yesterday)

    p_log = sub.add_parser("log", help="Show all entries or a specific date")
    p_log.add_argument("date", nargs="?", help="Date (YYYY-MM-DD)")
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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)
