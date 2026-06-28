"""Filename/frontmatter helpers and daysheet assembly."""

import os
import datetime
from pathlib import Path

from python_modules.config import (
    ARCHIVE_DIR,
    COMPONENTS_SUBDIR,
    DAYSHEET_RE,
    TEMPLATE_DIR,
    TODAY_DIR,
    fail,
)


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
