"""The public API for :ref:`metview`."""

import os

from PySide6 import QtCore

from ._core import constant

_CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
QtCore.QDir.addSearchPath(
    constant.QT_PREFIX,
    os.path.join(_CURRENT_DIRECTORY, "_resources"),
)
