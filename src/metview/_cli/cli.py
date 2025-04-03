"""The main CLI / terminal parser and implementation."""

import argparse
import dataclasses
import logging
import typing

from PySide6 import QtWidgets

from .._core import constant
from .._gui import gui
from . import exception_type, type_cli


@dataclasses.dataclass
class _CommonArguments:
    """Arguments that all subcommands are expected to support.

    Attributes:
        verbose: If included, show more logging messages to the user.

    """

    verbose: int


class _ShowGuiArguments(_CommonArguments):  # pylint: disable=too-few-public-methods
    """The :ref:`show-gui` subcommand arguments.

    Attributes:
        search_term: Some Work of Art to initially view.

    """

    search_term: str


def _add_show_gui_subcommand(parser: argparse.ArgumentParser) -> None:
    """Define the ``show-gui`` subcommand to ``parser``.

    Args:
        parser: The Python CLI that will be modified.

    """
    parser.set_defaults(execute=_show_gui)
    _add_verbose_flag(parser)


def _add_verbose_flag(parser: argparse.ArgumentParser) -> None:
    """Add a ``--verbose`` to ``parser``.

    Args:
        parser: The Python CLI that will be modified.

    """
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Add to show logs. Repeat to show more logs.",
    )


def _parse_arguments(text: list[str]) -> type_cli.ParsedArguments:
    """Convert raw user terminal input into data that Python understands.

    Args:
        text: All user input. e.g. ``["show-gui", "--verbose"]``.

    Raises:
        UserInputError: If ``text`` has no subcommand.

    Returns:
        The parsed output.

    """
    parser = argparse.ArgumentParser(
        description="The Met Museum Viewer. See subcommands for details."
    )
    subparsers = parser.add_subparsers(
        description="All metview inner commands that you can run.",
        dest="commands",
    )
    description = "Interactively search and filter Works Of Art from The Met in a GUI."
    show_gui_parser = subparsers.add_parser(
        name="show-gui",
        description=description,
        help=description,
    )
    show_gui_parser.add_argument(
        "--search-term",
        default="",
        help="An initial Art title to search, if any.",
    )
    _add_show_gui_subcommand(show_gui_parser)

    namespace = typing.cast(type_cli.ParsedArguments, parser.parse_args(text))

    if not namespace.commands:
        parser.print_help()

        raise exception_type.UserInputError("You must select a subcommand to continue.")

    return namespace


def _set_logger_if_needed(scale: int) -> None:
    """Set the root logger's level according to ``namespace``.

    Args:
        scale: A 0-or-more value. 0 == less logs. 1+ means more verbose logging.

    """
    level_difference = logging.INFO - logging.DEBUG
    initial_level = logging.WARNING
    computed_level = initial_level - max(0, level_difference * scale)
    logger = logging.getLogger(constant.ROOT_LOGGER_NAME)
    logger.setLevel(computed_level)


def _show_gui(namespace: _ShowGuiArguments) -> None:
    """Initialize and show a GUI with the user's arguments.

    Args:
        namespace: The parsed user input.

    """
    _set_logger_if_needed(namespace.verbose)

    application = typing.cast(
        QtWidgets.QApplication,
        QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
    )
    window = gui.Window(search_term=namespace.search_term)
    application.setStyle("macOS")
    window.show()
    application.exec_()


def main(text: list[str]) -> None:
    """Parse the user's raw terminal text and load the GUI.

    Args:
        text: All user input. e.g. ``["show-gui", "--verbose"]``.

    """
    namespace = _parse_arguments(text)
    namespace.execute(namespace)
