"""Initialize Qt so that we can use it in unittests."""

from PySide6 import QtWidgets

# IMPORTANT: We need a QApplication or unittests cannot run. Do not remove this line.
_APPLICATION = QtWidgets.QApplication([])
