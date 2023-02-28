"""
A script to bulk upgrade LBAF configuration files
"""

import argparse
import os
import sys
from pathlib import Path
from pydoc import locate
from typing import cast
import yaml

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as ex:
    print(f"Can not add project path to system path! Exiting!\nERROR: {ex}")
    raise SystemExit(1) from ex

# get and validate input args
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--add', type=str, default=None)
parser.add_argument('-r', '--remove', type=str, default=None)
parser.add_argument('-v', '--value', type=str, default=None)
parser.add_argument('-t', '--type', type=str, default='str')
parser.add_argument('-p', '--pattern', nargs='+', type=str, default= [
    './src/lbaf/Applications/**/*[.yml][.yaml]',
    './tests/data/config/**/*[.yml][.yaml]',
    './data/configuration_examples/**/*[.yml][.yaml]'
])
args = parser.parse_args()
if not args.add and not args.remove:
    raise ValueError('Missing either add (-a or --add xxx) or remove arg (-r or --remove xxx)')
if args.add and not args.value:
    raise ValueError('Missing value (-v or --vvv xxx)')


# pylint: disable=C0413
from src.lbaf.IO.configurationValidator import ConfigurationValidator
sections :dict = cast(dict, ConfigurationValidator.allowed_keys(group_by_section=True))

def upgrade(file_path: Path) -> int:
    """
    Apply an upgrade to the given configuration file
    """
    print(f'reading file file at {file_path} (TODO)')
    key_path = None
    if args.add:
        print(f'Add key named (dot path name) {args.add} with value {args.value}')
        key_path = args.add.split('.')
    elif args.remove:
        print(f'Remove key named (dot path name) {args.remove} (TODO)')
        key_path = args.remove.split('.')

    parsed_value = args.value
    if args.type is not None:
        type_v = locate(args.type)
        if callable(type_v):
            parsed_value = type_v(args.value)

    if key_path is None:
        raise ValueError('The `key` must be a valid string')

    conf = None
    with open(file_path, 'r', encoding='utf-8') as yaml_file:
        yaml_content = yaml_file.read()
        conf =  yaml.safe_load(yaml_content)
        node = conf
        for i, key in enumerate(key_path):
            is_leaf = i == len(key_path)-1
            # if node does not exist create it
            if not key in node.keys():
                if args.add:
                    if is_leaf:
                        node[key] = parsed_value
                    else:
                        new_branch = {}
                        new_node = new_branch
                        new_key_path = key_path[i+1:]
                        for j, new_key in enumerate(new_key_path):
                            is_leaf = j == len(new_key_path) - 1
                            new_node[new_key] = parsed_value if is_leaf else {}
                            new_node = new_node[new_key]
                        node[key] = new_branch
            elif is_leaf:
                if args.remove:
                    del node[key]
                else:
                    node[key] = parsed_value
            # go next node in child tree
            if is_leaf:
                break
            else:
                node=node[key]

    with open(file_path, 'w', encoding='utf-8') as yaml_file:
        indent_size = 2
        indent_str = ' ' * indent_size
        current_section = None
        for k, v in conf.items():
            # determine config section
            for section in sections:
                for key in sections[section]:
                    if k == key and current_section != section:
                        current_section = section
                        if yaml_file.tell() > 0:
                            yaml_file.write('\n')
                        yaml_file.write(f'# Specify {current_section}\n')

            yaml_file.write(f'{k}:')
            if isinstance(v, list) or isinstance(v, dict):
                yaml_file.write('\n')
                yaml_node = '  ' + yaml.dump(v, indent=indent_size, line_break='\n').replace('\n', '\n' + indent_str)
                if yaml_node.endswith('\n' + indent_str):
                    yaml_node = yaml_node[:-(indent_size + 1)]
                yaml_file.write(yaml_node)
            else:
                yaml_file.write(f' {v}')

            #if i < len(conf.items()) - 1:
            yaml_file.write('\n')

    return 1

# browse files matching configuration file path pattern
for pattern in args.pattern:
    files = Path(project_path).glob(pattern)
    print(f'searching files with pattern {pattern}')
    for file in files:
        upgrade(file)
