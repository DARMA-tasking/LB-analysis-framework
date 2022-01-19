import os

import yaml


def set_logging_level(project_path: str):
    """ Setting loging level from conf.yml to logger.ini """
    with open(os.path.join(project_path, "src", "Applications", "conf.yaml"), 'rt') as conf_file:
        conf = yaml.safe_load(conf_file)
    loggin_level = conf.get('logging_level', None)
    if loggin_level is not None:
        ll = loggin_level.upper()
    else:
        raise KeyError('No logging_level key in config file!')

    beg = '[handler_consoleHandler]\nlevel='
    end = '\nclass=StreamHandler'
    with open(os.path.join(project_path, "src", "Utils", "logger.ini"), 'rt') as log_file:
        log_file_str = log_file.read()
    beg_idx = log_file_str.find(beg) + len(beg)
    end_idx = log_file_str.find(end)
    new_log_file_str = f'{log_file_str[:beg_idx]}{ll}{log_file_str[end_idx:]}'
    with open(os.path.join(project_path, "src", "Utils", "logger.ini"), 'wt') as new_log_file:
        new_log_file.write(new_log_file_str)
