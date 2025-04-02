"""Any simple Python type to re-use in other modules."""

import functools


@functools.total_ordering
class Datetime:
    """Some really simple datetime proxy object.

    Python's standard ``datetime.datetime`` does not support B.C. years which is a
    problem because The Met has many Works of Art before A.D. So we use this class to
    get around it.

    """

    def __init__(self, year: int) -> None:
        """Keep track of ``year`` for later.

        Args:
            year: The B.C. / A.D. year to keep track of. e.g. ``2025`` or ``-100``.

        """
        super().__init__()

        self._year = year

    def __eq__(self, other: object) -> bool:
        """Check if this instance and ``other`` are equivalent.

        Args:
            other: Some other Datetime to check.

        Returns:
            If ``other`` is the same datetime, return ``True``.

        """
        if not isinstance(other, Datetime):
            return False

        return self._year == other._year

    def __lt__(self, other: object) -> bool:
        """Check if this instance comes before ``other`` in a sorting function.

        Args:
            other: Some other Datetime to check.

        Returns:
            If this instance must come before ``other``, return ``True``.

        """
        if not isinstance(other, Datetime):
            return False

        return self._year < other._year

    def __repr__(self) -> str:
        """Show how to create this instance."""
        return f"{self.__class__.__name__}({self._year!r})"

    def __str__(self) -> str:
        """Get the raw date of this instance."""
        return str(self._year)


DatetimeRange = tuple[Datetime | None, Datetime | None]
