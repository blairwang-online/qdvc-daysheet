"""`daysheet status` — report on the today / tomorrow / archive folders."""

import datetime

from python_modules.config import ARCHIVE_DIR, TODAY_DIR, TOMORROW_DIR
from python_modules.core import (
    classify_today_folder,
    date_to_filename,
    list_dir_entries,
    parse_daysheet_filename,
    read_frontmatter_flag,
    today_date,
)


def run(wd):
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
