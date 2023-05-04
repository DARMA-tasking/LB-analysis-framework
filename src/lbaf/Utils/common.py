"""Common utility functions"""
import os
import sys
import inspect
from typing import Optional

def is_editable():
    """Indicates if the current lbaf package is installed in editable mode"""
    editable = True
    for path_item in sys.path:
        egg_link = os.path.join(path_item, 'lbaf.egg-link')
        if os.path.isfile(egg_link):
            editable = False
    return editable

def project_dir() -> str:
    """Get the absolute path to the project root directory"""
    return os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../../../")

def current_module() -> Optional[inspect.types.ModuleType]:
    """Get the current module"""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    return module

def current_dir() -> str:
    """Get the absolute path to the directory containing the current executing module"""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    return os.path.dirname(module.__file__)

def abspath(path: str, relative_to: Optional[str] = None) -> Optional[str]:
    """Return an absolute path
    This function provides an additional option than os.path.abspath by enabling to express a relative path from
    another base path than the current working directory

    :param path: the input path
    :param relative_to: the base path, defaults to None (None = the current working directory)
    :return: an absolute path
    """
    if relative_to is None:
        # path is relative to the current working directory
        return os.path.abspath(path)
    elif not os.path.isabs(path):
        # path is a relative path
        if not os.path.isabs(relative_to):
            relative_to = os.path.abspath(relative_to)
        return os.path.abspath(os.path.join(relative_to, path))
    else:
        # path is already an absolute path
        return path
