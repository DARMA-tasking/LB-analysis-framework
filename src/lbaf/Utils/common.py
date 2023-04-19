"""Common utility functions"""
import os
import inspect
import sys
from typing import Optional


def append_to_path(path:str) -> str:
    """Add lbaf directory to python path"""
    try:
        sys.path.append(path)
    except Exception as path_ex:
        print(f"Can not add project path to system path. Exiting.\nERROR: {path_ex}")
        raise SystemExit(1) from path_ex

def project_dir() -> str:
    """Get the absolute path to the project root directory"""
    return os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../../../")

def src_dir() -> str:
    """Get the absolute path to the src directory"""
    return os.path.abspath(os.path.join(project_dir(), "src"))

def lbaf_dir() -> str:
    """Get the absolute path to the src/lbaf directory"""
    return os.path.abspath(os.path.join(project_dir(), "src", "lbaf"))

def current_module() -> Optional[inspect.types.ModuleType]:
    """Get the current module"""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    return module

def current_dir() -> str:
    """Get the absolute path to the directory containing the current module"""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    return os.path.dirname(module.__file__)

def abspath_from(path: Optional[str], base_dir: Optional[str]) -> Optional[str]:
    """Get the absolute path from the given path relative to some base directory.
    If path is None or is already an absolute path it is just returned
    If path is relative then base_dir must indicate the base directory from which to resolve the path
    """
    if path is None:
        return None
    elif not os.path.isabs(path):
        if base_dir is None or not os.path.isabs(base_dir):
            raise ValueError("base_dir must be an absolute path")
        return os.path.abspath(os.path.join(base_dir, path))
    else:
        return path
