"""This module contains path utility methods."""
import os
from typing import Optional


def abspath(path: str, relative_to: Optional[str] = None) -> Optional[str]:
    """Return an absolute path.

    This function provides an additional option than os.path.abspath by enabling to express a relative path from
    another base path than the current working directory.

    :param path: the input path. Can be absolute or relative.
    :param relative_to: the base path, defaults to None (None = the current working directory)
    :returns: an absolute path
    """
    if relative_to is None:
        # Path is relative to the current working directory
        return os.path.abspath(path)
    if not os.path.isabs(path):
        # Path is a relative path
        if not os.path.isabs(relative_to):
            relative_to = os.path.abspath(relative_to)
        return os.path.abspath(os.path.join(relative_to, path))
    else:
        # Path is already an absolute path
        return path
