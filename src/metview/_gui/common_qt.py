"""Basic functions that make working with Qt easier."""

from Qt import QtCore, QtWidgets


def initialize_framed_label(widget: QtWidgets.QLabel) -> None:
    """Make ``widget`` center-aligned, framed, and generally prettier.

    Args:
        widget: Some QLabel whose style will be modified.

    """
    widget.setWordWrap(True)
    widget.setAlignment(QtCore.Qt.AlignCenter)
    widget.setFrameStyle(QtWidgets.QLabel.Box | QtWidgets.QLabel.Plain)
