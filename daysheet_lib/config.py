"""Configuration constants and config.yml loading for daysheet."""

import os
import re
import sys
from pathlib import Path

# The repository root is the parent of this package directory, i.e. the folder
# that contains daysheet.py and config.yml.
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config.yml"

TODAY_DIR = "01-today"
TOMORROW_DIR = "02-tomorrow"
ARCHIVE_DIR = "03-archive"
TEMPLATE_DIR = "04-templates"
COMPONENTS_SUBDIR = "components"

# A valid daysheet filename is exactly an ISO date, e.g. 2026-06-28.md
DAYSHEET_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.md$")


def fail(message, code=1):
    """Print an error to stderr and exit."""
    print(f"daysheet: {message}", file=sys.stderr)
    sys.exit(code)


def load_config():
    """Load config.yml and return the resolved working directory Path.

    We avoid a hard PyYAML dependency for this single string key by doing a
    tiny line-based parse, but use PyYAML if it is available (more robust).
    """
    if not CONFIG_PATH.exists():
        fail(
            f"Config file not found: {CONFIG_PATH}\n"
            "Copy config-example.yml to config.yml next to daysheet.py with:\n"
            '  working_directory: "/path/to/your/daysheet/data"'
        )

    working_directory = None
    try:
        import yaml  # type: ignore

        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        working_directory = data.get("working_directory")
    except ImportError:
        # Minimal fallback parser: find `working_directory: <value>`.
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("working_directory:"):
                    working_directory = line.split(":", 1)[1].strip()
                    working_directory = working_directory.strip("'\"")
                    break

    if not working_directory:
        fail("config.yml does not define a 'working_directory'.")

    wd = Path(os.path.expanduser(working_directory)).resolve()
    if not wd.is_dir():
        fail(f"Working directory does not exist: {wd}")
    return wd
