"""Helper functions to make iterating over Qt objects easier.

These functions are meant to be as generic as possible.

"""

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
