# coding: utf-8

"""The main ``show-gui`` widget. It can be embedded or a standalone window."""

from __future__ import annotations

from Qt import QtCore, QtWidgets


class Widget(QtWidgets.QWidget):
    """The main ``show-gui`` widget. It can be embedded or a standalone window.

    See Also:
        :meth:`Widget.create_as_window`.

    """

    def __init__(self, search_term: str="", parent: QtWidgets.QWidget | None=None) -> None:
        """Initialize the child widgets for this instance.

        Args:
            search_term: Some Work of Art to initially search with, if any.
            parent: The GUI that owns this instance, if any.

        """
        super().__init__(parent)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self._filter_type = QtWidgets.QPushButton("Filter:")
        self._filter_line = QtWidgets.QLineEdit()
        self._filter_details = QtWidgets.QPushButton("Details")

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self._filter_type)
        top.addWidget(self._filter_line)
        top.addWidget(self._filter_details)

        main_layout.addLayout(top)

        self._initialize_default_settings()

    def _initialize_default_settings(self) -> None:
        """Set the default appearance of child widgets."""
        self._filter_line.setPlaceholderText("Example: La Grenouillère")

        self._filter_type.setToolTip("Press this to filter by artwork-type.")
        self._filter_line.setToolTip("Type the name of the Work of Art here.")
        self._filter_details.setToolTip("Extra, less common filter actions.")

    @classmethod
    def create_as_window(
        cls,
        search_term: str="",
        parent: QtWidgets.QWidget | None=None,
    ) -> Widget:
        """Change this widget into a standalone viewer GUI.

        Args:
            search_term: Some Work of Art to initially search with, if any.
            parent: The GUI that owns this instance, if any.

        Returns:
            The created instance.

        """
        widget = cls(search_term=search_term, parent=parent)
        widget.setWindowTitle("MetViewer")
        # TODO: Add an icon
        # widget.setWindowIcon()
        widget.setWindowFlag(QtCore.Qt.Window)

        return widget
