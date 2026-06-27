# MAINTENANCE.md

Technical notes for anyone (human or AI) maintaining `daysheet.py`.

## Overview

Single-file CLI (`daysheet.py`), no third-party dependency required. PyYAML is
used opportunistically for `config.yml`; if it is absent a minimal line parser
reads the one key we need (`working_directory`).

## Layout of the working directory

Configured via `working_directory` in `config.yml` (sibling of `daysheet.py`):

```
01-today/                 # exactly one daysheet expected: <today>.md
02-tomorrow/              # staging for <tomorrow>.md
03-archive/YYYY/MM/       # filed past daysheets
04-templates/components/  # *.md fragments, concatenated in filename order
```

Constants for these names live at the top of `daysheet.py`
(`TODAY_DIR`, `TOMORROW_DIR`, `ARCHIVE_DIR`, `TEMPLATE_DIR`,
`COMPONENTS_SUBDIR`). Change them there if folder names ever change.

## Core conventions

- **Valid daysheet filename**: matches `DAYSHEET_RE` = `^\d{4}-\d{2}-\d{2}\.md$`
  AND parses as a real calendar date. `parse_daysheet_filename()` returns a
  `datetime.date` or `None`. Anything that fails is treated as "other material".
- **Frontmatter**: a leading `---` ... `---` block. `read_frontmatter_flag()`
  reads a single boolean key (currently only `ready_to_archive`). It returns
  `True` / `False` / `None`, where `None` means absent or unparseable. Treat
  `None` conservatively (do NOT archive on `None`).
- **Assembly** (`build_daysheet_text`): frontmatter → date heading
  (`# YYYY-MM-DD: Daysheet for <weekday, D Month YYYY>`) → each component file
  in sorted order, separated by blank lines. The heading uses `%-d` (no leading
  zero on the day); on platforms lacking `%-d` you would switch to `%d` or a
  manual format.
- **Output discipline**: the *content* of a daysheet goes to **stdout** (so it
  pipes into `glow` etc.); all status/diagnostic/"Created"/"Archived" messages
  go to **stderr**. Preserve this split — it is what makes piping clean.

## Command behaviour (the parts most likely to be edited)

`cmd_today`:
1. If `<today>.md` exists in `01-today`, print and stop.
2. Else, for each *older* daysheet flagged `ready_to_archive: True`, move it to
   `03-archive/YYYY/MM/`.
3. Re-scan. If `01-today` is empty → create + print today's. If not → list
   remaining items (classified) on stderr and exit 1 without creating.

`cmd_tomorrow`:
1. If `<tomorrow>.md` exists in `02-tomorrow`, print and stop.
2. Else if folder empty → create + print. Else report contents, exit 1.

`cmd_status` reports on all three folders. The archive section compares the
inclusive day-span of the date range against the file count and notes any
apparent missing days (or surplus files).

## Edge cases handled

- Empty / missing folders (`list_dir_entries` tolerates a missing dir).
- Missing `ready_to_archive` flag → not archived.
- Archive count vs. range mismatch reported both ways (missing or surplus).
- Non-daysheet files anywhere are surfaced, never silently moved or deleted.

## Things to be careful about

- The tool **never deletes** user files; it only *moves* daysheets into the
  archive and *creates* new ones. Keep it that way.
- `today`/`tomorrow` must remain idempotent when the target file already
  exists (print as-is, no mutation).
- Archiving only ever targets daysheets strictly *older* than today; never
  archive today's or future-dated sheets.
- If you add template components, they are picked up automatically (any `*.md`
  in `components/`), ordered by filename — hence the numeric prefixes.

## Testing

There is no test suite committed. To exercise it manually, point
`working_directory` at a throwaway folder, seed `04-templates/components/`,
and run the commands. Verify: creation, re-print, archiving of a flagged older
sheet, blocked creation when stray material is present, and the status math.
