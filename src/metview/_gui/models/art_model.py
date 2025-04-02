"""The MVC model that interacts between The Met's API and Qt."""

import typing

from Qt import QtCore

from . import model_type

_ARTWORK_COLUMN = 0
_ARTIST_COLUMN = 1


class Model(QtCore.QAbstractListModel):
    """The MVC model that interacts between The Met's API and Qt.

    Attributes:
        artwork_role:
            The role that gets the underlying Met API data. Be careful with this role
            (use it only in read-only contexts).

    """

    artwork_role = QtCore.Qt.UserRole

    def __init__(
        self,
        identifiers: typing.Sequence[int],
        parent: QtCore.QObject | None = None,
    ) -> None:
        """Keep track of some artwork to query later.

        Args:
            data:
                All Artwork from The Met to consider.
            parent:
                An object which, if provided, holds a reference to this instance.
                It's recommended to always provide a parent for Qt models.

        """
        super().__init__(parent)

        self._identifiers = identifiers
        self._cache: dict[int, model_type.Artwork] = {}

    def _get_artwork(self, index: QtCore.QModelIndex) -> model_type.Artwork:
        """Get the real artwork data from `index``.

        Args:
            index: Some Qt location to query from.

        Returns:
            The found artwork.

        """
        identifier = self._identifiers[index.row()]

        if identifier in self._cache:
            node = self._cache[identifier]
        else:
            node = model_type.Artwork(identifier=identifier)
            self._cache[identifier] = node

        return node

    def columnCount(self, _: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # pylint: disable=invalid-name
        """Get the number of columns to show in a view by default.

        Args:
            parent: The immediate Qt location parent to look within.

        Returns:
            Show the artwork and the artist.

        """
        return 2

    def data(  # pylint: disable=too-many-return-statements
        self,
        index: QtCore.QModelIndex,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.DisplayRole,
    ) -> str | model_type.Artwork | None:
        """Get any relevant data from ``index`` and show ``role``.

        Args:
            index: Some Qt source data location (row & column) to query from.
            role: The representation of ``index`` to return.

        Returns:
            The found data, if any.

        """
        column = index.column()

        if role == self.artwork_role:
            return self._get_artwork(index)

        if role == QtCore.Qt.ToolTipRole:
            return self._get_artwork(index).get_tooltip()

        if column == _ARTWORK_COLUMN:
            if role == QtCore.Qt.DisplayRole:
                return self._get_artwork(index).get_title()

            return None

        # TODO: Add date column
        if column == _ARTIST_COLUMN:
            if role == QtCore.Qt.DisplayRole:
                return self._get_artwork(index).get_artist()

            return None

        return None

    # TODO: (performance) - Make this faster later (using fetchMore and caching)
    def rowCount(self, _: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # pylint: disable=invalid-name
        """Get the rows to show in the GUI.

        Args:
            parent: The immediate parent to get the children for.

        Returns:
            The number of rows to show.

        """
        return len(self._identifiers)

    def update_artwork_identifiers(self, identifiers: list[int]) -> None:
        """Clear and refresh this model with ``identifiers``.

        Important:
            This method reuses the existing Met Museum cache because, we assume, that an
            ID will only ever point to the same Work of Art for the lifetime of the GUI.
            (If it didn't, that would be pretty weird).

        Args:
            identifiers: Some Met Museum Artwork IDs (integers) to display.

        """
        self.beginResetModel()

        self._identifiers = identifiers

        self.endResetModel()
