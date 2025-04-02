# coding: utf-8

"""The main ``show-gui`` widget. It can be embedded or a standalone window."""

from __future__ import annotations

import functools
import logging
import math
import typing

from Qt import QtCore, QtGui, QtWidgets

from .._core import constant
from .._restapi import met_get_type
from .common import common_qt, iterbot, qt_constant
from .models import art_model, model_type
from .utilities import threader
from .utility_widgets import details_pane

_DEFAULT_LOADING_MESSAGE = "Loading..."
_LOGGER = logging.getLogger(__name__)


class _ArtworkSortFilterProxy(QtCore.QSortFilterProxyModel):
    """Sort and filter artwork based on the user's input."""

    def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
        """Check if ``left`` actually comes before ``right`` when both are sorted.

        Args:
            left: Some Qt locatino to check.
            right: Another Qt locatino to check.

        Returns:
            If ``left`` must come before ``right``, return ``True``. If it doesn't
            matter or ``left`` goes after ``right``, return ``False``.

        """

        def _get_default_text(index: QtCore.QModelIndex) -> str:
            return index.data(QtCore.Qt.DisplayRole) or ""

        column = left.column()

        if column == art_model.Column.datetime:
            left_datetime = typing.cast(
                met_get_type.Datetime | None,
                left.data(art_model.Model.data_role),
            )

            if not left_datetime:
                return False

            right_datetime = typing.cast(
                met_get_type.Datetime | None,
                right.data(art_model.Model.data_role),
            )

            if not right_datetime:
                return True

            return left_datetime < right_datetime

        return _get_default_text(left) < _get_default_text(right)


# NOTE: Ideally we'd use QIdentityProxyModel here but that isn't defined in Qt.py yet
class _DeferredLoadProxy(QtCore.QSortFilterProxyModel):
    """Extend a source model with "load more" capabilities.

    If the source model has thousands of entries, this class is designed to
    gradually show them - without overwhelming the user.

    Attributes:
        ran_fetched: When more model rows are requested, this signal is emitted.

    """

    ran_fetched = QtCore.Signal(QtCore.QModelIndex, int, int)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        """Initialize all of the row caches and keep track of ``parent`` if needed.

        Args:
            parent: An object which, if provided, holds a reference to this instance.

        """
        super().__init__(parent)

        # XXX: The project brief asks to initially load a maximum of 80 so that
        # will be our limit too.
        #
        self._fetch_limit = 80

        self._current_row_count: dict[QtCore.QModelIndex, int] = {}
        self._real_row_count: dict[QtCore.QModelIndex, int] = {}

    def canFetchMore(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """Check if we have seen all of the rows from ``parent`` yet, or not.

        Args:
            parent: Some Qt source location to check rows for.

        Returns:
            If there are no more rows to see / populate, return ``False``.

        """
        # NOTE: We always need this line
        self._current_row_count.setdefault(parent, 0)
        # NOTE: Rarely, canFetchMore runs before rowCount. So we add this just in case.
        self._real_row_count.setdefault(parent, 0)

        return self._current_row_count[parent] < self._real_row_count[parent]

    def fetchMore(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> None:
        """Add more rows to ``parent``. At least 1, up to the fetch limit.

        Args:
            parent: Some Qt source location to check rows for.

        """
        current = self._current_row_count[parent]
        total_remainder = self._real_row_count[parent] - current
        to_fetch = min(self._fetch_limit, total_remainder)

        self.beginInsertRows(parent, current, current + to_fetch)

        start = self._current_row_count[parent]
        self._current_row_count[parent] += self._fetch_limit
        end = self._current_row_count[parent]

        self.endInsertRows()

        self.ran_fetched.emit(parent, start, end)

    def invalidate(self) -> None:
        """Remove all cached row counts and start from scratch again."""
        self._current_row_count.clear()
        self._real_row_count.clear()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """Get the current row count that we have already populated.

        Args:
            parent: Some Qt source location to check rows for.

        Returns:
            The number of rows (from the start this will be 0. We add more rows later).

        """
        # NOTE: rowCount gets called before the fetch-related methods so we use this
        # opportunity to get the real size. We will need it for later.
        #
        self._real_row_count[parent] = super().rowCount(parent)
        self._current_row_count.setdefault(parent, 0)

        return self._current_row_count[parent]


# NOTE: Ideally we'd use QIdentityProxyModel here but that isn't defined in Qt.py yet
class _MaskedDataProxy(QtCore.QSortFilterProxyModel):
    """A proxy that masks and batches requests to The Met's REST API.

    Qt does not allow us developers to decide when and how often its MVC model data is
    queried. This is a problem for us because our row data requires some high-latency
    REST API calls, potentially dozens or thousands. By default, Qt does these queries
    on the main thread, which means bad interactivity in our GUIs. This class solves the
    problem like this:

    1. If Qt requests data that we know will be slow, show a placeholder instead
    2. Do the query in another thread
    3. Once the data is ready, report which indices are "ready to show its data"
    4. (outside of this class), update the views and widgets to show the data

    Once #4 happens, :meth:`_MaskedDataProxy.data` gets called again and we show the
    real data instead of the placeholder.

    The end result: The user gets uninterrupted UX and we can load any high-latency data
    as it becomes available.

    Attributes:
        needs_invalidate:
            If any internal data has changed in a way that could make views / proxies
            out-of-date, this signal is emitted. Important: when this signal emits, it's
            a good idea to immediately call ``invalidateFilter`` or ``invalidate`` on
            your proxy models, if any.

    """

    needs_invalidate = QtCore.Signal()

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        """Initialize all of the row caches and keep track of ``parent`` if needed.

        Args:
            parent: An object which, if provided, holds a reference to this instance.

        """
        super().__init__(parent)

        self._threads: list[
            tuple[QtCore.QThread, threader.QueryArtworkDetailsWorker]
        ] = []

    def _is_details_populated(self, index: QtCore.QModelIndex) -> bool:
        """Check if ``index`` has been partially or fully loaded with data.

        Args:
            index: Some Qt location (proxy or source) to check.

        Returns:
            If loaded, return ``True``.

        """
        artwork = typing.cast(
            model_type.Artwork,
            index.data(art_model.Model.artwork_role),
        )

        return artwork.is_details_populated()

    def data(  # pylint: disable=too-many-return-statements
        self,
        index: QtCore.QModelIndex,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.DisplayRole,
    ) -> str | model_type.Artwork | met_get_type.DatetimeRange | QtGui.QIcon | None:
        """Get any relevant data from ``index`` and show ``role``.

        Args:
            index: Some Qt source data location (row & column) to query from.
            role: The representation of ``index`` to return.

        Returns:
            The found data, if any.

        """
        if role == QtCore.Qt.DecorationRole:
            column = index.column()

            if column == 0:
                if not self._is_details_populated(index):
                    return QtGui.QIcon(f"{constant.QT_PREFIX}:loading.svg")

            return None

        if role == QtCore.Qt.ToolTipRole:
            if not self._is_details_populated(index):
                return _DEFAULT_LOADING_MESSAGE

            return super().data(index, role)  # type: ignore

        if role == QtCore.Qt.DisplayRole:
            if not self._is_details_populated(index):
                column = index.column()

                if column == 0:
                    return _DEFAULT_LOADING_MESSAGE

                return ""

            return super().data(index, role)  # type: ignore

        return super().data(index, role)  # type: ignore

    def populate_rows(self, parent: QtCore.QModelIndex, start: int, end: int) -> None:
        """Request data for all indices under ``parent``, from ``start`` to ``end``.

        We use a series of threads to query The Met's REST API, here. Each thread is
        response for a batch of Qt indices (to keep the overall thread size down).

        Important:
            This method is **inclusive**, all indices including ``start`` and ``end``
            will be populated.

        Args:
            parent: Some Qt location which has child indices to populate.
            start: The first index row to populate.
            end: The last index row to populate.

        """

        def _update_all(
            start: QtCore.QPersistentModelIndex,
            end: QtCore.QPersistentModelIndex,
            thread: QtCore.QThread,
        ) -> None:
            if not start.isValid() or not end.isValid():
                # NOTE: This should be super rare, if no impossible to happen.
                _LOGGER.warning('We cannot update. The "%s / %s" indices are invalid.')

                return

            self.dataChanged.emit(start, end)
            thread.quit()
            self.needs_invalidate.emit()

        def _get_all_qt_indices(
            parent: QtCore.QModelIndex,
            start: int,
            end: int,
        ) -> list[QtCore.QModelIndex]:
            all_indices: list[QtCore.QModelIndex] = []
            source_model = iterbot.get_lowest_source(self)

            for row_index in range(start, end):
                # NOTE: We only need to update one column from each row because that's
                # how the underlying data is laid out
                #
                proxy_index = self.index(row_index, qt_constant.ANY_COLUMN, parent)
                source_index = iterbot.map_to_source_recursively(
                    proxy_index, source_model
                )
                all_indices.append(source_index)

            return all_indices

        def _split_qt_indices_into_chunks(
            qt_indices: typing.Sequence[QtCore.QModelIndex],
        ) -> list[list[QtCore.QModelIndex]]:
            chunk = 10  # NOTE: An abitrary value to help minimize the number of threads
            rows = list(range(start, end))
            groups = [rows[index::chunk] for index in range(chunk)]
            output: list[list[QtCore.QModelIndex]] = []

            for subgroup in groups:
                output.append([qt_indices[index] for index in subgroup])

            return output

        for qt_indices in _split_qt_indices_into_chunks(
            _get_all_qt_indices(parent, start, end)
        ):
            worker = threader.QueryArtworkDetailsWorker(qt_indices)
            thread = QtCore.QThread(parent=self)
            thread.started.connect(worker.run)
            worker.finished.connect(
                functools.partial(
                    _update_all,
                    QtCore.QPersistentModelIndex(qt_indices[0]),
                    QtCore.QPersistentModelIndex(qt_indices[-1]),
                    thread,
                )
            )
            worker.moveToThread(thread)
            self._threads.append((thread, worker))
            # TODO: Consider limiting to 80 requests a second
            thread.start()

    def stop(self) -> None:
        """Force any ongoing work to terminate."""
        for thread, worker in self._threads:
            worker.stop()
            thread.terminate()


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

        # NOTE: An arbitrary size that "looks good"
        height = 550
        golden_ratio = 1.618
        self.resize(int(math.floor(height * golden_ratio)), height)

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
        self._no_artwork_label = QtWidgets.QLabel("No artwork loaded yet. Please wait!")
        self._artwork_view = QtWidgets.QTableView()
        self._details_switcher = QtWidgets.QStackedWidget()
        self._details_no_selection_label = QtWidgets.QLabel(
            "This view will show art information. Please select some art on the left."
        )
        self._artwork_switcher = QtWidgets.QStackedWidget()
        self._artwork_splitter = QtWidgets.QSplitter()
        self._details_pane = details_pane.DetailsPane()
        self._details_switcher.addWidget(self._details_no_selection_label)
        self._details_switcher.addWidget(self._details_pane)
        self._artwork_switcher.addWidget(self._no_artwork_label)
        self._artwork_switcher.addWidget(self._artwork_splitter)
        self._artwork_splitter.addWidget(self._artwork_view)
        self._artwork_splitter.addWidget(self._details_switcher)

        # TODO: Add a switcher for when we're querying artwork data
        self._worker = threader.ArtQueryWorker()
        self._thread = QtCore.QThread(parent=self)
        self._worker.moveToThread(self._thread)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self._filter_type)
        top.addWidget(self._filter_line)
        top.addWidget(self._filter_details)
        main_layout.addLayout(top)
        main_layout.addWidget(self._artwork_switcher)

        self._initialize_default_settings()

        if search_term:
            self._filter_line.setText(search_term)

        self.set_model(model or art_model.Model([]))

        self._initialize_interactive_settings()
        self._update_main_switcher()
        self._thread.start()

    def _initialize_default_settings(self) -> None:
        """Set the default appearance of child widgets."""
        common_qt.initialize_framed_label(self._no_artwork_label)
        common_qt.initialize_framed_label(self._details_no_selection_label)
        self._artwork_splitter.setHandleWidth(25)  # Arbitrary, thick value
        self._details_switcher.setCurrentWidget(self._details_no_selection_label)
        self._filter_line.setPlaceholderText("Example: La Grenouillère")

        self._no_artwork_label.setToolTip(
            "No artwork has been loaded yet. Once there is artwork to see, "
            "this widget will be automatically hidden "
            "and you will see a table with the data.",
        )
        self._artwork_view.horizontalHeader().setStretchLastSection(True)
        self._artwork_view.setSelectionBehavior(QtWidgets.QListView.SelectRows)
        self._artwork_view.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self._artwork_view.verticalHeader().hide()

        self._model_debouncer.setInterval(100)  # NOTE: Wait 0.1 sec between refreshes
        self._model_debouncer.setSingleShot(True)

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
        self._thread.started.connect(self._worker.run)
        self._worker.identifiers_found.connect(self._update_model)

    def _get_current_artworks(self) -> list[QtCore.QModelIndex]:
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
        output: list[QtCore.QModelIndex] = []
        selected = model.selectedIndexes()

        for index in iterbot.iter_unique_rows(selected):
            data = index.data(art_model.Model.artwork_role)

            if not isinstance(data, model_type.Artwork):
                invalids.append(data)

            output.append(index)

        if invalids:
            raise RuntimeError(f'Got unknown "{invalids}" data. Expected arkwork!')

        # IMPORTANT: ``output`` contains proxy indices which could cause the GUI to seg
        # fault if the user messes with filters so we get the real source index before
        # returning.
        #
        proxy = self._artwork_view.model()
        source = iterbot.get_lowest_source(proxy)

        return [iterbot.map_to_source_recursively(index, source) for index in output]

    def _stop_masked_proxy_threads(self) -> None:
        """Stop all threads from all :class:`_MaskedDataProxy` models."""
        top_proxy = self._artwork_view.model()

        if not top_proxy:
            return

        for proxy in iterbot.get_all_models_by_type(top_proxy, _MaskedDataProxy):
            proxy.stop()

    def _update_details_pane(self) -> None:
        """Show or hide the details pane if the user has selected some artwork."""
        if artworks := self._get_current_artworks():
            self._details_pane.set_current_artworks(artworks)
            self._details_switcher.setCurrentWidget(self._details_pane)
        else:
            self._details_switcher.setCurrentWidget(self._details_no_selection_label)

    def _update_main_switcher(self) -> None:
        """Show the artwork table if there is any data to show."""
        source = iterbot.get_lowest_source(self._artwork_view.model())

        if not source.rowCount(QtCore.QModelIndex()):
            self._artwork_switcher.setCurrentWidget(self._no_artwork_label)
        else:
            self._artwork_switcher.setCurrentWidget(self._artwork_splitter)

    def _invalidate_proxies(self) -> None:
        """Force proxies to redraw their sorting and filters."""
        top_proxy = typing.cast(_ArtworkSortFilterProxy, self._artwork_view.model())
        lowest_proxy = typing.cast(
            QtCore.QSortFilterProxyModel,
            iterbot.get_lowest_proxy(top_proxy),
        )
        lowest_proxy.invalidate()

    def _update_model(self, identifiers: list[int]) -> None:
        """Clear and refresh our internal model with ``identifiers``.

        Args:
            identifiers: Some Met Museum Artwork IDs (integers) to display.

        """
        top_proxy = typing.cast(_ArtworkSortFilterProxy, self._artwork_view.model())
        model = _get_artwork_source_model(top_proxy)
        model.update_artwork_identifiers(identifiers)
        self._invalidate_proxies()
        self._update_main_switcher()

    def set_model(self, model: art_model.Model) -> None:
        """Store and display source ``model``.

        Args:
            model: Some Met Museum-related artwork model.

        Raises:
            RuntimeError: If ``model`` could not be applied as expected due to a bug.

        """
        self._stop_masked_proxy_threads()
        deferred_proxy = _DeferredLoadProxy(parent=self)
        deferred_proxy.setSourceModel(model)
        mask_proxy = _MaskedDataProxy(parent=self)
        mask_proxy.setSourceModel(deferred_proxy)
        sorter_proxy = _ArtworkSortFilterProxy(parent=self)
        sorter_proxy.setSourceModel(mask_proxy)

        self._artwork_view.setModel(sorter_proxy)
        self._artwork_view.setSortingEnabled(True)
        self._artwork_view.sortByColumn(
            art_model.Column.title, QtCore.Qt.AscendingOrder
        )
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
        self._stop_masked_proxy_threads()
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
