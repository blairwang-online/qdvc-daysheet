"""`daysheet today` — print today's daysheet, creating/archiving as needed."""

import sys
import shutil

from daysheet_lib.config import TODAY_DIR
from daysheet_lib.core import (
    archive_destination,
    classify_today_folder,
    date_to_filename,
    read_frontmatter_flag,
    today_date,
    write_daysheet,
)


def run(wd):
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
