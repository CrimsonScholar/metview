"""All terminal-related tests for the :ref:`metview` CLI."""

import unittest

from metview._cli import cli, exception_type


class Failure(unittest.TestCase):
    """Make sure the CLI fails when it's supposed to."""

    def test_empty(self) -> None:
        """Fail to run the CLI if no subcommand is chosen."""
        with self.assertRaises(exception_type.UserInputError):
            cli.main([])
