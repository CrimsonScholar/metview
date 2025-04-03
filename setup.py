import os
import setuptools


_CURRENT_DIRECTORY = os.path.join(os.path.dirname(__file__))


def read(*names: list[str]) -> str:
    """Get the contents of all of the file `names`."""
    with open(os.path.join(_CURRENT_DIRECTORY, *names), "r", encoding="utf-8") as file_:
        return file_.read()


# TODO: Fill this out
setuptools.setup(
    author="Colin Kennedy",
    author_email="colinvfx@gmail.com",
    classifiers=[
        # Complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: No-License",
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
    name="metview",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
    version="1.0.0",
)
