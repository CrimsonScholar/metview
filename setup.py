"""The main packaging file."""

import os
import setuptools
import sys


_NAME = "metview"
_CURRENT_DIRECTORY = os.path.join(os.path.dirname(__file__))
_VERSION = "1.0.0"

_EXTRA_OPTIONS: dict[str, str] = {}


if sys.platform == "darwin":
    _PY2APP_OPTIONS = dict(
        packages=["PySide6", "requests"],
        plist=dict(
            CFBundleDevelopmentRegion="en_US",
            CFBundleExecutable=_NAME,
            CFBundleDisplayName=_NAME,
            CFBundleName=_NAME,
            CFBundleVersion=_VERSION,
            CFBundleShortVersionString=_VERSION,
        ),
    )
    _EXTRA_OPTIONS = dict(
        app=[os.path.join(_CURRENT_DIRECTORY, "src", "metview_application.py")],
        options={"py2app": _PY2APP_OPTIONS},
        setup_requires=["py2app"],
    )


def read(*names: list[str]) -> str:
    """Get the contents of all of the file `names`."""
    with open(os.path.join(_CURRENT_DIRECTORY, *names), "r", encoding="utf-8") as file_:
        return file_.read()


setuptools.setup(
    author="Colin Kennedy",
    author_email="colinvfx@gmail.com",
    classifiers=[
        # Complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Operating System :: Unix",
        "Operating System :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
    ],
    install_requires=[read("requirements.txt").splitlines()],
    keywords=["art", "artwork", "qt", "pyside", "search"],
    name=_NAME,
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
    version=_VERSION,
    **_EXTRA_OPTIONS,
)
