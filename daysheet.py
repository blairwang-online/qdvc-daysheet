#!/usr/bin/env python3
"""daysheet — manage markdown "daysheets" for daily planning.

This is a thin entry point. The implementation lives in the
`python_modules` package:

- python_modules/config.py        constants + config.yml loading
- python_modules/core.py          filename/frontmatter helpers + assembly
- python_modules/commands/*.py    one module per subcommand

See README.md for an overview and MAINTENANCE.md for internals.
"""

import sys
from pathlib import Path

# Ensure the repo root is importable so `python_modules` resolves regardless
# of where `daysheet` is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from python_modules.commands import COMMANDS, NO_CONFIG
from python_modules.config import fail, load_config


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        COMMANDS["help"]()
        return

    cmd = argv[0]
    handler = COMMANDS.get(cmd)
    if handler is None:
        fail(f"unknown command '{cmd}'. Try `daysheet help`.")

    if cmd in NO_CONFIG:
        handler()
        return

    wd = load_config()
    handler(wd)


if __name__ == "__main__":
    main()
