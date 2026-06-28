"""Filename/frontmatter helpers and daysheet assembly."""

import os
import re
import datetime
from pathlib import Path

from daysheet_lib.config import (
    ARCHIVE_DIR,
    COMPONENTS_SUBDIR,
    DAYSHEET_RE,
    RECURRING_INSERT_MAX_PREFIX,
    TEMPLATE_DIR,
    TODAY_DIR,
    fail,
)
from daysheet_lib.recurring import build_recurring_sections

# Leading numeric prefix on a component filename, e.g. "010-foo.md" -> 10.
_PREFIX_RE = re.compile(r"^(\d+)")


def _component_prefix(path):
    """Return the integer prefix of a component filename, or None if absent."""
    m = _PREFIX_RE.match(path.name)
    return int(m.group(1)) if m else None


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

    # Build the programmatically-generated recurring/checklist sections. They
    # are inserted immediately after the last component whose numeric prefix is
    # <= RECURRING_INSERT_MAX_PREFIX (e.g. after 009-, before 010-).
    recurring_sections = build_recurring_sections(wd, d)
    recurring_inserted = not recurring_sections  # nothing to insert => "done"

    for comp in component_files:
        prefix = _component_prefix(comp)
        # Once we reach a component past the threshold, flush the generated
        # sections first (so they sit between the <=009 and >=010 components).
        if (not recurring_inserted
                and prefix is not None
                and prefix > RECURRING_INSERT_MAX_PREFIX):
            for section in recurring_sections:
                parts.append(section)
                parts.append("")
            recurring_inserted = True

        text = comp.read_text(encoding="utf-8").rstrip("\n")
        parts.append(text)
        parts.append("")  # blank line between components

    # If every component had a small prefix (or none crossed the threshold),
    # append the generated sections at the end.
    if not recurring_inserted:
        for section in recurring_sections:
            parts.append(section)
            parts.append("")

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
