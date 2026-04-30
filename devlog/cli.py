import argparse
import sys
from datetime import date, timedelta

from .storage import add_entry, get_entries, delete_entry


COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "red": "\033[91m",
    "dim": "\033[2m",
}


def c(color, text):
    return f"{COLORS[color]}{text}{COLORS['reset']}"


def fmt_tag(tag):
    if not tag:
        return ""
    return c("yellow", f"[{tag}]") + " "


def print_entries(entries, title=None):
    if title:
        print(c("bold", f"\n{title}"))
        print(c("dim", "─" * 40))

    if not entries:
        print(c("dim", "  No entries found."))
        return

    current_date = None
    for e in entries:
        if e["date"] != current_date:
            current_date = e["date"]
            if not title:
                print(c("bold", f"\n{current_date}"))
                print(c("dim", "─" * 40))
        tag_str = fmt_tag(e.get("tag"))
        print(f"  {c('dim', str(e['id'])+'.')} {c('dim', e['time'])}  {tag_str}{e['text']}")


def export_markdown(entries):
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
    print(c("green", "✓") + f" Logged: {fmt_tag(entry.get('tag'))}{entry['text']} {c('dim', '(' + entry['date'] + ' ' + entry['time'] + ')')}")


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
        print(c("green", f"✓ Exported to {args.output}"))
    else:
        print(md)


def cmd_delete(args):
    if delete_entry(args.id):
        print(c("green", f"✓ Deleted entry {args.id}"))
    else:
        print(c("red", f"✗ Entry {args.id} not found"))


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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)
