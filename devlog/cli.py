import argparse
import os
import sys
from datetime import date, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box

from .storage import add_entry, get_entries, delete_entry, search_entries

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


def cmd_add(args):
    text = " ".join(args.text)
    entry = add_entry(text, tag=args.tag)
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
    md = export_markdown(entries)
    if args.output:
        with open(args.output, "w") as f:
            f.write(md)
        console.print(f"[green]✓ Exported to {args.output}[/green]")
    else:
        print(md)


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

    p_export = sub.add_parser("export", help="Export entries as Markdown")
    p_export.add_argument("date", nargs="?", help="Date to export (omit for all)")
    p_export.add_argument("-o", "--output", help="Output file path")
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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)
