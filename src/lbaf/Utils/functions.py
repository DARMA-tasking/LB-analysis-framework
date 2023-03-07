"""Utility functions"""
import os
from typing import Union

def abspath_from(path: Union[str, None], relative_to_dir: str) -> Union[str, None]:
    """Get the absolute path from the given path relative to specific directory.
    If path is None then None is returned
    If path is already absolute it irs returned as it is.
    If path is relative then set relative_to to indicate the reference directory (absolute path)
    """
    if path is None:
        return None
    elif not os.path.isabs(path):
        if not os.path.isabs(relative_to_dir):
            raise ValueError('relative_to_dir must be an absolute path')
        return os.path.abspath(relative_to_dir + '/' + path)
    else:
        return path
