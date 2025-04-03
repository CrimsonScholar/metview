"""Internal data to define Qt + MVC types."""

import functools
import textwrap
import typing

import requests

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

    def _has_thumbnail(self) -> bool:
        """Check if a thumbnail should exist without querying the thumbnail data."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return bool(self._details.thumbnail_url)

    def is_details_populated(self) -> bool:
        """Check if this instance has most of its label data yet."""
        return bool(self._details)

    def get_tooltip(self) -> str:
        """Show a simple breakdown of this instance."""
        return textwrap.dedent(
            f"""\
            Title: {self.get_title() or "<No title found>"}
            Artist: {self.get_artist() or "<No artist name found>"}
            Date: {self.get_datetime_range()!s}
            Classification: {self.get_classification() or "<No classification found>"}
            Has Thumbnail: {bool(self._has_thumbnail())}
            ID: {self._identifier!r}"""
        )

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
        """Get the type of artwork."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return self._details.classification

    def get_medium(self) -> str | None:
        """Get the material or method used to create the artwork."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return self._details.medium

    @functools.lru_cache()
    def get_thumbnail_data(self) -> bytes | None:
        """Search this instance for a small image so we can load it as a QPixmap later.

        Returns:
            The found thumbnail data, if any. If this instance has no image or
            it is not readable, ``None`` is returned.

        """
        # NOTE: The Met's database keeps thumbnail information separate from
        # the database because the images are large. So we separately cache it.
        #
        if thumbnail_url := self.get_thumbnail_url():
            return _read_thumbnail_data(thumbnail_url)

        return None

    def get_thumbnail_url(self) -> str | None:
        """Get the HTTP/S URL to a downloadable thumbnail, if any."""
        if not self._details:
            self.precompute_details()
            self._details = typing.cast(met_get.ObjectDetails, self._details)

        return self._details.thumbnail_url

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


def _read_thumbnail_data(url: str) -> bytes | None:
    """Search ``url`` for thumbnail data so we can load it as a QPixmap later.

    Args:
        url: Some https / http URL to request.

    Returns:
        The found thumbnail data, if any.
        If ``url`` is not readable, ``None`` is returned.

    """
    response = requests.get(url)

    if response.status_code != 200:
        raise ConnectionError(f'URL "{url}" is unreadable. Got "{response}" response.')

    return response.content
