"""daysheet support package.

The `daysheet.py` entry point is intentionally thin; the real logic lives
here:

- `config`   — locating constants and loading config.yml
- `core`     — filename/frontmatter helpers and daysheet assembly
- `commands` — one module per `daysheet` subcommand

See MAINTENANCE.md for the full layout.
"""
