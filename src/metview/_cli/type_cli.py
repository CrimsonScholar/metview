"""Any extra types needed to make CLI / terminal implementation easier to use."""

from __future__ import annotations

import argparse
import dataclasses


@dataclasses.dataclass
class ParsedArguments:
    """A very generic "argparse that runs a function" type."""

    commands: argparse.ArgumentParser | None

    @staticmethod
    def execute(_: ParsedArguments) -> None:
        """Call the subcommand and pass it ``namespace``.

        Args:
            namespace: The parsed user input to consider during the function run.

        """
