"""Basic classes to make Qt + multi-threading easier."""

import logging
import typing

from PySide2 import QtCore

from ..._restapi import met_get
from ..models import art_model, model_type

_LOGGER = logging.getLogger(__name__)


class ArtQueryWorker(QtCore.QObject):
    """Handle any high latency / slow functions here.

    Attributes:
        identifiers_found:
            After we query the Met Museum for all Artworks, the found IDs are emitted.

    """

    identifiers_found = QtCore.Signal(list)

    def run(self) -> None:
        """Look for Met Museum IDs and update the parent thread when it is ready."""
        identifiers = met_get.get_all_identifiers()
        # IMPORTANT: Higher identifiers tend to have no thumbnails so we will prioritize
        # the later IDs. Both may get displayed in the end so this is just done to give
        # the user a meaningful GUI result sooner.
        #
        self.identifiers_found.emit(sorted(identifiers))


class QueryArtworkDetailsWorker(QtCore.QObject):
    """A Qt worker (meant to run in a QThread) that populates :class:`.Artwork` data.

    By default, :class:`.Artwork` classes contain basically no data and need to
    ask for its contents from The Met's REST API. This work populates those
    objects in another thread so the user is not impacted.

    Attributes:
        finished:
            A signal that emits when there is no more work left to do or the user
            (gracefully) interrupts this worker instance.

    """

    finished = QtCore.Signal()

    def __init__(
        self,
        indices: typing.Sequence[QtCore.QModelIndex],
        parent: QtCore.QObject | None = None,
    ) -> None:
        """Keep track of ``indices`` to process, later.

        Args:
            indices:
                Some Qt source locations that, we assume, is sparse / partially
                described. We will modify it!
            parent:
                An object which, if provided, holds a reference to this instance.

        """
        super().__init__(parent)

        self._running = False
        self._to_run = [QtCore.QPersistentModelIndex(index) for index in indices]

    def _populate(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Fill in the data for ``index``.

        Args:
            index:
                Some Qt source location that, we assume, is sparse / partially
                described. We will modify it!

        """
        artwork = typing.cast(
            model_type.Artwork, index.data(art_model.Model.artwork_role)
        )
        artwork.precompute_details()

    def run(self) -> None:
        """Populate all Artwork data in this instance (run Met REST API calls)."""
        self._running = True

        while self._running and self._to_run:
            current = self._to_run[-1]

            if not current.isValid():
                # NOTE: This should be rare but if a source row / index is
                # deleted, we could seg fault here. So we need to check first.
                #
                _LOGGER.warning("Skipped populating an invalid index.")

                continue

            self._populate(current)

            self._to_run.pop()

        if self._running:
            self.finished.emit()

    def stop(self) -> None:
        """Do not query any more data in this instance."""
        self._running = False
