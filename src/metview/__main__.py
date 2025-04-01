"""The main implementation for ``python -m metview``.

Example:
    python -m metview show-gui

"""

import logging
import sys

from ._cli import cli, exception_type


_ROOT_LOGGER_NAME = "metview"


def _initialize_logging() -> None:
    """Add the logging print handlers."""
    _LOGGER = logging.getLogger(_ROOT_LOGGER_NAME)
    _HANDLER = logging.StreamHandler(sys.stdout)
    _HANDLER.setLevel(logging.INFO)
    _FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    _HANDLER.setFormatter(_FORMATTER)
    _LOGGER.addHandler(_HANDLER)
    _LOGGER.setLevel(logging.INFO)


_initialize_logging()

try:
    cli.main(sys.argv[1:])
except exception_type.CoreException as error:
    print("Error: {error}", file=sys.stderr)

    sys.exit(error.error_code)
