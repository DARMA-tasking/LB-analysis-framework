import logging
import logging.config
from logging import Formatter
import os

import yaml

from src.Utils.colors import red, green, blue, cyan, magenta, yellow, white, black, light_red, light_green, \
    light_blue, light_cyan, light_magenta, light_yellow, light_white, light_black

LOGGING_LEVEL = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR}


class CustomFormatter(Formatter):
    def __init__(self, frmttr):
        super(CustomFormatter, self).__init__()
        self.frmttr = frmttr

    def format(self, record):
        log_fmt = self.frmttr.get(record.levelno)
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
    terminal_bg = conf.get('terminal_background', None)
    if terminal_bg == 'light':
        clr_fnc = black
    else:
        clr_fnc = light_white
    FORMATER_EXTENDED = {
        logging.DEBUG: yellow("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]"),
        logging.INFO: green("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]"),
        logging.WARNING: cyan("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]"),
        logging.ERROR: red("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]"),
    }

    FORMATER_PPP = {
        logging.DEBUG: yellow("[%(module)s] ") + clr_fnc("%(message)s"),
        logging.INFO: green("[%(module)s] ") + clr_fnc("%(message)s"),
        logging.WARNING: cyan("[%(module)s] ") + clr_fnc("%(message)s"),
        logging.ERROR: red("[%(module)s] ") + clr_fnc("%(message)s"),
    }

    lgr = logging.getLogger(name)
    lgr.setLevel(LOGGING_LEVEL.get(ll))
    if not lgr.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(LOGGING_LEVEL.get(ll))
        ch.setFormatter(CustomFormatter(frmttr=FORMATER_PPP))
        lgr.addHandler(ch)

    return lgr