"""Basic functions that make working with Qt easier."""

from PySide6 import QtCore, QtWidgets


def initialize_framed_label(widget: QtWidgets.QLabel) -> None:
    """Make ``widget`` center-aligned, framed, and generally prettier.

    Args:
        widget: Some QLabel whose style will be modified.

    """
    widget.setWordWrap(True)
    widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    widget.setFrameStyle(QtWidgets.QLabel.Box | QtWidgets.QLabel.Plain)  # type: ignore
    # NOTE: This is an arbitrary value that "looks nice" in the GUI
    widget.setStyleSheet("QLabel { padding: 10px; }")
