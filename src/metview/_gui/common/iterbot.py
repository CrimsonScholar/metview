"""Helper functions to make iterating over Qt objects easier.

These functions are meant to be as generic as possible.

"""

import collections
import typing

from PySide6 import QtCore

T = typing.TypeVar("T")


def get_all_models_by_type(
    model: QtCore.QAbstractItemModel,
    type_: typing.Type[T],
) -> list[T]:
    """Find every Qt proxy / model starting from ``model`` of ``type_`` class type.

    Important:
        This method is **inclusive**, meaning ``model`` may be included in the return.

    Args:
        model: Some Qt proxy or source to begin searching within.
        type_: The Qt class to look within.

    Returns:
        All found matches, if any.

    """
    output: list[T] = []

    while hasattr(model, "sourceModel"):
        if isinstance(model, type_):
            output.append(model)
        model = model.sourceModel()

    if model and isinstance(model, type_):
        output.append(model)

    return output


def get_lowest_proxy(
    model: QtCore.QAbstractProxyModel,
) -> QtCore.QAbstractProxyModel:
    """Find the last contiguous proxy, starting from ``model``, which supports invalidation.

    Args:
        model: The model to search within.

    Raises:
        RuntimeError: If ``model`` cannot find a valid return proxy.

    Returns:
        The found proxy.

    """
    current = model
    found: QtCore.QAbstractProxyModel | None = None

    while True:
        if hasattr(current, "invalidate"):
            found = current

        if hasattr(current, "sourceModel"):
            current = typing.cast(QtCore.QAbstractProxyModel, current.sourceModel())
        else:
            break

    if not found:
        raise RuntimeError(
            'Model "{model}" has no inner filter proxies.'.format(model=model)
        )

    return found


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


def map_to_source_recursively(
    index: QtCore.QModelIndex,
    source_model: QtCore.QAbstractItemModel,
) -> QtCore.QModelIndex:
    """Convert ``index`` from whatever model it is to an index in ``source_model``.

    Args:
        index:
            The row / column / parent index to convert into a source index.
        source_model:
            The model to map into.

    Raises:
        RuntimeError: If no source index / model could be found.

    Returns:
        The found source index, using ``index``.

    """
    model = index.model()
    original = model

    current_index = index

    while (
        model != source_model
        and hasattr(model, "sourceModel")
        and hasattr(model, "mapToSource")
    ):
        current_index = model.mapToSource(current_index)

        model = model.sourceModel()

    if model != source_model:
        raise RuntimeError(
            'Model "{original}" could not be mapped to our source model, "{source_model}".'.format(
                original=original, source_model=source_model
            )
        )

    return current_index
