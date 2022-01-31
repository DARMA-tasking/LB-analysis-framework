import logging
import logging.config
from logging import Formatter
import os

import yaml

from src.Utils.colors import red, green, blue, cyan, magenta, yellow, white, black, light_red, light_green, \
    light_blue, light_cyan, light_magenta, light_yellow, light_white, light_black

LOGGING_LEVEL = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR}

FORMATER_EXTENDED = {
        logging.DEBUG: yellow("%(levelname)s [%(module)s.%(funcName)s()] ") + light_white("msg:[%(message)s]"),
        logging.INFO: green("%(levelname)s [%(module)s.%(funcName)s()] ") + light_white("msg:[%(message)s]"),
        logging.WARNING: cyan("%(levelname)s [%(module)s.%(funcName)s()] ") + light_white("msg:[%(message)s]"),
        logging.ERROR: red("%(levelname)s [%(module)s.%(funcName)s()] ") + light_white("msg:[%(message)s]"),
    }

FORMATER_PPP = {
        logging.DEBUG: yellow("[%(module)s] ") + light_white("%(message)s"),
        logging.INFO: green("[%(module)s] ") + light_white("%(message)s"),
        logging.WARNING: cyan("[%(module)s] ") + light_white("%(message)s"),
        logging.ERROR: red("[%(module)s] ") + light_white("%(message)s"),
    }


class CustomFormatter(Formatter):
    def format(self, record):
        log_fmt = FORMATER_PPP.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def logger(name: str = 'root'):
    """ Returns logger with config from logger.ini
    """
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    with open(os.path.join(project_path, "src", "Applications", "conf.yaml"), 'rt') as conf_file:
        conf = yaml.safe_load(conf_file)
    loggin_level = conf.get('logging_level', None)
    if loggin_level is not None:
        ll = loggin_level.upper()
    else:
        raise KeyError('No logging_level key in config file!')

    lgr = logging.getLogger(name)
    lgr.setLevel(LOGGING_LEVEL.get(ll))
    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL.get(ll))
    ch.setFormatter(CustomFormatter())
    lgr.addHandler(ch)
    return lgr
