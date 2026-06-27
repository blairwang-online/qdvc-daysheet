#!/usr/bin/env python3
"""daysheet.py — manage markdown "daysheets" for daily planning.

A daysheet is a markdown summary of a day, used for planning. This tool
creates them from templates, prints them, archives old ones, and reports
on the state of your daysheet folders.

See README.md for an overview and MAINTENANCE.md for internals.
"""

import os
import re
import sys
import shutil
import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.yml"

TODAY_DIR = "01-today"
TOMORROW_DIR = "02-tomorrow"
ARCHIVE_DIR = "03-archive"
TEMPLATE_DIR = "04-templates"
COMPONENTS_SUBDIR = "components"

# A valid daysheet filename is exactly an ISO date, e.g. 2026-06-28.md
DAYSHEET_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.md$")


def load_config():
    """Load config.yml and return the resolved working directory Path.

    We avoid a hard PyYAML dependency for this single string key by doing a
    tiny line-based parse, but use PyYAML if it is available (more robust).
    """
    if not CONFIG_PATH.exists():
        fail(
            f"Config file not found: {CONFIG_PATH}\n"
            "Create a config.yml next to daysheet.py with:\n"
            '  working_directory: "/path/to/your/daysheet/data"'
        )

    working_directory = None
    try:
        import yaml  # type: ignore

        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        working_directory = data.get("working_directory")
    except ImportError:
        # Minimal fallback parser: find `working_directory: <value>`.
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("working_directory:"):
                    working_directory = line.split(":", 1)[1].strip()
                    working_directory = working_directory.strip("'\"")
                    break

    if not working_directory:
        fail("config.yml does not define a 'working_directory'.")

    wd = Path(os.path.expanduser(working_directory)).resolve()
    if not wd.is_dir():
        fail(f"Working directory does not exist: {wd}")
    return wd


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def fail(message, code=1):
    """Print an error to stderr and exit."""
    print(f"daysheet: {message}", file=sys.stderr)
    sys.exit(code)


def today_date():
    return datetime.date.today()


def date_to_filename(d):
    return f"{d.isoformat()}.md"


def parse_daysheet_filename(name):
    """Return a datetime.date if `name` is a valid daysheet filename, else None."""
    m = DAYSHEET_RE.match(name)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def list_dir_entries(path):
    """Return a sorted list of entry names in `path` (files and dirs), or []."""
    if not path.is_dir():
        return []
    return sorted(os.listdir(path))


def read_frontmatter_flag(file_path, key):
    """Read a simple top-of-file YAML frontmatter boolean flag.

    Returns True / False / None (None if the key is absent or unparseable).
    Only the leading `---` ... `---` block is inspected.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None

    if not lines or lines[0].strip() != "---":
        return None

    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            if k.strip() == key:
                val = v.strip().lower()
                if val in ("true", "yes", "1"):
                    return True
                if val in ("false", "no", "0"):
                    return False
                return None
    return None


# --------------------------------------------------------------------------- #
# Daysheet assembly
# --------------------------------------------------------------------------- #

def build_daysheet_text(wd, d):
    """Assemble the markdown text for daysheet of date `d`."""
    components_dir = wd / TEMPLATE_DIR / COMPONENTS_SUBDIR
    if not components_dir.is_dir():
        fail(f"Template components directory not found: {components_dir}")

    # Heading, e.g. "# 2026-06-28: Daysheet for Sunday, 28 June 2026"
    pretty = d.strftime("%A, %-d %B %Y")
    heading = f"# {d.isoformat()}: Daysheet for {pretty}"

    parts = ["---", "ready_to_archive: False", "---", "", heading, ""]

    component_files = sorted(
        p for p in components_dir.iterdir()
        if p.is_file() and p.suffix == ".md"
    )
    if not component_files:
        fail(f"No template components (*.md) found in {components_dir}")

    for comp in component_files:
        text = comp.read_text(encoding="utf-8").rstrip("\n")
        parts.append(text)
        parts.append("")  # blank line between components

    return "\n".join(parts).rstrip("\n") + "\n"


def write_daysheet(wd, folder, d):
    """Create the daysheet for date `d` inside `folder`. Returns the path."""
    dest = wd / folder / date_to_filename(d)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(build_daysheet_text(wd, d), encoding="utf-8")
    return dest


def archive_destination(wd, d):
    """Return the archive path (03-archive/YYYY/MM/YYYY-MM-DD.md) for date d."""
    return wd / ARCHIVE_DIR / f"{d.year:04d}" / f"{d.month:02d}" / date_to_filename(d)


# --------------------------------------------------------------------------- #
# Folder inspection
# --------------------------------------------------------------------------- #

def classify_today_folder(wd):
    """Classify the contents of 01-today.

    Returns a dict:
        {
          "daysheets":  [(date, name), ...],   # valid daysheet files
          "other":      [name, ...],           # everything else
        }
    """
    folder = wd / TODAY_DIR
    daysheets, other = [], []
    for name in list_dir_entries(folder):
        d = parse_daysheet_filename(name)
        if d and (folder / name).is_file():
            daysheets.append((d, name))
        else:
            other.append(name)
    daysheets.sort()
    return {"daysheets": daysheets, "other": other}


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def cmd_today(wd):
    today = today_date()
    today_file = wd / TODAY_DIR / date_to_filename(today)

    if today_file.is_file():
        sys.stdout.write(today_file.read_text(encoding="utf-8"))
        return

    # Today's daysheet is missing — try to tidy up older ones.
    info = classify_today_folder(wd)

    # Archive any older daysheets that are ready_to_archive.
    for d, name in list(info["daysheets"]):
        if d >= today:
            continue
        src = wd / TODAY_DIR / name
        if read_frontmatter_flag(src, "ready_to_archive") is True:
            dest = archive_destination(wd, d)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            print(f"Archived {name} -> {dest.relative_to(wd)}", file=sys.stderr)

    # Re-inspect after archiving.
    info = classify_today_folder(wd)
    remaining = info["daysheets"] + [(None, n) for n in info["other"]]

    if not remaining:
        # 01-today is empty: create today's daysheet and print it.
        path = write_daysheet(wd, TODAY_DIR, today)
        print(f"Created {path.relative_to(wd)}", file=sys.stderr)
        sys.stdout.write(path.read_text(encoding="utf-8"))
        return

    # Still not empty: report what remains and do NOT create today's daysheet.
    print(
        f"Cannot create today's daysheet: {TODAY_DIR} still contains items.\n"
        "Please review and clear them, then run `daysheet today` again.\n",
        file=sys.stderr,
    )
    for d, name in info["daysheets"]:
        flag = read_frontmatter_flag(wd / TODAY_DIR / name, "ready_to_archive")
        if flag is True:
            note = "older daysheet, ready to archive (archive failed?)"
        elif flag is False:
            note = "older daysheet, NOT ready to archive"
        else:
            note = "older daysheet, ready_to_archive flag missing/unparseable"
        print(f"  - {name}: {note}", file=sys.stderr)
    for name in info["other"]:
        print(f"  - {name}: other material (not a daysheet)", file=sys.stderr)
    sys.exit(1)


def cmd_tomorrow(wd):
    tomorrow = today_date() + datetime.timedelta(days=1)
    tomorrow_file = wd / TOMORROW_DIR / date_to_filename(tomorrow)

    if tomorrow_file.is_file():
        sys.stdout.write(tomorrow_file.read_text(encoding="utf-8"))
        return

    entries = list_dir_entries(wd / TOMORROW_DIR)
    if not entries:
        path = write_daysheet(wd, TOMORROW_DIR, tomorrow)
        print(f"Created {path.relative_to(wd)}", file=sys.stderr)
        sys.stdout.write(path.read_text(encoding="utf-8"))
        return

    # Not empty: report contents, do not create.
    print(
        f"Cannot create tomorrow's daysheet: {TOMORROW_DIR} is not empty.\n"
        "Please review and clear it, then run `daysheet tomorrow` again.\n"
        f"Contents of {TOMORROW_DIR}:",
        file=sys.stderr,
    )
    for name in entries:
        d = parse_daysheet_filename(name)
        kind = "daysheet file" if d else "other material"
        print(f"  - {name}: {kind}", file=sys.stderr)
    sys.exit(1)


def cmd_status(wd):
    today = today_date()
    tomorrow = today + datetime.timedelta(days=1)

    print("daysheet status")
    print("=" * 40)

    # --- 01-today ---------------------------------------------------------- #
    info = classify_today_folder(wd)
    print(f"\n[{TODAY_DIR}]")
    if not info["daysheets"] and not info["other"]:
        print("  empty")
    else:
        has_today = any(d == today for d, _ in info["daysheets"])
        if has_today:
            tf = wd / TODAY_DIR / date_to_filename(today)
            flag = read_frontmatter_flag(tf, "ready_to_archive")
            ready = {True: "yes", False: "no"}.get(flag, "unknown")
            print(f"  today's daysheet present ({date_to_filename(today)}); "
                  f"ready_to_archive: {ready}")
            print(f"    path: {tf}")
        else:
            print("  today's daysheet NOT present")
        for d, name in info["daysheets"]:
            if d != today:
                print(f"  other daysheet present: {name} (dated {d.isoformat()})")
        for name in info["other"]:
            print(f"  other material: {name}")

    # --- 02-tomorrow ------------------------------------------------------- #
    print(f"\n[{TOMORROW_DIR}]")
    tomorrow_entries = list_dir_entries(wd / TOMORROW_DIR)
    if not tomorrow_entries:
        print("  empty")
    else:
        has_tomorrow = (wd / TOMORROW_DIR / date_to_filename(tomorrow)).is_file()
        if has_tomorrow:
            tf = wd / TOMORROW_DIR / date_to_filename(tomorrow)
            print(f"  tomorrow's daysheet present ({date_to_filename(tomorrow)})")
            print(f"    path: {tf}")
        for name in tomorrow_entries:
            d = parse_daysheet_filename(name)
            if d == tomorrow:
                continue
            kind = f"daysheet file (dated {d.isoformat()})" if d else "other material"
            print(f"  {kind}: {name}")

    # --- 03-archive -------------------------------------------------------- #
    print(f"\n[{ARCHIVE_DIR}]")
    valid_dates = []
    invalid = []
    archive_root = wd / ARCHIVE_DIR
    if archive_root.is_dir():
        for path in archive_root.rglob("*"):
            if path.is_file():
                d = parse_daysheet_filename(path.name)
                if d:
                    valid_dates.append(d)
                else:
                    invalid.append(str(path.relative_to(wd)))

    if not valid_dates:
        print("  no valid daysheet files")
    else:
        valid_dates.sort()
        first, last = valid_dates[0], valid_dates[-1]
        span_days = (last - first).days + 1
        count = len(valid_dates)
        print(f"  valid daysheet files: {count}")
        print(f"  date range: {first.isoformat()} .. {last.isoformat()} "
              f"({span_days} calendar day(s))")
        if span_days != count:
            missing = span_days - count
            if missing > 0:
                print(f"  note: {missing} day(s) within range appear to be missing")
            else:
                print(f"  note: {-missing} more file(s) than days in range "
                      "(duplicates across folders?)")

    print(f"  invalid / other files: {len(invalid)}")
    for name in invalid:
        print(f"    - {name}")


def cmd_help(wd=None):
    print(HELP_TEXT.strip())


HELP_TEXT = """
daysheet — manage your markdown daysheets

USAGE
  daysheet today       Print today's daysheet. If missing, archive any
                       older daysheets flagged ready_to_archive, then
                       create today's (only if 01-today ends up empty).
  daysheet tomorrow    Print tomorrow's daysheet. If missing and
                       02-tomorrow is empty, create it.
  daysheet status      Report on 01-today, 02-tomorrow, and 03-archive.
  daysheet help        Show this help.

Daysheets are created from the components in
04-templates/components/ (sorted by filename), with an auto-generated
date heading and YAML frontmatter (ready_to_archive: False).

Pipe to a renderer if you like:
  daysheet today | glow -

Configuration lives in config.yml next to daysheet.py.
"""


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

COMMANDS = {
    "today": cmd_today,
    "tomorrow": cmd_tomorrow,
    "status": cmd_status,
    "help": cmd_help,
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        cmd_help()
        return
    cmd = argv[0]
    handler = COMMANDS.get(cmd)
    if handler is None:
        fail(f"unknown command '{cmd}'. Try `daysheet help`.")
    if cmd == "help":
        cmd_help()
        return
    wd = load_config()
    handler(wd)


if __name__ == "__main__":
    main()
