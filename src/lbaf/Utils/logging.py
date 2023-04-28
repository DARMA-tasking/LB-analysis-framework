"""logging util module """
import logging
import logging.config
import os
from logging import Formatter
from typing import Union, List, Dict
from .colors import red, green, cyan, yellow, black, light_white

LOGGING_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR
}

FORMATTER_BASIC = 'basic'
FORMATTER_EXTENDED = 'extended'
FORMATTERS = [ FORMATTER_BASIC, FORMATTER_EXTENDED ]

THEME_DARK = 'dark'
THEME_LIGHT = 'light'
THEMES = [ THEME_LIGHT, THEME_DARK ]

# type alias


Logger = logging.Logger
"""Logger class"""

class CustomFormatter(Formatter):
    """Custom formatter class defining a format by logging level """
    formatters: Dict[int,Formatter] = {}
    def __init__(self, frmttr):
        super(CustomFormatter, self).__init__()
        for level, fmt in frmttr.items():
            self.formatters[level] = Formatter(fmt)
    def format(self, record):
        return self.formatters[record.levelno].format(record)

def formatter(formatter_type: str, theme: Union[str, None] = None):
    """Creates a formatter of the given type"""
    if not formatter_type in FORMATTERS:
        frmtrs = str.join(', ', FORMATTERS)
        raise ValueError(f'Invalid formatter name. Supported are {frmtrs}')

    if theme is not None and not theme in THEMES:
        themes = str.join(', ', THEMES)
        raise ValueError(f'Invalid thee name. Supported are {themes}')

    def msgcolor(msg):
        if not theme is None:
            return black(msg) if theme == 'light' else light_white(msg)
        return msg

    # 'extended' formatter
    if formatter_type == 'extended':
        frmttr = {
            logging.DEBUG: yellow("%(levelname)s [%(module)s.%(funcName)s()] ") + msgcolor("msg:[%(message)s]"),
            logging.INFO: green("%(levelname)s [%(module)s.%(funcName)s()] ") + msgcolor("msg:[%(message)s]"),
            logging.WARNING: cyan("%(levelname)s [%(module)s.%(funcName)s()] ") + msgcolor("msg:[%(message)s]"),
            logging.ERROR: red("%(levelname)s [%(module)s.%(funcName)s()] ") + msgcolor("msg:[%(message)s]")
        }
    # 'basic' formatter
    else:
        frmttr = {
            logging.DEBUG: yellow("[%(module)s] ") + msgcolor("%(message)s"),
            logging.INFO: green("[%(module)s] ") + msgcolor("%(message)s"),
            logging.WARNING: cyan("[%(module)s] ") + msgcolor("%(message)s"),
            logging.ERROR: red("[%(module)s] ") + msgcolor("%(message)s")
        }
    return CustomFormatter(frmttr)

def get_logger(
        name: str = "root",
        level: Union[str, None] = "info",
        log_to_console: bool= True,
        log_to_file: Union[str, None] = None,
        formatter_name: str = FORMATTER_BASIC,
        theme: str = THEME_DARK
)-> Logger:
    """Return a new or an existing logger"""
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level.upper())
    if log_to_file is not None:
        logs_dir = f"{os.sep}".join(log_to_file.split(os.sep)[:-1])
        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)
    # initialize handlers only once
    if not logger.hasHandlers():
        handlers = [] #type: List[logging.Handler]
        if isinstance(log_to_file, str):
            handlers.append(logging.FileHandler(filename=log_to_file))
        if log_to_console:
            handlers.append(logging.StreamHandler())
        for handler in handlers:
            handler.setLevel(logger.level)
            handler.setFormatter(formatter(formatter_name, theme))
            logger.addHandler(handler)
    return logger
