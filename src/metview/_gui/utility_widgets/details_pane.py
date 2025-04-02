"""The right-hand side view of :ref:`metview`. It shows basic artwork + artist data."""

import typing

from Qt import QtGui, QtWidgets

from ..common import common_qt
from ..models import model_type


class _DetailsPage(QtWidgets.QWidget):
    """A detailed breakdown of some artwork."""

    def __init__(
        self,
        artwork: model_type.Artwork,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initialize the child widgets for this instance.

        Args:
            parent: The GUI that owns this instance, if any.

        """
        super().__init__(parent)

        main_layout = QtWidgets.QGridLayout()
        self.setLayout(main_layout)

        self._artwork_label = QtWidgets.QLabel("Title:")
        self._artwork_line = QtWidgets.QLineEdit()
        self._artist_label = QtWidgets.QLabel("Artist:")
        self._artist_line = QtWidgets.QLineEdit()
        self._datetime_label = QtWidgets.QLabel("Datetime:")
        self._datetime_line = QtWidgets.QLineEdit()
        self._no_thumbnail_label = QtWidgets.QLabel("No thumbnail")
        self._thumbnail_label = QtWidgets.QLabel()
        self._thumbnail_switcher = QtWidgets.QStackedWidget()
        self._thumbnail_switcher.addWidget(self._no_thumbnail_label)
        self._thumbnail_switcher.addWidget(self._thumbnail_label)

        # TODO: Add better column stretch
        main_layout.addWidget(self._artwork_label, 0, 0)
        main_layout.addWidget(self._artwork_line, 0, 1)
        main_layout.addWidget(self._artist_label, 1, 0)
        main_layout.addWidget(self._artist_line, 1, 1)
        main_layout.addWidget(self._thumbnail_switcher, 0, 2, 2, 2)
        main_layout.addWidget(self._datetime_label, 2, 0)
        main_layout.addWidget(self._datetime_line, 2, 1)

        self._initialize_default_settings()
        self.set_current_artwork(index)

    def _initialize_default_settings(self) -> None:
        """Set the default appearance for all child widgets."""
        self._artwork_line.setReadOnly(True)
        self._artist_line.setReadOnly(True)
        self._datetime_line.setReadOnly(True)
        common_qt.initialize_framed_label(self._no_thumbnail_label)

        tip = "The title of the artwork."
        self._artwork_label.setToolTip(tip)
        self._artwork_line.setToolTip(tip)
        tip = "The person / group / entity that created the art."
        self._artist_label.setToolTip(tip)
        self._artist_line.setToolTip(tip)
        tip = "The year / period that the artwork was thought to be made during."
        self._datetime_label.setToolTip(tip)
        self._datetime_label.setToolTip(tip)
        self._no_thumbnail_label.setToolTip("No artwork image preview could be found.")
        self._thumbnail_label.setToolTip("Here is what the artwork looks like.")

    def clear_current_artwork(self) -> None:
        """Hide all artwork display details."""
        self._artwork_line.clear()
        self._artist_line.clear()
        self.clear_thumbnail()

    def clear_thumbnail(self) -> None:
        """Hide any artwork thumbnail display."""
        self._thumbnail_switcher.setCurrentWidget(self._no_thumbnail_label)

    def set_current_artwork(self, artwork: model_type.Artwork) -> None:
        """Display the ``artwork`` in this instance."""
        self._artwork_line.setText(artwork.get_title())
        self._artist_line.setText(artwork.get_artist())

        if thumbnail := artwork.get_thumbnail_data():
            # TODO: Make sure this code works later
            self._thumbnail_label.setPixmap(QtGui.QPixmap(thumbnail))

        self._thumbnail_switcher.setCurrentWidget(self._thumbnail_label)


class DetailsPane(QtWidgets.QTabWidget):  # pylint: disable=too-few-public-methods
    """A QTabWidget that is meant to show artwork."""

    def set_current_artworks(
        self, artworks: typing.Iterable[model_type.Artwork]
    ) -> None:
        """Clear all existing artworks and populate with ``artworks``.

        Args:
            artworks: The Met artwork to show.

        """
        self.clear()

        # TODO: Make sure this looks good even if titles are rathger long
        # + lots of ``artworks`` selected at-once.
        #
        for artwork in artworks:
            self.addTab(_DetailsPage(artwork), artwork.get_title())
