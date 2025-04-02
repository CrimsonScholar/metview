"""A thin wrap around The Met Museum's (JSON-based) REST API."""

import os
import typing
from urllib import parse

import requests

_ARTIST_NAME_NOT_FOUND = "<No artist name>"
_TITLE_NOT_FOUND = "<No title>"

# Reference: https://datatracker.ietf.org/doc/html/rfc3986
_BASE = os.getenv("MET_MUSEUM_API_DOMAIN", "https://collectionapi.metmuseum.org")


class ObjectDetails(typing.NamedTuple):
    artist: str
    classification: str | None
    thumbnail_url: str | None
    title: str


class _ObjectDetailsResponse(typing.TypedDict):
    artistDisplayName: str
    classification: str | None
    primaryImageSmall: str | None
    title: str


class _ObjectsResponse(typing.TypedDict):
    limit: int
    objectIDs: list[int]


def get_all_identifiers() -> list[int]:
    url = parse.urljoin(_BASE, "public/collection/v1/objects")
    response = requests.get(url)

    if response.status_code != 200:
        raise ConnectionError(f'URL "{url}" is unreadable. Got "{response}" response.')

    data = typing.cast(_ObjectsResponse, response.json())

    return data["objectIDs"]


def get_identifier_data(identifier: str | int) -> ObjectDetails:
    url = parse.urljoin(_BASE, f"public/collection/v1/objects/{identifier}")
    response = requests.get(url)

    if response.status_code == 200:
        data = typing.cast(_ObjectDetailsResponse, response.json())

        return ObjectDetails(
            artist=data.get("artistDisplayName", _ARTIST_NAME_NOT_FOUND),
            classification=data.get("classification") or None,
            thumbnail_url=data["primaryImageSmall"] or None,
            title=data.get("title", _TITLE_NOT_FOUND),
        )

    raise ConnectionError(f'URL "{url}" is unreadable. Got "{response}" response.')


def get_artist() -> str:
    raise RuntimeError("STUn")


def get_thumbnail() -> str | None:
    raise RuntimeError("STUn")


def get_title() -> str:
    raise RuntimeError("STUn")
