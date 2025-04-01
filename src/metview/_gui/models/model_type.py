"""Internal data to define Qt + MVC types."""

import typing


class Artwork(typing.NamedTuple):
    """The main representation of some Artwork."""

    title: str
    artist: str
    thumbnail: str | None
