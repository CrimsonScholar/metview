"""Internal data to define Qt + MVC types."""

import datetime
import functools
import textwrap
import typing

from ..._restapi import met_get, met_get_type


class Artwork:
    """The main representation of some Artwork."""

    def __init__(self, identifier: int) -> None:
        """Keep track of ``identifier`` so we can query with it later.

        Args:
            identifier: Some Met Museum artwork identifier number.

        """
        super().__init__()

        self._identifier = identifier
        self._details: met_get.ObjectDetails | None = None

    def get_tooltip(self) -> str:
        """Show a simple breakdown of this instance."""
        return textwrap.dedent(
            f"""\
            Title: {self.get_title() or "<No title found>"}
            Artist: {self.get_artist() or "<No artist name found>"}
            Classification: {self.get_classification() or "<No classification found>"}
            Has Thumbnail: {bool(self.get_thumbnail_data())}"""
        )

    # TODO: Consider refactoring this ``if precompute ... return foo`` pattern
    def get_artist(self) -> str:
        """Get the artwork name / title."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return self._details.artist

    def get_datetime_range(self) -> met_get_type.DatetimeRange:
        """Get type / method used to create the artwork."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return self._details.datetime_range

    def get_classification(self) -> str | None:
        """Get type / method used to create the artwork."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return self._details.classification

    @functools.lru_cache()
    def get_thumbnail_data(self) -> str | None:
        """Search this instance for a small image so we can load it as a QPixmap later.

        Returns:
            The found thumbnail data, if any. If this instance has no image or
            it is not readable, ``None`` is returned.

        """
        # NOTE: The Met's database keeps thumbnail information separate from
        # the database because the images are large. So we separately cache it.
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        if not self._details.thumbnail_url:
            return None

        return _read_thumbnail_data(self._details.thumbnail_url)

    def get_title(self) -> str:
        """Get the artwork name / title."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return self._details.title

    def precompute_details(self) -> None:
        """Get the main data for this instance.

        Basically this instance is sparse by default and calling this method helps "fill
        out" the data.

        """
        self._details = met_get.get_identifier_data(self._identifier)

    def __eq__(self, other: typing.Any) -> bool:
        """Check if ``other`` is the same as this instance.

        Args:
            other: Another Artwork to check.

        Returns:
            If ``other`` is not Artwork or is a different work of art, return ``False``.

        """
        if not isinstance(other, Artwork):
            return False

        return self._identifier == other._identifier

    def __hash__(self) -> int:
        """Serialize this to an immutable type (so we cause it in hash contexts)."""
        return hash((self.__class__.__name__, self._identifier))

    def __repr__(self) -> str:
        """Show how to reproduce this Python object."""
        return f"{self.__class__.__name__}(identifier={self._identifier!r})"


def _read_thumbnail_data(url: str) -> str | None:
    """Search ``url`` for thumbnail data so we can load it as a QPixmap later.

    Args:
        url: Some https / http URL to request.

    Returns:
        The found thumbnail data, if any.
        If ``url`` is not readable, ``None`` is returned.

    """
    # TODO: Finish this later
    raise NotImplementedError("TODO: Finish this later")
