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
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)


_initialize_logging()

try:
    cli.main(sys.argv[1:])
except exception_type.CoreException as error:
    print("Error: {error}", file=sys.stderr)

    sys.exit(error.error_code)
