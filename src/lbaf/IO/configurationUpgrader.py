"""A script to bulk upgrade LBAF configuration files"""
import os
from enum import Enum
from pathlib import Path
from pydoc import locate
from typing import cast, Any, IO, List
from logging import Logger
import yaml
from .configurationValidator import ConfigurationValidator

project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])


# Uncomment to format numbers with scientific notation without using Pythong automatic rule
# and also `import re`
# Python formats in scientific notation if value < 1e-4 or value > 1e6
# #
# def float_representer(dumper, value):
#     if value != 0.0 and (value < 1e-4 or value > 1e6):
#         text = "{:e}".format(value)
#     else:
#         text = str(value)
#     return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)
# yaml.add_representer(float, float_representer)

class UpgradeAction(Enum):
    """Upgrade action"""
    ADD_KEY = 'add'
    REMOVE_KEY = 'remove'

class ConfigurationDumper(yaml.Dumper):
    """Custom dumper to add indent before list items hyphens"""
    def increase_indent(self, flow=False, indentless=False):
        return super(ConfigurationDumper, self).increase_indent(flow, False)

class ConfigurationUpgrader:
    """This class enables to bulk upgrade configuration files by adding or removing keys"""
    __dumper: ConfigurationDumper
    __logger: Logger
    __sections: dict

    def __init__(self, logger: Logger):
        self.__dumper = ConfigurationDumper
        self.__logger = logger
        self.__sections = cast(dict, ConfigurationValidator.allowed_keys(group=True))

    def write_node(self, k: str, value: Any, yaml_file: IO, indent_size: int = 2):
        """Write a single node (key/value) in the given yaml file"""
        indent_str = ' ' * indent_size
        yaml_file.write(f'{k}:')
        if isinstance(value, list) or isinstance(value, dict):
            yaml_file.write('\n')
            yaml_file.write(indent_str)
            yaml_node = yaml.dump(
                value,
                indent=indent_size,
                line_break='\n',
                sort_keys=False,
                Dumper=self.__dumper
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

    def upgrade(
        self,
        file_path: Path,
        action: UpgradeAction,
        key: str,
        value: str = None,
        value_type: str = 'str'
    ) -> None:
        """Apply an upgrade to the given configuration file"""
        self.__logger.debug('Upgrading file %s ...', file_path)
        key_path = None
        if action == UpgradeAction.ADD_KEY:
            self.__logger.debug('Add key `%s` with value `%s`', key, value)
        elif action == UpgradeAction.REMOVE_KEY:
            print(f'Remove key `{key}`')
        key_path = key.split('.')
        parsed_value = value
        if value_type is not None:
            type_v = locate(value_type)
            if callable(type_v):
                parsed_value = type_v(value)

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
                    if action == UpgradeAction.ADD_KEY:
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
                    if action == UpgradeAction.REMOVE_KEY:
                        del node[key]
                    else:
                        node[key] = parsed_value
                # go next node in child tree
                if is_leaf:
                    break
                else:
                    node=node[key]

        with open(file_path, 'w', encoding='utf-8') as yaml_file:
            added_keys = []
            for section in self.__sections:
                if yaml_file.tell() > 0:
                    yaml_file.write('\n')
                yaml_file.write(f'# Specify {section}\n')
                for k in self.__sections[section]:
                    if k in conf.keys():
                        value = conf[k]
                        self.write_node(k, value, yaml_file)
                        added_keys.append(k)
            # process possible other nodes not defined in a specific section
            intersect = [value for value in conf.keys() if not value in added_keys ]
            if len(intersect) > 0:
                keys_without_group = '`' + str.join('`, `', intersect) + '`'
                self.__logger.warning(
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
                    self.write_node(k, value, yaml_file)
                    added_keys.append(k)

        self.__logger.debug('File has been successfully upgraded')
        return 1

    def upgrade_all(
        self,
        pattern: List[str],
        relative_to: str,
        action: UpgradeAction,
        key: str,
        value: str = None,
        value_type: str = 'str'
    ) -> None:
        """Search all files matching some pattern and upgrade each file as needed"""
        for pat in pattern:
            files = Path(relative_to).glob(pat)
            self.__logger.debug('searching files with pattern %s in %s', pat, project_path)
            for file in files:
                self.upgrade(file, action, key, value, value_type)