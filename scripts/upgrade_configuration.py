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
default_pattern = ['./src/lbaf/Applications/**/*[.yml][.yaml]',
    './tests/data/config/**/*[.yml][.yaml]',
    './data/configuration_examples/**/*[.yml][.yaml]'
]
parser.add_argument('-a', '--add', type=str, default=None,
                    help='Key name (tree dot notation) to add')
parser.add_argument('-r', '--remove', type=str, default=None,
                    help='The key name (tree dot notation) to remove. e.g. `work_model.paramters.foo`. ' +
                    'Required for a remove operation.')
parser.add_argument('-v', '--value', type=str, default=None,
                    help='The initial value for a key to add.  e.g. `42`. Required for a add operation.')
parser.add_argument('-t', '--type', type=str, default='str',
                    help='Optional. The type of the initial value to set for a nnew key. Ex. `int`. Default `str`')
parser.add_argument('-p', '--pattern', nargs='+', type=str, default= [
    './src/lbaf/Applications/**/*[.yml][.yaml]',
    './tests/data/config/**/*[.yml][.yaml]',
    './data/configuration_examples/**/*[.yml][.yaml]'
], help='The list of patterns indicating which configuration files reside (path must be defined as relative to the ' +
    'project directory). Defaults `' + str.join(' ', default_pattern) + '`')
args = parser.parse_args()

if not args.add and not args.remove:
    raise ValueError('Missing either add (-a or --add xxx) or remove arg (-r or --remove xxx)')
if args.add and args.remove:
    raise ValueError('Cannot set both add and remove args')
if args.add and not args.value:
    raise ValueError('Missing value (-v or --vvv xxx)')


# pylint: disable=C0413
from src.lbaf.IO.configurationValidator import ConfigurationValidator
sections :dict = cast(dict, ConfigurationValidator.allowed_keys(group=True))
from src.lbaf.Utils.logger import logger
# pylint: enable=C0413

logger = logger('upgrade', level='debug')
logger.info('Script to bulk add or remove key to/from LBAF configuration files within the project')
logger.info(
    'NOTICE: Remember that the keys must be defined first at the schema level defined in ' \
    'the ConfigurationValidator class'
)

def upgrade(file_path: Path) -> int:
    """
    Apply an upgrade to the given configuration file
    """
    print('---')
    logger.debug('upgrading file %s ...', file_path)
    key_path = None
    if args.add:
        logger.debug('Add key `%s` with value `%s`', args.add, args.value)
        key_path = args.add.split('.')
    elif args.remove:
        print(f'Remove key `{args.remove}`')
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

    def write_node(k, value, yaml_file):
        """Wirtes a single node (key/value) in the given yaml file"""
        yaml_file.write(f'{k}:')
        if isinstance(value, list) or isinstance(value, dict):
            yaml_file.write('\n')
            yaml_file.write(indent_str)
            yaml_node = yaml.safe_dump(
                value,
                indent=indent_size,
                line_break='\n',
                sort_keys=False
            ).replace(
                '\n',
                '\n' + indent_str
            )
            if yaml_node.endswith('\n' + indent_str):
                yaml_node = yaml_node[:-(indent_size + 1)]
        else:
            yaml_node = ' ' + yaml.representer.SafeRepresenter().represent_data(value).value
        yaml_file.write(yaml_node)
        yaml_file.write('\n')

    with open(file_path, 'w', encoding='utf-8') as yaml_file:
        indent_size = 2
        indent_str = ' ' * indent_size
        added_keys = []
        for section in sections:
            if yaml_file.tell() > 0:
                yaml_file.write('\n')
            yaml_file.write(f'# Specify {section}\n')
            for k in sections[section]:
                if k in conf.keys():
                    value = conf[k]
                    write_node(k, value, yaml_file)
                    added_keys.append(k)
        # process possible other nodes not defined in a specific section
        intersect = [value for value in conf.keys() if not value in added_keys ]
        if len(intersect) > 0:
            keys_without_group = '`' + str.join('`, `', intersect) + '`'
            logger.warning(
                'The following keys are not in a group : %s\n' \
                'It will added by default to a group named `Other`.' \
                'To place this key in a specific group please update ConfigurationValidator.allowed_keys() at\n' \
                '%s/src/lbaf/IO/configurationValidator.py:182',
                keys_without_group,
                project_path
            )
            if yaml_file.tell() > 0:
                yaml_file.write('\n')
            yaml_file.write('# Other\n')
            for k in intersect:
                value = conf[k]
                write_node(k, value, yaml_file)
                added_keys.append(k)

        yaml_file.write('\n')

    logger.debug('File has been successfully upgraded')
    return 1

def run():
    """ Search all files matching pattern and upgrade each file"""
    for pattern in args.pattern:
        files = Path(project_path).glob(pattern)
        logger.debug('searching files with pattern %s', pattern)
        for file in files:
            upgrade(file)

run()
