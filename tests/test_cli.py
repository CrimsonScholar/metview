"""All terminal-related tests for the :ref:`metview` CLI."""

import contextlib
import typing
import unittest
from unittest import mock

from metview._cli import cli, exception_type


class Failure(unittest.TestCase):
    """Make sure the CLI fails when it's supposed to."""

    def test_empty(self) -> None:
        """Fail to run the CLI if no subcommand is chosen."""
        with self.assertRaises(exception_type.UserInputError), _silence_print():
            cli.main([])


@contextlib.contextmanager
def _silence_print() -> typing.Generator[None, None, None]:
    """Prevent :mod:`argparse` from printing, to keep unittests concise.

    Yields:
        A context that won't print messages to the terminal.

    """
    with mock.patch("argparse.ArgumentParser.print_help"):
        yield
