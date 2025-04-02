"""Helper functions to make iterating over Qt objects easier.

These functions are meant to be as generic as possible.

"""

import collections
import typing

from Qt import QtCore


def get_lowest_source(model: QtCore.QAbstractItemModel) -> QtCore.QAbstractItemModel:
    """Find the lower-most source model, starting from ``model``.

    Args:
        model: The proxy to search within.

    Returns:
        The found source model.

    """
    while hasattr(model, "sourceModel"):
        model = model.sourceModel()

    return model


def iter_unique_rows(
    indices: typing.Iterable[QtCore.QModelIndex],
    predicate: typing.Optional[typing.Callable[[QtCore.QModelIndex], bool]] = None,
) -> list[QtCore.QModelIndex]:
    """Filter ``indices`` down to only each unique row.

    Important:
        This function does not preserve the order of ``indices``.

    Args:
        indices:
            The data to uniquify.
        predicate:
            A function that, if included, is called whenever more than one index with
            the same parent / row is found. By default if no predicate is found, this
            function prefers the 0th column for a particular parent + row index. But you
            can provide your own function to do custom things if you want. 99% of the
            time, leave this parameter untouched.

    Returns:
        The uniquified indices.

    """

    def _prefer_column_0(index: QtCore.QModelIndex) -> bool:
        """Iterate over just the child columns.

        In Qt, tree information is stored on the 0th column, which we target here.

        Args:
            index: The data to query from.

        Returns:
            If ``index`` is a location that may contain children, return ``True``.

        """
        return index.column() == 0

    if not predicate:
        predicate = _prefer_column_0

    rows = collections.OrderedDict()

    for index in indices:
        key = (index.parent(), index.row())

        if key not in rows or predicate(index):
            rows[key] = index

    return list(rows.values())
