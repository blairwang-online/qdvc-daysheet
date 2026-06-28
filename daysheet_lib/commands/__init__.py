"""One module per `daysheet` subcommand, plus a small registry.

Each command module exposes a `run(wd)` function (except `help`, which takes
no working directory). `COMMANDS` maps the CLI verb to its handler, and
`NEEDS_CONFIG` records which commands require a loaded working directory.
"""

from daysheet_lib.commands import help as help_cmd
from daysheet_lib.commands import status as status_cmd
from daysheet_lib.commands import today as today_cmd
from daysheet_lib.commands import tomorrow as tomorrow_cmd

COMMANDS = {
    "today": today_cmd.run,
    "tomorrow": tomorrow_cmd.run,
    "status": status_cmd.run,
    "help": help_cmd.run,
}

# Commands that do NOT need config.yml / a working directory.
NO_CONFIG = {"help"}
