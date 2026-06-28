"""`daysheet tomorrow` — print tomorrow's daysheet, creating if folder empty."""

import sys
import datetime

from daysheet_lib.config import TOMORROW_DIR
from daysheet_lib.core import (
    date_to_filename,
    list_dir_entries,
    parse_daysheet_filename,
    today_date,
    write_daysheet,
)


def run(wd):
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
