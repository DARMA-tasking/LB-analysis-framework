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

    _formatters: Dict[int,Formatter] = {}
    _format:Union[FORMAT_BASIC, FORMAT_EXTENDED]

    def __init__(self, frmt: str):
        super(CustomFormatter, self).__init__()

        if not frmt in FORMATS:
            formats = str.join(', ', FORMATS)
            raise ValueError(f"Invalid format. Supported are {formats}")

        self._format = frmt
        self._init_formatters()

    def _init_formatters(self):
        """Initialize inner formatters for each supported logging level"""

        # 'basic' default format
        formats = { "prefix": "[%(module)s] ", "message": "%(message)s" }
        # 'extended' format
        if self._format == "extended":
            formats = { "prefix": "%(levelname)s [%(module)s.%(funcName)s()] ", "message": "msg:[%(message)s]" }

        frmttr = {}
        # create inner formatter for each log level
        for level, colorizer in self.LOGGING_LEVEL_COLORS.items():
            frmttr[level] = colorizer(formats.get("prefix")) + formats.get("message")

        for level, fmt in frmttr.items():
            self._formatters[level] = Formatter(fmt)

    def format(self, record):
        formatter = self._formatters[record.levelno if record.levelno in self.LOGGING_LEVEL_COLORS else logging.INFO]
        return formatter.format(record)

def get_logger(
        name: str = "root",
        level: Union[str, None] = "info",
        log_to_console: bool = True,
        log_to_file: Union[str, None] = None,
        frmt: str = FORMAT_BASIC
)-> Logger:
    """Return a new or an existing logger"""

    # return from cache if logger already created
    logger = logging.Logger.manager.loggerDict.get(name)
    if logger is not None:
        return logger

    # init new logger
    logger = logging.getLogger(name)
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
        handler.setFormatter(CustomFormatter(frmt))
        logger.addHandler(handler)

    return logger
