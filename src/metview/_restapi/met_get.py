"""A thin wrap around The Met Museum's (JSON-based) REST API."""

import datetime
import logging
import os
import typing
from urllib import parse

import requests

from . import met_get_type


_ARTIST_NAME_NOT_FOUND = "<No artist name>"
_TITLE_NOT_FOUND = "<No title>"
# Reference: https://datatracker.ietf.org/doc/html/rfc3986
_BASE = os.getenv("MET_MUSEUM_API_DOMAIN", "https://collectionapi.metmuseum.org")

_LOGGER = logging.getLogger(__name__)


class ObjectDetails(typing.NamedTuple):
    """The formatted Met Museum data.

    Attributes:
        artist: The name, group, or entity that created the Artwork.
        classification: The type of art, if any. e.g. ``"Print"``, ``"Etching"``, etc.
        thumbnail_url: The https / http URL to the artwork, if any.
        title: The name of the art. If no art, a default "no title found" is given.

    """

    artist: str
    classification: str | None
    datetime_range: met_get_type.DatetimeRange
    thumbnail_url: str | None
    title: str


class _ObjectDetailsResponse(typing.TypedDict):
    """The raw Met Museum response to a ``../v1/objects/{objectID}`` API call."""

    artistDisplayName: str
    classification: str | None
    objectBeginDate: int
    objectEndDate: int
    primaryImageSmall: str | None
    title: str


class _ObjectsResponse(typing.TypedDict):
    """The raw Met Museum response to a ``public/collection/v1/objects`` API call."""

    limit: int
    objectIDs: list[int]


def _get_datetime(year: int | None) -> datetime.datetime | None:
    """Convert ``year`` to a datetime object.

    Args:
        year: Some B.C / A.D. year, if any. e.g. ``2025``.

    Returns:
        The converted datetime, if any.

    """
    if not year:
        return None

    month = 1
    day = 1

    try:
        # NOTE: The Met Museum only tracks year so we just fill in
        # a placeholder for the month and day.
        #
        return datetime.datetime(year, month, day)
    except (ValueError, TypeError):
        _LOGGER.error('Value "%s" could not be converted into a datetime.', year)

        return None


def get_all_identifiers() -> list[int]:
    """Find all Met Museum Artwork IDs."""
    url = parse.urljoin(_BASE, "public/collection/v1/objects")
    response = requests.get(url)

    if response.status_code != 200:
        raise ConnectionError(f'URL "{url}" is unreadable. Got "{response}" response.')

    data = typing.cast(_ObjectsResponse, response.json())

    return data["objectIDs"]


def get_identifier_data(identifier: str | int) -> ObjectDetails:
    """Read all data from Artwork ``identifier``.

    Args:
        identifier: Some Met Museum Artwork ID to check.

    Raises:
        ConnectionError: If no data could be found for ``identifier``.

    Returns:
        All found data.

    """
    url = parse.urljoin(_BASE, f"public/collection/v1/objects/{identifier}")
    response = requests.get(url)

    if response.status_code != 200:
        raise ConnectionError(f'URL "{url}" is unreadable. Got "{response}" response.')

    data = typing.cast(_ObjectDetailsResponse, response.json())

    return ObjectDetails(
        artist=data.get("artistDisplayName", _ARTIST_NAME_NOT_FOUND),
        classification=data.get("classification") or None,
        datetime_range=(
            _get_datetime(data.get("objectBeginDate")),
            _get_datetime(data.get("objectEndDate")),
        ),
        thumbnail_url=data["primaryImageSmall"] or None,
        title=data.get("title", _TITLE_NOT_FOUND),
    )
