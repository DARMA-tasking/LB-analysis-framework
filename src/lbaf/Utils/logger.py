import logging
import logging.config
from logging import Formatter
import os
import yaml

from .colors import red, green, blue, cyan, magenta, yellow, white, black, light_red, light_green, light_blue, light_cyan, light_magenta, light_yellow, light_white, light_black

LOGGING_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR}


class CustomFormatter(Formatter):
    def __init__(self, frmttr):
        super(CustomFormatter, self).__init__()
        self.frmttr = frmttr

    def format(self, record):
        log_fmt = self.frmttr.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def logger(name: str = "root", conf: str = None):
    """ Return logger with config from logger.ini
    """
    if conf is not None:
        with open(conf, "rt") as conf_file:
            config = yaml.safe_load(conf_file)
    else:
        config = {}

    # Assign formatting properties
    clr_fnc = black if config.get("terminal_background") == "light" else light_white
    logger_output = config.get("log_to_file") if \
        bool(isinstance(config.get("log_to_file"), str) and config.get("log_to_file") is not None) else None
    formater_extended = {
        logging.DEBUG: yellow("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]"),
        logging.INFO: green("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]"),
        logging.WARNING: cyan("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]"),
        logging.ERROR: red("%(levelname)s [%(module)s.%(funcName)s()] ") + clr_fnc("msg:[%(message)s]")}
    formater_PPP = {
        logging.DEBUG: yellow("[%(module)s] ") + clr_fnc("%(message)s"),
        logging.INFO: green("[%(module)s] ") + clr_fnc("%(message)s"),
        logging.WARNING: cyan("[%(module)s] ") + clr_fnc("%(message)s"),
        logging.ERROR: red("[%(module)s] ") + clr_fnc("%(message)s")}

    # Set logger properties in INFO mode by default
    lgr = logging.getLogger(name)
    ll = config.get("logging_level", "INFO").upper()
    lgr.setLevel(LOGGING_LEVEL.get(ll))
    if not lgr.hasHandlers():
        if logger_output is not None:
            ch = logging.FileHandler(filename=logger_output)
        else:
            ch = logging.StreamHandler()
        ch.setLevel(LOGGING_LEVEL.get(ll))
        ch.setFormatter(CustomFormatter(frmttr=formater_PPP))
        lgr.addHandler(ch)

    # Return logger
    return lgr
