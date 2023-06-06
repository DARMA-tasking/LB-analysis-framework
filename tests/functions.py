"""Utility functions"""
import os
import subprocess
import sys


def run_lbaf(config_file) -> subprocess.CompletedProcess:
    """Run lbaf as a subprocess with the given configuration file (path)"""

    proc = subprocess.run(
        [
            'lbaf',
            '-c',
            config_file
        ],
        check=True,
        stdout=sys.stdout,
        stderr=sys.stdout
    )
    return proc
