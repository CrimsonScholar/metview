"""Internal exceptions to make CLI / terminal interactions simpler.

Try to define as few custom types as possible (prefer built-in Python types).

"""


class CoreException(Exception):
    """A common class that all :ref:`metview` exceptions should inherit from."""

    error_code = 0  # NOTE: Override this in subclasses if you wish


class UserInputError(CoreException):
    """When a user writes invalid input to the terminal / CLI."""

    error_code = 10
