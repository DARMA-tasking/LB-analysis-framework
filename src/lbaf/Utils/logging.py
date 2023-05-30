"""logging util module """
import logging
import logging.config
import os
from logging import Formatter
from typing import Union, List, Dict
from .colors import red, green, cyan, yellow


LOGGING_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR
}

FORMAT_BASIC = "basic"
FORMAT_EXTENDED = "extended"
FORMATS = [ FORMAT_BASIC, FORMAT_EXTENDED ]

# Logger type alias
Logger = logging.Logger
"""Logger class"""

class CustomFormatter(Formatter):
    """Custom color formatter class defining a color by logging level for log message prefix """

    LOGGING_LEVEL_COLORS = {
        logging.DEBUG: yellow,
        logging.INFO: green,
        logging.WARNING: cyan,
        logging.ERROR: red
    }

    _raw_formatter: None
    _color_formatters: Dict[int,Formatter] = {}
    _format:Union[FORMAT_BASIC, FORMAT_EXTENDED]
    _colored: bool = False

    def __init__(self, frmt: str, colored: bool = False):
        super(CustomFormatter, self).__init__()

        if not frmt in FORMATS:
            formats = str.join(', ', FORMATS)
            raise ValueError(f"Invalid format. Supported are {formats}")

        self._colored = colored
        self._format = frmt
        self._init_formatters()

    def _init_formatters(self):
        """Initialize inner formatters for each supported logging level"""

        # 'basic' default format
        formats = { "prefix": "[%(module)s] ", "message": "%(message)s" }
        # 'extended' format
        if self._format == "extended":
            formats = { "prefix": "%(levelname)s [%(module)s.%(funcName)s()] ", "message": "msg:[%(message)s]" }

        # create inner formatter for each log level
        if self._colored:
            for level, colorizer in self.LOGGING_LEVEL_COLORS.items():
                self._color_formatters[level] = Formatter(
                    colorizer(formats.get("prefix")) + formats.get("message")
                )
        # or create raw formatter to use at any level
        else:
            self._raw_formatter = Formatter(formats.get("prefix") + formats.get("message"))

    def format(self, record):
        formatter = None
        if self._colored:
            formatter = self._color_formatters[
                record.levelno
                    if record.levelno in self.LOGGING_LEVEL_COLORS
                    else logging.INFO
            ]
        else:
            formatter = self._raw_formatter
        return formatter.format(record)

l = {}

def get_logger(
        name: str = "root",
        level: Union[str, None] = "info",
        log_to_console: bool = True,
        log_to_file: Union[str, None] = None,
        frmt: str = FORMAT_BASIC
)-> Logger:
    """Return a new or an existing logger"""

    # return from cache if logger already created
    # logger = logging.Logger.manager.loggerDict.get(name)
    # if logger is not None:
    #     return logger
    if name in l:
        return l[name]

    print("Init logger " + name + "...")

    # init new logger
    logger = logging.getLogger(name)
    # index logger for future usage
    l[name] = logger

    logging.getLogger().handlers.clear() # clear default handlers
    if level is not None:
        logger.setLevel(level.upper())
    if log_to_file is not None:
        logs_dir = f"{os.sep}".join(log_to_file.split(os.sep)[:-1])
        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)
    # initialize handlers only once
    handlers = logger.handlers
    handlers = [] #type: List[logging.Handler]
    if isinstance(log_to_file, str):
        handlers.append(logging.FileHandler(filename=log_to_file))
    if log_to_console:
        handlers.append(logging.StreamHandler())
    for handler in handlers:
        handler.setLevel(logger.level)
        # use color formatter only if console
        handler.setFormatter(CustomFormatter(frmt, colored=isinstance(handler, logging.StreamHandler)))
        logger.addHandler(handler)

    return logger
