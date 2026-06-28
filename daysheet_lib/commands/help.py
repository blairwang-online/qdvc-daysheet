"""`daysheet help` — brief help page."""

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
date heading and YAML frontmatter (ready_to_archive: False). Recurring
tasks due today (from 04-templates/recurring-tasks.crontab) and any
checklists they reference are inserted automatically.

Pipe to a renderer if you like:
  daysheet today | glow -

Configuration lives in config.yml next to daysheet.py
(copy config-example.yml to get started).
"""


def run(wd=None):
    print(HELP_TEXT.strip())
