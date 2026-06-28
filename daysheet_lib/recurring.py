"""Generate the recurring-tasks (and checklists) sections of a daysheet.

Recurring tasks are defined in `04-templates/recurring-tasks.crontab`, written
in crontab style:

    0 0 * * *    Email clearing process
    0 0 * * 6    Saturday Special Budget Sync #budget-sync
    0 0 1 */2 *  #check-tyre-pressure

The first two fields (minute, hour) are irrelevant for a per-day system and
are ignored. The remaining three fields (day-of-month, month, day-of-week)
are matched against the daysheet's date using standard cron semantics.

A task's description may end with a `#hashtag` referring to a checklist file
at `04-templates/checklists/<hashtag>.md`. When such a task fires on a given
day, that checklist's contents are appended in a "Checklists mentioned"
section.
"""

import sys

from daysheet_lib.config import (
    CHECKLISTS_SUBDIR,
    RECURRING_TASKS_FILE,
    TEMPLATE_DIR,
    fail,
)

AUTO_NOTE = "_This section has been automatically populated._"


# --------------------------------------------------------------------------- #
# Cron field matching
# --------------------------------------------------------------------------- #

def _parse_field(field, lo, hi):
    """Expand a single cron field into a set of matching integers in [lo, hi].

    Supports: '*', single values, comma lists, ranges (a-b), and step values
    on either a range or a star (a-b/n, */n). Returns a set of ints, or raises
    ValueError on malformed input.
    """
    values = set()
    for part in field.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty term in field {field!r}")

        step = 1
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            if step <= 0:
                raise ValueError(f"invalid step in {part!r}")
        else:
            base = part

        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            start_str, end_str = base.split("-", 1)
            start, end = int(start_str), int(end_str)
        else:
            start = end = int(base)

        if start < lo or end > hi or start > end:
            raise ValueError(f"value out of range in {part!r} (allowed {lo}-{hi})")

        values.update(range(start, end + 1, step))
    return values


def _matches(dom_field, month_field, dow_field, d):
    """Return True if date `d` matches the three cron fields.

    Day-of-week is 0-6 with both 0 and 7 meaning Sunday (cron convention).
    Standard cron DOM/DOW rule: if BOTH day-of-month and day-of-week are
    restricted (neither is '*'), the date matches if EITHER matches; otherwise
    both must match.
    """
    dom = _parse_field(dom_field, 1, 31)
    month = _parse_field(month_field, 1, 12)

    # Normalise day-of-week so 7 collapses onto 0 (Sunday).
    dow_raw = _parse_field(dow_field, 0, 7)
    dow = {0 if v == 7 else v for v in dow_raw}

    if d.month not in month:
        return False

    # Python weekday(): Monday=0..Sunday=6 → cron: Sunday=0..Saturday=6.
    cron_dow = (d.weekday() + 1) % 7

    dom_restricted = dom_field.strip() != "*"
    dow_restricted = dow_field.strip() != "*"

    dom_hit = d.day in dom
    dow_hit = cron_dow in dow

    if dom_restricted and dow_restricted:
        return dom_hit or dow_hit
    return dom_hit and dow_hit


# --------------------------------------------------------------------------- #
# Crontab parsing
# --------------------------------------------------------------------------- #

def _split_tag(description):
    """Split a trailing '#hashtag' off a task description.

    Returns (description, tag_or_None). The description is returned exactly as
    written (the hashtag is NOT stripped from it); the tag is the bare word
    after '#', used to locate a checklist file.
    """
    tag = None
    for token in description.split():
        if token.startswith("#") and len(token) > 1:
            tag = token[1:]
    return description, tag


def parse_crontab(text):
    """Parse crontab text into a list of (dom, month, dow, description, tag).

    Blank lines and lines beginning with '#' (comments) are skipped. Each
    remaining line must have at least 5 whitespace-separated fields; fields 1-2
    (minute, hour) are ignored, fields 3-5 are the schedule, and the remainder
    of the line is the task description.
    """
    entries = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split(None, 5)
        if len(fields) < 6:
            fail(
                f"{RECURRING_TASKS_FILE}: line {lineno} has too few fields "
                f"(need 5 cron fields + a description): {raw!r}"
            )
        _minute, _hour, dom, month, dow, description = fields
        description, tag = _split_tag(description.strip())
        entries.append((dom, month, dow, description, tag))
    return entries


# --------------------------------------------------------------------------- #
# Section rendering
# --------------------------------------------------------------------------- #

def _read_crontab(wd):
    path = wd / TEMPLATE_DIR / RECURRING_TASKS_FILE
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _checklist_text(wd, tag):
    """Return the checklist body for `tag`, or None if the file is missing."""
    path = wd / TEMPLATE_DIR / CHECKLISTS_SUBDIR / f"{tag}.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").rstrip("\n")


def build_recurring_sections(wd, d):
    """Build the recurring-tasks and checklists markdown for date `d`.

    Returns a (possibly empty) list of section strings, each a self-contained
    markdown block. The first is the "Recurring tasks" section (when any task
    fires); the second, if present, is "Checklists mentioned".
    """
    text = _read_crontab(wd)
    if text is None:
        return []

    entries = parse_crontab(text)

    # Determine which tasks fire today, preserving file order.
    fired = []  # list of (description, tag)
    for dom, month, dow, description, tag in entries:
        try:
            hit = _matches(dom, month, dow, d)
        except ValueError as exc:
            fail(f"{RECURRING_TASKS_FILE}: {exc}")
        if hit:
            fired.append((description, tag))

    if not fired:
        return []

    # --- Recurring tasks section --- #
    lines = ["## Recurring tasks", "", AUTO_NOTE, ""]
    for description, _tag in fired:
        lines.append(f"- [ ] {description}")
    recurring_section = "\n".join(lines)
    sections = [recurring_section]

    # --- Checklists mentioned section --- #
    # Collect tags that fired today, in first-seen order, de-duplicated.
    seen = set()
    tags_today = []
    for _description, tag in fired:
        if tag and tag not in seen:
            seen.add(tag)
            tags_today.append(tag)

    checklist_blocks = []
    for tag in tags_today:
        body = _checklist_text(wd, tag)
        if body is None:
            print(
                f"daysheet: warning: checklist '#{tag}' has no file at "
                f"{TEMPLATE_DIR}/{CHECKLISTS_SUBDIR}/{tag}.md; skipping it.",
                file=sys.stderr,
            )
            continue
        checklist_blocks.append(f"### {tag}\n\n{body}")

    if checklist_blocks:
        header = ["## Checklists mentioned", "", AUTO_NOTE, "", ""]
        sections.append("\n".join(header) + "\n\n".join(checklist_blocks))

    return sections
