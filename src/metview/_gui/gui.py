# coding: utf-8

"""The main ``show-gui`` widget. It can be embedded or a standalone window."""

from __future__ import annotations

import typing

from Qt import QtCore, QtGui, QtWidgets

from .._restapi import met_get
from .common import common_qt, iterbot
from .models import art_model, model_type
from .utility_widgets import details_pane


class _ArtworkProxy(QtCore.QSortFilterProxyModel):
    """Sort and filter artwork based on the user's input."""

    # TODO: Finish this class later
    def rowCount(
        self, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> int:  # pylint: disable=invalid-name
        """Get the rows to show in the GUI.

        Args:
            parent: The immediate parent to get the children for.

        Returns:
            The number of rows to show.

        """
        # TODO: Remove this min() later and redo this method
        # return super().rowCount(parent)
        return min(10, super().rowCount(parent))


class _MetThread(QtCore.QThread):
    """Handle any high latency / slow functions here.

    Attributes:
        identifiers_found:
            After we query the Met Museum for all Artworks, the found IDs are emitted.

    """

    identifiers_found = QtCore.Signal(list)

    def run(self) -> None:
        """Look for Met Museum IDs and update the parent thread when it is ready."""
        identifiers = met_get.get_all_identifiers()
        # IMPORTANT: Lower identifiers tend to be empty or have missing contents so we
        # will prioritize the later IDs. Both may get displayed in the end so this is
        # just done to give the user a meaningful GUI result sooner.
        #
        self.identifiers_found.emit(sorted(identifiers, reverse=True))


class Window(QtWidgets.QWidget):  # pylint: disable=too-few-public-methods
    """A standalone version of :class:`Widget`.

    This class is not meant to be embedded into other classes via composition.
    Use :class:`Widget` instead.

    """

    def __init__(
        self,
        search_term: str = "",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Change this widget into a standalone viewer GUI.

        Args:
            search_term: Some Work of Art to initially search with, if any.
            parent: The GUI that owns this instance, if any.

        Returns:
            The created instance.

        """
        super().__init__(parent)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self._close_button = QtWidgets.QPushButton("Close")
        self._widget = Widget(search_term=search_term, parent=parent)

        main_layout.addWidget(self._widget)

        bottom = QtWidgets.QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(self._close_button)
        main_layout.addLayout(bottom)

        self.setWindowTitle("MetViewer")
        # TODO: Add an icon
        # self.setWindowIcon()
        self.setWindowFlag(QtCore.Qt.Window)

        self._widget.layout().setContentsMargins(0, 0, 0, 0)
        self._close_button.setToolTip("Press this to close this GUI window.")
        self._close_button.clicked.connect(self.close)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Force any ongoing work to terminate before closing.

        Args:
            event: The Qt-provided event that handles widget closing.

        """
        self._widget.close()

        super().closeEvent(event)


class Widget(
    QtWidgets.QWidget
):  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """The main ``show-gui`` widget. It can be embedded or a standalone window.

    See Also:
        :meth:`Widget.create_as_window`.

    """

    def __init__(
        self,
        search_term: str = "",
        model: art_model.Model | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initialize the child widgets for this instance.

        Args:
            search_term:
                Some Work of Art to initially search for, if any.
            model:
                A source model to display in this instance. If none is provided, an
                empty model is used instead and we query the artwork to show, ourslves.
            parent:
                The GUI that owns this instance, if any.

        """
        super().__init__(parent)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # NOTE: The top widgets
        self._filter_type = QtWidgets.QPushButton("Filter:")
        self._filter_line = QtWidgets.QLineEdit()
        self._filter_details = QtWidgets.QPushButton("Details")

        # NOTE: The lower artwork + details widgets
        #
        # +-------+-------------------------+
        # | art_a | name: art_a             |
        # | art_b | artist: Some Person Jr. |
        # +-------+-------------------------+
        #
        self._artwork_view = QtWidgets.QTableView()
        self._details_switcher = QtWidgets.QStackedWidget()
        self._details_no_selection_label = QtWidgets.QLabel(
            "This view will show art information. Please select some art on the left."
        )
        self._artwork_splitter = QtWidgets.QSplitter()
        self._details_pane = details_pane.DetailsPane()
        self._details_switcher.addWidget(self._details_no_selection_label)
        self._details_switcher.addWidget(self._details_pane)
        self._artwork_splitter.addWidget(self._artwork_view)
        self._artwork_splitter.addWidget(self._details_switcher)

        # TODO: Add a switcher for when we're querying artwork data
        self._thread = _MetThread(parent=self)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self._filter_type)
        top.addWidget(self._filter_line)
        top.addWidget(self._filter_details)
        main_layout.addLayout(top)
        main_layout.addWidget(self._artwork_splitter)

        self._initialize_default_settings()

        if search_term:
            self._filter_line.setText(search_term)

        self.set_model(model or art_model.Model([]))

        self._initialize_interactive_settings()
        self._thread.run()

    def _initialize_default_settings(self) -> None:
        """Set the default appearance of child widgets."""
        common_qt.initialize_framed_label(self._details_no_selection_label)
        self._artwork_splitter.setHandleWidth(25)  # Arbitrary, thick value
        self._details_switcher.setCurrentWidget(self._details_no_selection_label)
        self._filter_line.setPlaceholderText("Example: La Grenouillère")

        self._artwork_view.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self._artwork_view.horizontalHeader().setStretchLastSection(True)
        self._artwork_view.verticalHeader().hide()

        self._filter_type.setToolTip("Press this to filter by artwork-type.")
        self._filter_line.setToolTip("Type the name of the Work of Art here.")
        self._filter_details.setToolTip("Extra, less common filter actions.")

        self._details_pane.setToolTip("Information about the selected artwork.")
        self._details_no_selection_label.setToolTip(
            "If you are seeing this, you need to select some artwork. "
            "Once you do that, this widget will be replaced with the artwork details."
        )

    def _initialize_interactive_settings(self) -> None:
        """Create any click / automatic functionality for this instance."""
        self._thread.identifiers_found.connect(self._update_model)

    def _get_current_artworks(self) -> list[model_type.Artwork]:
        """Get the user's current artwork selection, if any.

        Raises:
            RuntimeError: If any selected rows somehow did not find artwork.

        Returns:
            If the current user artwork selection.

        """
        model = self._artwork_view.selectionModel()

        if not model:
            raise RuntimeError(
                "Artwork view has no selection model. This is a bug, please fix!"
            )

        invalids: list[typing.Any] = []
        output: list[model_type.Artwork] = []
        selected = model.selectedIndexes()

        for index in iterbot.iter_unique_rows(selected):
            data = index.data(art_model.Model.artwork_role)

            if not isinstance(data, model_type.Artwork):
                invalids.append(data)

            output.append(data)

        if invalids:
            raise RuntimeError(f'Got unknown "{invalids}" data. Expected arkwork!')

        return output

    def _update_details_pane(self) -> None:
        """Show or hide the details pane if the user has selected some artwork."""
        if artworks := self._get_current_artworks():
            self._details_pane.set_current_artworks(artworks)
            self._details_switcher.setCurrentWidget(self._details_pane)
        else:
            self._details_switcher.setCurrentWidget(self._details_no_selection_label)

    def _update_model(self, identifiers: list[int]) -> None:
        """Clear and refresh our internal model with ``identifiers``.

        Args:
            identifiers: Some Met Museum Artwork IDs (integers) to display.

        """
        proxy = self._artwork_view.model()
        model = _get_artwork_source_model(proxy)
        model.update_artwork_identifiers(identifiers)

    def set_model(self, model: art_model.Model) -> None:
        """Store and display source ``model``.

        Args:
            model: Some Met Museum-related artwork model.

        Raises:
            RuntimeError: If ``model`` could not be applied as expected due to a bug.

        """
        proxy = _ArtworkProxy(parent=self)
        proxy.setSourceModel(model)
        self._artwork_view.setModel(proxy)
        self._artwork_view.resizeColumnsToContents()
        selection_model = self._artwork_view.selectionModel()

        if not selection_model:
            raise RuntimeError(
                "Artwork view has no selection model. This is a bug, please fix!"
            )

        selection_model.selectionChanged.connect(self._update_details_pane)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Force any ongoing work to terminate before closing.

        Args:
            event: The Qt-provided event that handles widget closing.

        """
        self._thread.terminate()

        super().closeEvent(event)


def _get_artwork_source_model(proxy: QtCore.QAbstractItemModel) -> art_model.Model:
    """Find the model that defines our Artwork objects.

    Args:
        proxy: A starting model (which may wrap other models).

    Raises:
        RuntimeError: If no source model could be found.

    Returns:
        The found source model.

    """
    source = iterbot.get_lowest_source(proxy)

    if isinstance(source, art_model.Model):
        return source

    raise RuntimeError(f'Expected a art_model.Model source but got "{source}" instead.')
