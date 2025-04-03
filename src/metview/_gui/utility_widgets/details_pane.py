"""The right-hand side view of :ref:`metview`. It shows basic artwork + artist data."""

import logging
import typing

from Qt import QtCore, QtGui, QtWidgets

from ..common import common_qt, iterbot
from ..models import art_model, model_type

_LOGGER = logging.getLogger(__name__)


class _DetailsPage(QtWidgets.QWidget):
    """A detailed breakdown of some artwork."""

    def __init__(
        self,
        index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initialize the child widgets for this instance.

        Args:
            index: The source Qt index to display.
            parent: The GUI that owns this instance, if any.

        """
        super().__init__(parent)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self._artwork_label = QtWidgets.QLabel("Title:")
        self._artwork_line = QtWidgets.QLineEdit()
        self._artist_label = QtWidgets.QLabel("Artist:")
        self._artist_line = QtWidgets.QLineEdit()
        self._datetime_label = QtWidgets.QLabel("Datetime:")
        self._datetime_line = QtWidgets.QLineEdit()
        self._classifaction_label = QtWidgets.QLabel("Classification:")
        self._classifaction_line = QtWidgets.QLineEdit()
        self._no_thumbnail_label = QtWidgets.QLabel("No thumbnail")
        self._thumbnail_label = QtWidgets.QLabel()
        self._thumbnail_label.setMaximumHeight(200)
        self._thumbnail_switcher = QtWidgets.QStackedWidget()
        self._thumbnail_switcher.addWidget(self._no_thumbnail_label)
        self._thumbnail_switcher.addWidget(self._thumbnail_label)

        summary_layout = QtWidgets.QGridLayout()
        summary_layout.addWidget(self._artwork_label, 0, 0)
        summary_layout.addWidget(self._artwork_line, 0, 1)
        summary_layout.addWidget(self._artist_label, 1, 0)
        summary_layout.addWidget(self._artist_line, 1, 1)
        summary_layout.addWidget(self._datetime_label, 2, 0)
        summary_layout.addWidget(self._datetime_line, 2, 1, 1, -1)
        summary_layout.addWidget(self._classifaction_label, 3, 0)
        summary_layout.addWidget(self._classifaction_line, 3, 1)
        main_layout.addLayout(summary_layout)
        main_layout.addWidget(self._thumbnail_switcher, alignment=QtCore.Qt.AlignCenter)
        main_layout.addItem(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            ),
        )

        self._initialize_default_settings()
        self.set_current_artwork(index)

    def _initialize_default_settings(self) -> None:
        """Set the default appearance for all child widgets."""
        self._artwork_line.setReadOnly(True)
        self._artist_line.setReadOnly(True)
        self._datetime_line.setReadOnly(True)
        self._classifaction_line.setReadOnly(True)

        common_qt.initialize_framed_label(self._no_thumbnail_label)

        tip = "The title of the artwork."
        self._artwork_label.setToolTip(tip)
        self._artwork_line.setToolTip(tip)
        tip = "The person / group / entity that created the art."
        self._artist_label.setToolTip(tip)
        self._artist_line.setToolTip(tip)
        tip = "The year / period that the artwork was thought to be made during."
        self._datetime_label.setToolTip(tip)
        self._datetime_line.setToolTip(tip)
        tip = "The way that the artwork was presented / created (e.g. Etching, Print)"
        self._classifaction_label.setToolTip(tip)
        self._classifaction_line.setToolTip(tip)
        self._no_thumbnail_label.setToolTip("No artwork image preview could be found.")
        self._thumbnail_label.setToolTip("Here is what the artwork looks like.")

    def _make_thumbnail_pixmap(self, thumbnail: bytes) -> QtGui.QPixmap:
        """Load ``thumbnail`` image as a Qt object.

        Args:
            thumbnail: Some blob of jpg / png / something data to load.

        Returns:
            The loaded image.

        """
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(QtCore.QByteArray(thumbnail))
        maximum_height = self._thumbnail_label.maximumHeight()

        if pixmap.height() > maximum_height:
            pixmap = pixmap.scaledToHeight(maximum_height, QtCore.Qt.SmoothTransformation)

        return pixmap

    def clear_current_artwork(self) -> None:
        """Hide all artwork display details."""
        self._artwork_line.clear()
        self._artist_line.clear()
        self._datetime_line.clear()
        self._classifaction_line.clear()
        self.clear_thumbnail()

    def clear_thumbnail(self) -> None:
        """Hide any artwork thumbnail display."""
        self._thumbnail_switcher.setCurrentWidget(self._no_thumbnail_label)

    def set_current_artwork(self, index: QtCore.QModelIndex) -> None:
        """Display the ``artwork`` in this instance.

        Args:
            index: The source Qt index to display.

        """
        self._artwork_line.setText(_get_display(index, art_model.Column.title))
        self._artist_line.setText(_get_display(index, art_model.Column.artist))
        self._datetime_line.setText(_get_display(index, art_model.Column.datetime))
        self._classifaction_line.setText(
            _get_display(index, art_model.Column.classification)
        )

        source = iterbot.get_lowest_source(index.model())
        source_index = iterbot.map_to_source_recursively(index, source)
        thumbnail_index = source_index.siblingAtColumn(art_model.Column.thumbnail)
        thumbnail: bytes | None = None

        if not thumbnail_index.isValid():
            _LOGGER.warning('Index "%s" has no thumbnail index.', source_index)

            self._thumbnail_switcher.setCurrentWidget(self._no_thumbnail_label)

            return

        thumbnail = typing.cast(
            bytes | None,
            thumbnail_index.data(art_model.Model.data_role),
        )

        if not thumbnail:
            self._thumbnail_switcher.setCurrentWidget(self._no_thumbnail_label)

            return

        pixmap = self._make_thumbnail_pixmap(thumbnail)
        self._thumbnail_label.setPixmap(pixmap)
        self._thumbnail_switcher.setCurrentWidget(self._thumbnail_label)


class DetailsPane(QtWidgets.QTabWidget):  # pylint: disable=too-few-public-methods
    """A QTabWidget that is meant to show artwork."""

    def set_current_artworks(
        self, indices: typing.Iterable[QtCore.QModelIndex]
    ) -> None:
        """Clear all existing artworks and populate with ``artworks``.

        Args:
            indices: The source Qt indices (Met Artwork) to show.

        """
        self.clear()

        maximum_length = 10

        for index in indices:
            label = _get_display(index, art_model.Column.title)

            if len(label) > maximum_length:
                label = label[:maximum_length] + "..."

            self.addTab(_DetailsPage(index), label)
            tab_index = self.count() - 1
            self.setTabToolTip(
                tab_index,
                _get_display(index, art_model.Column.title, QtCore.Qt.ToolTipRole),
            )


def _get_display(
    index: QtCore.QModelIndex,
    column: int,
    role: QtCore.Qt.ItemDataRole = QtCore.Qt.DisplayRole,
) -> str:
    """Get the user-display text starting from ``index``.

    Args:
        index: Some source Qt index to look through for data.
        column: The specific data to find. e.g. :obj:`.Column.datetime`.

    Raises:
        RuntimeError: If we cannot resolve a valid index from ``index`` and ``column``.

    Returns:
        The found displayable text.

    """
    sibling = index.siblingAtColumn(column)

    if not sibling.isValid():
        raise RuntimeError(
            f'Cannot get display text, "{index} / {column}" has no valid sibling.',
        )

    return typing.cast(str, sibling.data(role))
