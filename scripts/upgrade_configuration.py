"""
A script to bulk upgrade LBAF configuration files
"""

import os
from pathlib import Path
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--add", type=str)
parser.add_argument("-r", "--remove", type=str)
args = parser.parse_args()

if not args.add and not args.remove:
    raise Exception('Missing either add (-a or --add xxx) or remove arg (-r or --remove xxx)')

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.absolute()

def upgrade(file_path: Path) -> None:
    """
    Apply an upgrade to the given configuration file
    """
    print(f'reading file file at {file_path} (TODO)')
    if args.add:
        print(f'Add key named (dot path name) {args.add} (TODO)')
    if args.remove:
        print(f'Remove key named (dot path name) {args.remove} (TODO)')

# define path patterns for configuration files
patterns = [
   './src/lbaf/Applications/**/*[.yml][.yaml]',
   './tests/data/config/**/*[.yml][.yaml]'
]

# browse files matching configuration file path pattern
for pattern in patterns:
    files = Path(BASE_DIR).glob(pattern)
    print('searching ' + pattern)
    for file in files:
        upgrade(file)
