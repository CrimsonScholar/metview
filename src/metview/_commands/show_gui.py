"""The ``show-gui`` subcommand implementation."""

import typing

from Qt import QtWidgets

from .._gui import gui


def run(search_term: str="") -> None:
    """Show a Qt GUI to the user so they can search Works of Art.

    Args:
        search_term: Some artwork name to look for, if any.

    """
    application = typing.cast(
        QtWidgets.QApplication,
        QtWidgets.QApplication.instance()  # type: ignore
        or QtWidgets.QApplication([])
    )
    widget = gui.Widget.create_as_window(search_term=search_term)
    widget.show()
