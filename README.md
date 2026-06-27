# qdvc-daysheet

A small command-line tool for managing **daysheets** — markdown summaries of
the day ahead, used for planning. Each daysheet is a plain `.md` file built
from reusable template components, with a date heading and YAML frontmatter.

```markdown
---
ready_to_archive: False
---
# 2026-06-28: Daysheet for Sunday, 28 June 2026

## Top priorities for today

1. File taxes
2. Water the flowers
3. Play soccer with my son

## Recurring daily tasks

- [ ] Email clearing process
- [ ] Calendar sync
- [ ] Nightly drinking water task
```

## How it works

Your daysheets live in a working directory (set in `config.yml`) with four folders:

```
01-today      → today's daysheet (e.g. 2026-06-28.md)
02-tomorrow   → where you prepare tomorrow's daysheet
03-archive    → past daysheets, filed under YYYY/MM/
04-templates  → components/ used to assemble new daysheets
```

A new daysheet is assembled from an auto-generated date heading plus every
`.md` file in `04-templates/components/`, sorted by filename. Frontmatter
(`ready_to_archive: False`) is added automatically and is used later to decide
when an old daysheet can be filed away.

## Usage

```
daysheet today       # print today's daysheet (creating/archiving as needed)
daysheet tomorrow    # print tomorrow's daysheet (creating if folder is empty)
daysheet status      # report on the today / tomorrow / archive folders
daysheet help        # brief help
```

`today` and `tomorrow` print the file as-is, so they pipe cleanly into a
markdown renderer:

```
daysheet today | glow -
```

### today, in detail

If `01-today` already has today's daysheet, it is printed. Otherwise the tool
archives any **older** daysheets marked `ready_to_archive: True`, then:

- if `01-today` is now empty, it creates and prints today's daysheet;
- if not, it reports what remains (older daysheets vs. other material) and
  does **not** create today's daysheet — you clear it out manually and retry.

### tomorrow, in detail

If `02-tomorrow` has tomorrow's daysheet, it is printed. Otherwise, if the
folder is empty, tomorrow's daysheet is created; if not, the contents are
reported and nothing is created.

## Installation

```sh
git clone <this-repo>
cd daysheet
cp config.yml config.yml.local   # optional; or just edit config.yml
# set working_directory to your data folder
```

Add an alias to your `~/.zshrc` so `daysheet` works from anywhere:

```sh
alias daysheet='python3 /full/path/to/daysheet/daysheet.py'
```

Tab-completion for zsh is available — see [`misc/shell_completion.md`](misc/shell_completion.md).

## Configuration

Settings live in `config.yml` next to `daysheet.py`:

```yaml
working_directory: "~/daysheet-data"
```

## Requirements

- Python 3.6+
- [PyYAML](https://pypi.org/project/PyYAML/) is used if present, but a small
  built-in fallback parser handles `config.yml` without it.

## Maintainers

See [MAINTENANCE.md](MAINTENANCE.md) for internals and conventions to preserve.